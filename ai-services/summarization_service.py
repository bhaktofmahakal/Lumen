"""
Document Summarization and Data Extraction Service
Implements document summarization, comparative analysis, and data extraction
Requirements: 5.1, 5.2, 5.3, 5.7, 6.1, 6.2, 6.3, 6.5, 6.7, 14.1, 14.2, 14.8
"""

import logging
import time
from typing import List, Dict, Optional, Any, Literal
from enum import Enum
from pydantic import BaseModel
import asyncio

from llm_router import LLMRouter
from vector_store import QdrantVectorStore
from embeddings import EmbeddingGenerator

logger = logging.getLogger(__name__)


class SummaryLength(str, Enum):
    """Summary length options"""
    BRIEF = "brief"  # 1-2 paragraphs
    STANDARD = "standard"  # 3-5 paragraphs
    DETAILED = "detailed"  # 1-2 pages


class DocumentSection(BaseModel):
    """Document section model"""
    section_name: str
    content: str
    page_numbers: Optional[List[int]] = []


class DocumentSummary(BaseModel):
    """Document summary model"""
    document_id: str
    document_title: str
    summary_length: SummaryLength
    abstract: Optional[str] = None
    introduction: Optional[str] = None
    methods: Optional[str] = None
    results: Optional[str] = None
    conclusion: Optional[str] = None
    key_findings: List[str] = []
    generated_at: str


class ComparativeSummary(BaseModel):
    """Comparative summary model"""
    document_ids: List[str]
    similarities: List[str]
    differences: List[str]
    common_themes: List[str]
    unique_contributions: Dict[str, List[str]]


class ExtractedData(BaseModel):
    """Extracted data model"""
    document_id: str
    methods: List[str] = []
    results: List[str] = []
    datasets: List[str] = []
    statistical_findings: List[Dict[str, Any]] = []
    key_conclusions: List[str] = []


class SummarizationService:
    """
    Document summarization service
    Requirements: 5.1, 5.2, 5.3
    """
    
    def __init__(
        self,
        llm_router: Optional[LLMRouter] = None,
        vector_store: Optional[QdrantVectorStore] = None,
        embedding_generator: Optional[EmbeddingGenerator] = None
    ):
        """
        Initialize summarization service
        
        Args:
            llm_router: LLM router for content generation
            vector_store: Vector store for document retrieval
            embedding_generator: Embedding generator
        """
        self.llm_router = llm_router or LLMRouter()
        self.vector_store = vector_store or QdrantVectorStore()
        self.embedding_generator = embedding_generator or EmbeddingGenerator()
    
    async def extract_sections(
        self,
        document_id: str,
        project_id: Optional[str] = None
    ) -> Dict[str, DocumentSection]:
        """
        Extract key sections from document
        Requirements: 5.1
        
        Args:
            document_id: Document ID
            project_id: Optional project ID
        
        Returns:
            Dict of section name to DocumentSection
        """
        try:
            logger.info(f"Extracting sections from document {document_id}")
            
            # Retrieve all chunks for document
            filter_conditions = {'document_id': document_id}
            if project_id:
                filter_conditions['project_id'] = project_id
            
            # Get all chunks (use a dummy embedding for retrieval)
            dummy_embedding = [0.0] * 384
            chunks = await asyncio.to_thread(
                self.vector_store.search,
                query_embedding=dummy_embedding,
                limit=1000,  # Get all chunks
                score_threshold=0.0,
                filter_conditions=filter_conditions
            )
            
            if not chunks:
                logger.warning(f"No chunks found for document {document_id}")
                return {}
            
            # Sort chunks by chunk_id to maintain order
            chunks = sorted(chunks, key=lambda x: x.get('chunk_id', 0))
            
            # Combine all text
            full_text = "\n\n".join([chunk['text'] for chunk in chunks])
            
            # Use LLM to identify and extract sections
            prompt = f"""Analyze the following research paper and extract the key sections.
Identify and extract content for these sections if present:
- Abstract
- Introduction
- Methods (or Methodology)
- Results
- Conclusion (or Discussion)

For each section found, provide:
1. Section name
2. The actual content from that section

Paper text:
{full_text[:15000]}  # Limit to avoid token limits

Return the sections in JSON format:
{{
    "abstract": "content here or null",
    "introduction": "content here or null",
    "methods": "content here or null",
    "results": "content here or null",
    "conclusion": "content here or null"
}}"""
            
            response = await self.llm_router.complete(
                query=prompt,
                context={"document_count": 1},
                temperature=0.1,
                max_tokens=2000,
                use_cache=True
            )
            
            # Parse response
            import json
            import re
            
            # Extract JSON from response
            content = response['content']
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            
            if json_match:
                sections_data = json.loads(json_match.group())
            else:
                # Fallback: create sections from chunks
                sections_data = {
                    "abstract": None,
                    "introduction": full_text[:1000] if len(full_text) > 1000 else full_text,
                    "methods": None,
                    "results": None,
                    "conclusion": None
                }
            
            # Convert to DocumentSection objects
            sections = {}
            for section_name, content in sections_data.items():
                if content:
                    sections[section_name] = DocumentSection(
                        section_name=section_name.title(),
                        content=content,
                        page_numbers=[]
                    )
            
            logger.info(f"Extracted {len(sections)} sections from document {document_id}")
            return sections
            
        except Exception as e:
            logger.error(f"Error extracting sections: {e}")
            # Return empty dict on error
            return {}
    
    async def generate_summary(
        self,
        document_id: str,
        project_id: Optional[str] = None,
        length: SummaryLength = SummaryLength.STANDARD,
        document_title: Optional[str] = None
    ) -> DocumentSummary:
        """
        Generate structured summary of document
        Requirements: 5.1, 5.2, 5.3
        
        Args:
            document_id: Document ID
            project_id: Optional project ID
            length: Summary length (brief, standard, detailed)
            document_title: Optional document title
        
        Returns:
            DocumentSummary with structured sections
        """
        start_time = time.time()
        
        try:
            logger.info(
                f"Generating {length.value} summary for document {document_id}"
            )
            
            # Extract sections
            sections = await self.extract_sections(document_id, project_id)
            
            if not sections:
                raise ValueError(f"Could not extract sections from document {document_id}")
            
            # Determine summary length parameters
            length_params = {
                SummaryLength.BRIEF: {
                    "section_sentences": 2,
                    "key_findings": 3,
                    "max_tokens": 500
                },
                SummaryLength.STANDARD: {
                    "section_sentences": 4,
                    "key_findings": 5,
                    "max_tokens": 1000
                },
                SummaryLength.DETAILED: {
                    "section_sentences": 8,
                    "key_findings": 10,
                    "max_tokens": 2000
                }
            }
            
            params = length_params[length]
            
            # Build context from sections
            context_parts = []
            for section_name, section in sections.items():
                context_parts.append(f"## {section.section_name}\n{section.content[:2000]}")
            
            context = "\n\n".join(context_parts)
            
            # Generate summary
            prompt = f"""Generate a structured summary of this research paper.

Paper sections:
{context}

Create a summary with approximately {params['section_sentences']} sentences per section.
Include:
1. Abstract summary (if available)
2. Introduction summary
3. Methods summary (if available)
4. Results summary (if available)
5. Conclusion summary (if available)
6. {params['key_findings']} key findings as bullet points

Return in JSON format:
{{
    "abstract": "summary or null",
    "introduction": "summary or null",
    "methods": "summary or null",
    "results": "summary or null",
    "conclusion": "summary or null",
    "key_findings": ["finding 1", "finding 2", ...]
}}"""
            
            response = await self.llm_router.complete(
                query=prompt,
                context={"document_count": 1},
                temperature=0.3,
                max_tokens=params['max_tokens'],
                use_cache=True
            )
            
            # Parse response
            import json
            import re
            from datetime import datetime
            
            content = response['content']
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            
            if json_match:
                summary_data = json.loads(json_match.group())
            else:
                # Fallback summary
                summary_data = {
                    "abstract": sections.get('abstract', {}).content[:500] if 'abstract' in sections else None,
                    "introduction": sections.get('introduction', {}).content[:500] if 'introduction' in sections else None,
                    "methods": sections.get('methods', {}).content[:500] if 'methods' in sections else None,
                    "results": sections.get('results', {}).content[:500] if 'results' in sections else None,
                    "conclusion": sections.get('conclusion', {}).content[:500] if 'conclusion' in sections else None,
                    "key_findings": ["Summary generation failed - manual review required"]
                }
            
            # Create DocumentSummary
            summary = DocumentSummary(
                document_id=document_id,
                document_title=document_title or document_id,
                summary_length=length,
                abstract=summary_data.get('abstract'),
                introduction=summary_data.get('introduction'),
                methods=summary_data.get('methods'),
                results=summary_data.get('results'),
                conclusion=summary_data.get('conclusion'),
                key_findings=summary_data.get('key_findings', []),
                generated_at=datetime.utcnow().isoformat()
            )
            
            elapsed = time.time() - start_time
            logger.info(
                f"Generated {length.value} summary for document {document_id} "
                f"in {elapsed:.2f}s"
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            raise


class ComparativeSummarizationService:
    """
    Comparative summarization service for multiple documents
    Requirements: 5.7
    """
    
    def __init__(
        self,
        llm_router: Optional[LLMRouter] = None,
        summarization_service: Optional[SummarizationService] = None
    ):
        """
        Initialize comparative summarization service
        
        Args:
            llm_router: LLM router
            summarization_service: Summarization service for individual documents
        """
        self.llm_router = llm_router or LLMRouter()
        self.summarization_service = summarization_service or SummarizationService(llm_router)
    
    async def generate_comparative_summary(
        self,
        document_ids: List[str],
        project_id: Optional[str] = None,
        document_titles: Optional[Dict[str, str]] = None
    ) -> ComparativeSummary:
        """
        Generate comparative summary for multiple documents
        Requirements: 5.7
        
        Args:
            document_ids: List of document IDs to compare
            project_id: Optional project ID
            document_titles: Optional mapping of document_id to title
        
        Returns:
            ComparativeSummary with similarities, differences, and themes
        """
        start_time = time.time()
        
        try:
            logger.info(f"Generating comparative summary for {len(document_ids)} documents")
            
            if len(document_ids) < 2:
                raise ValueError("Need at least 2 documents for comparative summary")
            
            # Generate individual summaries
            summary_tasks = [
                self.summarization_service.generate_summary(
                    document_id=doc_id,
                    project_id=project_id,
                    length=SummaryLength.STANDARD,
                    document_title=document_titles.get(doc_id) if document_titles else None
                )
                for doc_id in document_ids
            ]
            
            summaries = await asyncio.gather(*summary_tasks)
            
            # Build context from summaries
            context_parts = []
            for i, summary in enumerate(summaries):
                context_parts.append(
                    f"Document {i+1}: {summary.document_title}\n"
                    f"Key Findings: {', '.join(summary.key_findings[:5])}\n"
                    f"Methods: {summary.methods or 'N/A'}\n"
                    f"Results: {summary.results or 'N/A'}\n"
                    f"Conclusion: {summary.conclusion or 'N/A'}"
                )
            
            context = "\n\n".join(context_parts)
            
            # Generate comparative analysis
            prompt = f"""Analyze these {len(document_ids)} research papers and provide a comparative summary.

Papers:
{context}

Provide:
1. Similarities: What do these papers have in common? (methods, findings, conclusions)
2. Differences: How do these papers differ? (approaches, results, perspectives)
3. Common Themes: What are the recurring themes across papers?
4. Unique Contributions: What unique contribution does each paper make?

Return in JSON format:
{{
    "similarities": ["similarity 1", "similarity 2", ...],
    "differences": ["difference 1", "difference 2", ...],
    "common_themes": ["theme 1", "theme 2", ...],
    "unique_contributions": {{
        "Document 1": ["contribution 1", ...],
        "Document 2": ["contribution 1", ...],
        ...
    }}
}}"""
            
            response = await self.llm_router.complete(
                query=prompt,
                context={"document_count": len(document_ids)},
                temperature=0.3,
                max_tokens=1500,
                use_cache=True
            )
            
            # Parse response
            import json
            import re
            
            content = response['content']
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            
            if json_match:
                comparison_data = json.loads(json_match.group())
            else:
                # Fallback
                comparison_data = {
                    "similarities": ["Analysis failed - manual review required"],
                    "differences": [],
                    "common_themes": [],
                    "unique_contributions": {}
                }
            
            # Create ComparativeSummary
            comparative_summary = ComparativeSummary(
                document_ids=document_ids,
                similarities=comparison_data.get('similarities', []),
                differences=comparison_data.get('differences', []),
                common_themes=comparison_data.get('common_themes', []),
                unique_contributions=comparison_data.get('unique_contributions', {})
            )
            
            elapsed = time.time() - start_time
            logger.info(
                f"Generated comparative summary for {len(document_ids)} documents "
                f"in {elapsed:.2f}s"
            )
            
            return comparative_summary
            
        except Exception as e:
            logger.error(f"Error generating comparative summary: {e}")
            raise


class DataExtractionService:
    """
    Data extraction service for research papers
    Requirements: 6.1, 6.2, 6.3
    """
    
    def __init__(
        self,
        llm_router: Optional[LLMRouter] = None,
        vector_store: Optional[QdrantVectorStore] = None
    ):
        """
        Initialize data extraction service
        
        Args:
            llm_router: LLM router
            vector_store: Vector store
        """
        self.llm_router = llm_router or LLMRouter()
        self.vector_store = vector_store or QdrantVectorStore()
    
    async def extract_data(
        self,
        document_id: str,
        project_id: Optional[str] = None,
        data_types: Optional[List[str]] = None
    ) -> ExtractedData:
        """
        Extract specific data from research paper
        Requirements: 6.1, 6.2, 6.3
        
        Args:
            document_id: Document ID
            project_id: Optional project ID
            data_types: Optional list of data types to extract
                       (methods, results, datasets, statistical_findings, key_conclusions)
        
        Returns:
            ExtractedData with structured information
        """
        start_time = time.time()
        
        try:
            logger.info(f"Extracting data from document {document_id}")
            
            # Default to all data types
            if not data_types:
                data_types = ['methods', 'results', 'datasets', 'statistical_findings', 'key_conclusions']
            
            # Retrieve document chunks
            filter_conditions = {'document_id': document_id}
            if project_id:
                filter_conditions['project_id'] = project_id
            
            dummy_embedding = [0.0] * 384
            chunks = await asyncio.to_thread(
                self.vector_store.search,
                query_embedding=dummy_embedding,
                limit=1000,
                score_threshold=0.0,
                filter_conditions=filter_conditions
            )
            
            if not chunks:
                raise ValueError(f"No chunks found for document {document_id}")
            
            # Sort and combine chunks
            chunks = sorted(chunks, key=lambda x: x.get('chunk_id', 0))
            full_text = "\n\n".join([chunk['text'] for chunk in chunks])
            
            # Extract data using LLM
            prompt = f"""Extract the following information from this research paper:

{', '.join(data_types)}

Paper text:
{full_text[:15000]}

Return in JSON format:
{{
    "methods": ["method 1", "method 2", ...],
    "results": ["result 1", "result 2", ...],
    "datasets": ["dataset 1", "dataset 2", ...],
    "statistical_findings": [
        {{"metric": "accuracy", "value": "95%", "context": "on test set"}},
        ...
    ],
    "key_conclusions": ["conclusion 1", "conclusion 2", ...]
}}

Extract only the data types requested: {', '.join(data_types)}"""
            
            response = await self.llm_router.complete(
                query=prompt,
                context={"document_count": 1},
                temperature=0.1,
                max_tokens=2000,
                use_cache=True
            )
            
            # Parse response
            import json
            import re
            
            content = response['content']
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            
            if json_match:
                extracted_data = json.loads(json_match.group())
            else:
                # Fallback
                extracted_data = {
                    "methods": [],
                    "results": [],
                    "datasets": [],
                    "statistical_findings": [],
                    "key_conclusions": []
                }
            
            # Create ExtractedData
            data = ExtractedData(
                document_id=document_id,
                methods=extracted_data.get('methods', []),
                results=extracted_data.get('results', []),
                datasets=extracted_data.get('datasets', []),
                statistical_findings=extracted_data.get('statistical_findings', []),
                key_conclusions=extracted_data.get('key_conclusions', [])
            )
            
            elapsed = time.time() - start_time
            logger.info(
                f"Extracted data from document {document_id} in {elapsed:.2f}s"
            )
            
            return data
            
        except Exception as e:
            logger.error(f"Error extracting data: {e}")
            raise
    
    async def extract_data_from_multiple(
        self,
        document_ids: List[str],
        project_id: Optional[str] = None,
        data_types: Optional[List[str]] = None
    ) -> List[ExtractedData]:
        """
        Extract data from multiple documents
        Requirements: 6.1, 6.2
        
        Args:
            document_ids: List of document IDs
            project_id: Optional project ID
            data_types: Optional list of data types to extract
        
        Returns:
            List of ExtractedData for each document
        """
        try:
            logger.info(f"Extracting data from {len(document_ids)} documents")
            
            # Extract data from each document in parallel
            extraction_tasks = [
                self.extract_data(doc_id, project_id, data_types)
                for doc_id in document_ids
            ]
            
            results = await asyncio.gather(*extraction_tasks)
            
            logger.info(f"Extracted data from {len(results)} documents")
            return results
            
        except Exception as e:
            logger.error(f"Error extracting data from multiple documents: {e}")
            raise


class DataExportService:
    """
    Data export service for extracted data
    Requirements: 6.5
    """
    
    @staticmethod
    def export_to_csv(extracted_data: List[ExtractedData]) -> str:
        """
        Export extracted data to CSV format
        Requirements: 6.5
        
        Args:
            extracted_data: List of ExtractedData
        
        Returns:
            CSV string
        """
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Document ID',
            'Methods',
            'Results',
            'Datasets',
            'Statistical Findings',
            'Key Conclusions'
        ])
        
        # Write data
        for data in extracted_data:
            writer.writerow([
                data.document_id,
                '; '.join(data.methods),
                '; '.join(data.results),
                '; '.join(data.datasets),
                '; '.join([f"{f.get('metric', '')}: {f.get('value', '')}" for f in data.statistical_findings]),
                '; '.join(data.key_conclusions)
            ])
        
        return output.getvalue()
    
    @staticmethod
    def export_to_json(extracted_data: List[ExtractedData]) -> str:
        """
        Export extracted data to JSON format
        Requirements: 6.5
        
        Args:
            extracted_data: List of ExtractedData
        
        Returns:
            JSON string
        """
        import json
        
        data_list = [data.dict() for data in extracted_data]
        return json.dumps(data_list, indent=2)
    
    @staticmethod
    def export_to_excel(extracted_data: List[ExtractedData]) -> bytes:
        """
        Export extracted data to Excel format
        Requirements: 6.5
        
        Args:
            extracted_data: List of ExtractedData
        
        Returns:
            Excel file bytes
        """
        try:
            import openpyxl
            from openpyxl import Workbook
            import io
            
            wb = Workbook()
            ws = wb.active
            ws.title = "Extracted Data"
            
            # Write header
            headers = [
                'Document ID',
                'Methods',
                'Results',
                'Datasets',
                'Statistical Findings',
                'Key Conclusions'
            ]
            ws.append(headers)
            
            # Write data
            for data in extracted_data:
                ws.append([
                    data.document_id,
                    '; '.join(data.methods),
                    '; '.join(data.results),
                    '; '.join(data.datasets),
                    '; '.join([f"{f.get('metric', '')}: {f.get('value', '')}" for f in data.statistical_findings]),
                    '; '.join(data.key_conclusions)
                ])
            
            # Save to bytes
            output = io.BytesIO()
            wb.save(output)
            output.seek(0)
            
            return output.getvalue()
            
        except ImportError:
            logger.error("openpyxl not installed, cannot export to Excel")
            raise ValueError("Excel export requires openpyxl package")
