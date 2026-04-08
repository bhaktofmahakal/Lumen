"""
Citation Management Service
Handles citation import, metadata enrichment, and bibliography generation
Requirements: 13.1, 13.2, 13.3, 13.5, 13.6, 13.7, 13.8, 13.9
"""

import logging
import re
import requests
from typing import Dict, List, Optional, Any, Tuple
import json
from datetime import datetime
import fitz  # PyMuPDF

from database import db_manager
from config import settings

logger = logging.getLogger(__name__)


class CitationExtractor:
    """Extract citations from PDF metadata and content"""
    
    def extract_from_pdf(self, pdf_path: str) -> Dict[str, Optional[str]]:
        """
        Extract citation metadata from PDF
        Requirements: 13.1
        
        Returns:
            Dict with DOI, arXiv ID, title, authors, etc.
        """
        try:
            doc = fitz.open(pdf_path)
            metadata = doc.metadata
            
            # Extract basic metadata
            result = {
                'title': metadata.get('title', '').strip() or None,
                'authors': self._parse_authors(metadata.get('author', '')),
                'doi': self._extract_doi(doc),
                'arxiv_id': self._extract_arxiv_id(doc),
                'pubmed_id': None,  # Can be added if needed
                'publication_year': self._extract_year(metadata),
                'journal': None,
                'volume': None,
                'issue': None,
                'pages': None
            }
            
            doc.close()
            return result
            
        except Exception as e:
            logger.error(f"Error extracting citation from PDF: {e}")
            return {}

    def _parse_authors(self, author_string: str) -> List[str]:
        """Parse author string into list of authors"""
        if not author_string:
            return []
        
        # Split by common delimiters
        authors = re.split(r'[,;]|\sand\s', author_string)
        return [a.strip() for a in authors if a.strip()]
    
    def _extract_doi(self, doc) -> Optional[str]:
        """Extract DOI from PDF content"""
        # Check first 3 pages for DOI
        for page_num in range(min(3, doc.page_count)):
            text = doc[page_num].get_text()
            
            # DOI pattern: 10.xxxx/xxxxx
            doi_pattern = r'10\.\d{4,}/[^\s]+'
            match = re.search(doi_pattern, text)
            if match:
                return match.group(0)
        
        return None
    
    def _extract_arxiv_id(self, doc) -> Optional[str]:
        """Extract arXiv ID from PDF content"""
        # Check first 2 pages for arXiv ID
        for page_num in range(min(2, doc.page_count)):
            text = doc[page_num].get_text()
            
            # arXiv pattern: arXiv:YYMM.NNNNN or YYMM.NNNNN
            arxiv_pattern = r'(?:arXiv:)?(\d{4}\.\d{4,5})'
            match = re.search(arxiv_pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_year(self, metadata: Dict) -> Optional[int]:
        """Extract publication year from metadata"""
        # Try creation date
        date_str = metadata.get('creationDate', '')
        if date_str:
            # Format: D:YYYYMMDDHHmmSS
            year_match = re.search(r'D:(\d{4})', date_str)
            if year_match:
                return int(year_match.group(1))
        
        return None


class CitationAPIClient:
    """Client for external citation APIs"""
    
    def __init__(self):
        self.crossref_base = "https://api.crossref.org/works"
        self.semantic_scholar_base = "https://api.semanticscholar.org/v1/paper"
        self.arxiv_base = "http://export.arxiv.org/api/query"

    def fetch_from_crossref(self, doi: str) -> Optional[Dict[str, Any]]:
        """
        Fetch citation metadata from Crossref API
        Requirements: 13.2
        
        Args:
            doi: DOI identifier
        
        Returns:
            Citation metadata dict
        """
        try:
            url = f"{self.crossref_base}/{doi}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                message = data.get('message', {})
                
                # Extract authors
                authors = []
                for author in message.get('author', []):
                    given = author.get('given', '')
                    family = author.get('family', '')
                    if given and family:
                        authors.append(f"{given} {family}")
                    elif family:
                        authors.append(family)
                
                # Extract publication year
                pub_date = message.get('published-print') or message.get('published-online')
                year = None
                if pub_date and 'date-parts' in pub_date:
                    year = pub_date['date-parts'][0][0] if pub_date['date-parts'][0] else None
                
                return {
                    'title': message.get('title', [''])[0],
                    'authors': authors,
                    'publication_year': year,
                    'journal': message.get('container-title', [''])[0],
                    'volume': message.get('volume'),
                    'issue': message.get('issue'),
                    'pages': message.get('page'),
                    'doi': doi,
                    'url': message.get('URL')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching from Crossref: {e}")
            return None

    def fetch_from_semantic_scholar(self, identifier: str, id_type: str = 'doi') -> Optional[Dict[str, Any]]:
        """
        Fetch citation metadata from Semantic Scholar API
        Requirements: 13.2
        
        Args:
            identifier: DOI or arXiv ID
            id_type: Type of identifier ('doi' or 'arxiv')
        
        Returns:
            Citation metadata dict
        """
        try:
            if id_type == 'arxiv':
                url = f"{self.semantic_scholar_base}/arXiv:{identifier}"
            else:
                url = f"{self.semantic_scholar_base}/{identifier}"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract authors
                authors = [author.get('name', '') for author in data.get('authors', [])]
                
                return {
                    'title': data.get('title'),
                    'authors': authors,
                    'publication_year': data.get('year'),
                    'journal': data.get('venue'),
                    'doi': data.get('doi'),
                    'arxiv_id': data.get('arxivId'),
                    'url': data.get('url'),
                    'abstract': data.get('abstract')
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching from Semantic Scholar: {e}")
            return None
    
    def fetch_from_arxiv(self, arxiv_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch citation metadata from arXiv API
        Requirements: 13.2
        
        Args:
            arxiv_id: arXiv identifier
        
        Returns:
            Citation metadata dict
        """
        try:
            url = f"{self.arxiv_base}?id_list={arxiv_id}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.content)
                
                # Parse XML response
                ns = {'atom': 'http://www.w3.org/2005/Atom'}
                entry = root.find('atom:entry', ns)
                
                if entry is not None:
                    # Extract authors
                    authors = []
                    for author in entry.findall('atom:author', ns):
                        name = author.find('atom:name', ns)
                        if name is not None:
                            authors.append(name.text)
                    
                    # Extract publication date
                    published = entry.find('atom:published', ns)
                    year = None
                    if published is not None:
                        year = int(published.text[:4])
                    
                    title_elem = entry.find('atom:title', ns)
                    summary_elem = entry.find('atom:summary', ns)
                    
                    return {
                        'title': title_elem.text.strip() if title_elem is not None else None,
                        'authors': authors,
                        'publication_year': year,
                        'arxiv_id': arxiv_id,
                        'url': f"https://arxiv.org/abs/{arxiv_id}",
                        'abstract': summary_elem.text.strip() if summary_elem is not None else None
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching from arXiv: {e}")
            return None



class BibTeXGenerator:
    """Generate BibTeX entries from citation metadata"""
    
    def generate_bibtex(self, citation: Dict[str, Any], citation_key: str) -> str:
        """
        Generate BibTeX entry from citation metadata
        Requirements: 13.5
        
        Args:
            citation: Citation metadata dict
            citation_key: Citation key for BibTeX
        
        Returns:
            BibTeX entry string
        """
        # Determine entry type
        if citation.get('journal'):
            entry_type = 'article'
        elif citation.get('arxiv_id'):
            entry_type = 'misc'
        else:
            entry_type = 'article'
        
        # Build BibTeX entry
        bibtex = f"@{entry_type}{{{citation_key},\n"
        
        if citation.get('title'):
            bibtex += f"  title = {{{citation['title']}}},\n"
        
        if citation.get('authors'):
            authors_str = ' and '.join(citation['authors'])
            bibtex += f"  author = {{{authors_str}}},\n"
        
        if citation.get('publication_year'):
            bibtex += f"  year = {{{citation['publication_year']}}},\n"
        
        if citation.get('journal'):
            bibtex += f"  journal = {{{citation['journal']}}},\n"
        
        if citation.get('volume'):
            bibtex += f"  volume = {{{citation['volume']}}},\n"
        
        if citation.get('issue'):
            bibtex += f"  number = {{{citation['issue']}}},\n"
        
        if citation.get('pages'):
            bibtex += f"  pages = {{{citation['pages']}}},\n"
        
        if citation.get('doi'):
            bibtex += f"  doi = {{{citation['doi']}}},\n"
        
        if citation.get('url'):
            bibtex += f"  url = {{{citation['url']}}},\n"
        
        if citation.get('arxiv_id'):
            bibtex += f"  eprint = {{{citation['arxiv_id']}}},\n"
            bibtex += f"  archivePrefix = {{arXiv}},\n"
        
        bibtex += "}\n"
        
        return bibtex

    def format_citation(self, citation: Dict[str, Any], style: str = 'APA') -> str:
        """
        Format citation in specified style
        Requirements: 13.6, 13.7
        
        Args:
            citation: Citation metadata dict
            style: Citation style (APA, MLA, Chicago, IEEE)
        
        Returns:
            Formatted citation string
        """
        if style == 'APA':
            return self._format_apa(citation)
        elif style == 'MLA':
            return self._format_mla(citation)
        elif style == 'Chicago':
            return self._format_chicago(citation)
        elif style == 'IEEE':
            return self._format_ieee(citation)
        else:
            return self._format_apa(citation)
    
    def _format_apa(self, citation: Dict[str, Any]) -> str:
        """Format citation in APA style"""
        parts = []
        
        # Authors (Last, F. M.)
        if citation.get('authors'):
            if len(citation['authors']) == 1:
                parts.append(citation['authors'][0])
            elif len(citation['authors']) == 2:
                parts.append(f"{citation['authors'][0]} & {citation['authors'][1]}")
            else:
                parts.append(f"{citation['authors'][0]} et al.")
        
        # Year
        if citation.get('publication_year'):
            parts.append(f"({citation['publication_year']})")
        
        # Title
        if citation.get('title'):
            parts.append(f"{citation['title']}.")
        
        # Journal
        if citation.get('journal'):
            journal_part = citation['journal']
            if citation.get('volume'):
                journal_part += f", {citation['volume']}"
            if citation.get('pages'):
                journal_part += f", {citation['pages']}"
            parts.append(f"{journal_part}.")
        
        # DOI
        if citation.get('doi'):
            parts.append(f"https://doi.org/{citation['doi']}")
        
        return ' '.join(parts)
    
    def _format_mla(self, citation: Dict[str, Any]) -> str:
        """Format citation in MLA style"""
        parts = []
        
        # Authors (Last, First)
        if citation.get('authors'):
            parts.append(f"{citation['authors'][0]}.")
        
        # Title
        if citation.get('title'):
            parts.append(f'"{citation["title"]}."')
        
        # Journal
        if citation.get('journal'):
            parts.append(f"{citation['journal']},")
        
        # Volume and issue
        if citation.get('volume'):
            vol_part = f"vol. {citation['volume']}"
            if citation.get('issue'):
                vol_part += f", no. {citation['issue']}"
            parts.append(f"{vol_part},")
        
        # Year
        if citation.get('publication_year'):
            parts.append(f"{citation['publication_year']},")
        
        # Pages
        if citation.get('pages'):
            parts.append(f"pp. {citation['pages']}.")
        
        return ' '.join(parts)

    def _format_chicago(self, citation: Dict[str, Any]) -> str:
        """Format citation in Chicago style"""
        parts = []
        
        # Authors (Last, First)
        if citation.get('authors'):
            parts.append(f"{citation['authors'][0]}.")
        
        # Title
        if citation.get('title'):
            parts.append(f'"{citation["title"]}."')
        
        # Journal
        if citation.get('journal'):
            parts.append(citation['journal'])
        
        # Volume and issue
        if citation.get('volume'):
            vol_part = f"{citation['volume']}"
            if citation.get('issue'):
                vol_part += f", no. {citation['issue']}"
            parts.append(vol_part)
        
        # Year and pages
        if citation.get('publication_year'):
            year_part = f"({citation['publication_year']})"
            if citation.get('pages'):
                year_part += f": {citation['pages']}"
            parts.append(f"{year_part}.")
        
        return ' '.join(parts)
    
    def _format_ieee(self, citation: Dict[str, Any]) -> str:
        """Format citation in IEEE style"""
        parts = []
        
        # Authors (F. Last)
        if citation.get('authors'):
            if len(citation['authors']) <= 3:
                parts.append(', '.join(citation['authors']))
            else:
                parts.append(f"{citation['authors'][0]} et al.")
        
        # Title
        if citation.get('title'):
            parts.append(f'"{citation["title"]},"')
        
        # Journal
        if citation.get('journal'):
            parts.append(f"{citation['journal']},")
        
        # Volume, issue, pages, year
        vol_parts = []
        if citation.get('volume'):
            vol_parts.append(f"vol. {citation['volume']}")
        if citation.get('issue'):
            vol_parts.append(f"no. {citation['issue']}")
        if citation.get('pages'):
            vol_parts.append(f"pp. {citation['pages']}")
        if citation.get('publication_year'):
            vol_parts.append(str(citation['publication_year']))
        
        if vol_parts:
            parts.append(', '.join(vol_parts) + '.')
        
        return ' '.join(parts)



class CitationExporter:
    """Export citations in various formats"""
    
    def export_bibtex(self, citations: List[Dict[str, Any]]) -> str:
        """
        Export citations as BibTeX
        Requirements: 13.9
        
        Args:
            citations: List of citation dicts
        
        Returns:
            BibTeX formatted string
        """
        generator = BibTeXGenerator()
        bibtex_entries = []
        
        for citation in citations:
            citation_key = citation.get('citation_key', f"ref{citation.get('id', '')}")
            bibtex = generator.generate_bibtex(citation, citation_key)
            bibtex_entries.append(bibtex)
        
        return '\n'.join(bibtex_entries)
    
    def export_ris(self, citations: List[Dict[str, Any]]) -> str:
        """
        Export citations as RIS format
        Requirements: 13.9
        
        Args:
            citations: List of citation dicts
        
        Returns:
            RIS formatted string
        """
        ris_entries = []
        
        for citation in citations:
            ris = "TY  - JOUR\n"  # Journal article
            
            if citation.get('title'):
                ris += f"TI  - {citation['title']}\n"
            
            if citation.get('authors'):
                for author in citation['authors']:
                    ris += f"AU  - {author}\n"
            
            if citation.get('publication_year'):
                ris += f"PY  - {citation['publication_year']}\n"
            
            if citation.get('journal'):
                ris += f"JO  - {citation['journal']}\n"
            
            if citation.get('volume'):
                ris += f"VL  - {citation['volume']}\n"
            
            if citation.get('issue'):
                ris += f"IS  - {citation['issue']}\n"
            
            if citation.get('pages'):
                ris += f"SP  - {citation['pages']}\n"
            
            if citation.get('doi'):
                ris += f"DO  - {citation['doi']}\n"
            
            if citation.get('url'):
                ris += f"UR  - {citation['url']}\n"
            
            ris += "ER  - \n\n"
            ris_entries.append(ris)
        
        return ''.join(ris_entries)

    def export_endnote(self, citations: List[Dict[str, Any]]) -> str:
        """
        Export citations as EndNote XML format
        Requirements: 13.9
        
        Args:
            citations: List of citation dicts
        
        Returns:
            EndNote XML formatted string
        """
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += '<xml>\n<records>\n'
        
        for citation in citations:
            xml += '<record>\n'
            xml += '<ref-type name="Journal Article">17</ref-type>\n'
            
            if citation.get('title'):
                xml += f'<titles><title>{citation["title"]}</title></titles>\n'
            
            if citation.get('authors'):
                xml += '<contributors><authors>\n'
                for author in citation['authors']:
                    xml += f'<author>{author}</author>\n'
                xml += '</authors></contributors>\n'
            
            if citation.get('publication_year'):
                xml += f'<dates><year>{citation["publication_year"]}</year></dates>\n'
            
            if citation.get('journal'):
                xml += f'<periodical><full-title>{citation["journal"]}</full-title></periodical>\n'
            
            if citation.get('volume'):
                xml += f'<volume>{citation["volume"]}</volume>\n'
            
            if citation.get('issue'):
                xml += f'<number>{citation["issue"]}</number>\n'
            
            if citation.get('pages'):
                xml += f'<pages>{citation["pages"]}</pages>\n'
            
            if citation.get('doi'):
                xml += f'<electronic-resource-num>{citation["doi"]}</electronic-resource-num>\n'
            
            if citation.get('url'):
                xml += f'<urls><related-urls><url>{citation["url"]}</url></related-urls></urls>\n'
            
            xml += '</record>\n'
        
        xml += '</records>\n</xml>'
        return xml


class CitationService:
    """Main citation management service"""
    
    def __init__(self):
        self.extractor = CitationExtractor()
        self.api_client = CitationAPIClient()
        self.bibtex_generator = BibTeXGenerator()
        self.exporter = CitationExporter()
    
    async def import_citation_from_pdf(
        self,
        pdf_path: str,
        project_id: str,
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Import citation from PDF with metadata enrichment
        Requirements: 13.1, 13.2
        
        Args:
            pdf_path: Path to PDF file
            project_id: Project ID
            document_id: Optional document ID
        
        Returns:
            Citation metadata dict
        """
        # Extract metadata from PDF
        metadata = self.extractor.extract_from_pdf(pdf_path)
        
        # Enrich with external APIs
        enriched_metadata = await self._enrich_metadata(metadata)
        
        # Generate citation key
        citation_key = self._generate_citation_key(enriched_metadata)
        
        # Check for duplicates
        duplicate = await self._check_duplicate(project_id, citation_key)
        if duplicate:
            logger.warning(f"Duplicate citation found: {citation_key}")
            return {
                'status': 'duplicate',
                'citation': duplicate,
                'message': f"Citation {citation_key} already exists in project"
            }
        
        # Store in database
        citation_data = {
            'project_id': project_id,
            'document_id': document_id,
            'citation_key': citation_key,
            'title': enriched_metadata.get('title'),
            'authors': json.dumps(enriched_metadata.get('authors', [])),
            'publication_year': enriched_metadata.get('publication_year'),
            'journal': enriched_metadata.get('journal'),
            'volume': enriched_metadata.get('volume'),
            'issue': enriched_metadata.get('issue'),
            'pages': enriched_metadata.get('pages'),
            'doi': enriched_metadata.get('doi'),
            'arxiv_id': enriched_metadata.get('arxiv_id'),
            'url': enriched_metadata.get('url'),
            'bibtex': self.bibtex_generator.generate_bibtex(enriched_metadata, citation_key),
            'citation_format': 'APA'
        }
        
        await self._store_citation(citation_data)
        
        return {
            'status': 'success',
            'citation': citation_data,
            'message': f"Citation {citation_key} imported successfully"
        }

    async def _enrich_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich metadata using external APIs
        Requirements: 13.2
        """
        enriched = metadata.copy()
        
        # Try Crossref if DOI available
        if metadata.get('doi'):
            crossref_data = self.api_client.fetch_from_crossref(metadata['doi'])
            if crossref_data:
                # Merge data, preferring Crossref
                for key, value in crossref_data.items():
                    if value and not enriched.get(key):
                        enriched[key] = value
        
        # Try Semantic Scholar if DOI or arXiv ID available
        if metadata.get('doi'):
            ss_data = self.api_client.fetch_from_semantic_scholar(metadata['doi'], 'doi')
            if ss_data:
                for key, value in ss_data.items():
                    if value and not enriched.get(key):
                        enriched[key] = value
        elif metadata.get('arxiv_id'):
            ss_data = self.api_client.fetch_from_semantic_scholar(metadata['arxiv_id'], 'arxiv')
            if ss_data:
                for key, value in ss_data.items():
                    if value and not enriched.get(key):
                        enriched[key] = value
        
        # Try arXiv if arXiv ID available
        if metadata.get('arxiv_id'):
            arxiv_data = self.api_client.fetch_from_arxiv(metadata['arxiv_id'])
            if arxiv_data:
                for key, value in arxiv_data.items():
                    if value and not enriched.get(key):
                        enriched[key] = value
        
        return enriched
    
    def _generate_citation_key(self, metadata: Dict[str, Any]) -> str:
        """Generate citation key from metadata"""
        # Format: FirstAuthorLastNameYYYY
        key_parts = []
        
        if metadata.get('authors') and len(metadata['authors']) > 0:
            # Get last name of first author
            first_author = metadata['authors'][0]
            last_name = first_author.split()[-1]
            key_parts.append(last_name.replace(' ', ''))
        else:
            key_parts.append('Unknown')
        
        if metadata.get('publication_year'):
            key_parts.append(str(metadata['publication_year']))
        else:
            key_parts.append(str(datetime.now().year))
        
        return ''.join(key_parts)
    
    async def _check_duplicate(self, project_id: str, citation_key: str) -> Optional[Dict]:
        """Check if citation already exists in project"""
        conn = db_manager.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                SELECT * FROM citations 
                WHERE project_id = %s AND citation_key = %s
                LIMIT 1
                """
                cursor.execute(sql, (project_id, citation_key))
                return cursor.fetchone()
        finally:
            conn.close()
    
    async def _store_citation(self, citation_data: Dict[str, Any]):
        """Store citation in database"""
        conn = db_manager.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                INSERT INTO citations (
                    project_id, document_id, citation_key, title, authors,
                    publication_year, journal, volume, issue, pages,
                    doi, arxiv_id, url, bibtex, citation_format
                ) VALUES (
                    %(project_id)s, %(document_id)s, %(citation_key)s, %(title)s, %(authors)s,
                    %(publication_year)s, %(journal)s, %(volume)s, %(issue)s, %(pages)s,
                    %(doi)s, %(arxiv_id)s, %(url)s, %(bibtex)s, %(citation_format)s
                )
                """
                cursor.execute(sql, citation_data)
                conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Error storing citation: {e}")
            raise
        finally:
            conn.close()

    async def create_citation(
        self,
        project_id: str,
        citation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create citation manually
        Requirements: 13.3
        
        Args:
            project_id: Project ID
            citation_data: Citation metadata
        
        Returns:
            Created citation dict
        """
        # Generate citation key if not provided
        if not citation_data.get('citation_key'):
            citation_data['citation_key'] = self._generate_citation_key(citation_data)
        
        # Check for duplicates
        duplicate = await self._check_duplicate(project_id, citation_data['citation_key'])
        if duplicate:
            return {
                'status': 'duplicate',
                'citation': duplicate,
                'message': f"Citation {citation_data['citation_key']} already exists"
            }
        
        # Generate BibTeX
        citation_data['bibtex'] = self.bibtex_generator.generate_bibtex(
            citation_data,
            citation_data['citation_key']
        )
        
        # Store citation
        citation_data['project_id'] = project_id
        citation_data['authors'] = json.dumps(citation_data.get('authors', []))
        await self._store_citation(citation_data)
        
        return {
            'status': 'success',
            'citation': citation_data,
            'message': 'Citation created successfully'
        }
    
    async def get_citations(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get all citations for a project
        Requirements: 13.3
        """
        conn = db_manager.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                SELECT * FROM citations 
                WHERE project_id = %s
                ORDER BY created_at DESC
                """
                cursor.execute(sql, (project_id,))
                citations = cursor.fetchall()
                
                # Parse authors JSON
                for citation in citations:
                    if citation.get('authors'):
                        try:
                            citation['authors'] = json.loads(citation['authors'])
                        except:
                            citation['authors'] = []
                
                return citations
        finally:
            conn.close()
    
    async def update_citation(
        self,
        citation_id: int,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update citation
        Requirements: 13.3
        """
        conn = db_manager.get_connection()
        try:
            with conn.cursor() as cursor:
                # Build update query
                set_clauses = []
                values = []
                
                for key, value in updates.items():
                    if key in ['title', 'publication_year', 'journal', 'volume', 'issue', 'pages', 'doi', 'arxiv_id', 'url', 'citation_format']:
                        set_clauses.append(f"{key} = %s")
                        values.append(value)
                    elif key == 'authors':
                        set_clauses.append("authors = %s")
                        values.append(json.dumps(value))
                
                if not set_clauses:
                    return {'status': 'error', 'message': 'No valid fields to update'}
                
                values.append(citation_id)
                sql = f"UPDATE citations SET {', '.join(set_clauses)} WHERE id = %s"
                cursor.execute(sql, values)
                conn.commit()
                
                return {'status': 'success', 'message': 'Citation updated successfully'}
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating citation: {e}")
            raise
        finally:
            conn.close()
    
    async def delete_citation(self, citation_id: int) -> Dict[str, Any]:
        """
        Delete citation
        Requirements: 13.3
        """
        conn = db_manager.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = "DELETE FROM citations WHERE id = %s"
                cursor.execute(sql, (citation_id,))
                conn.commit()
                
                return {'status': 'success', 'message': 'Citation deleted successfully'}
        except Exception as e:
            conn.rollback()
            logger.error(f"Error deleting citation: {e}")
            raise
        finally:
            conn.close()

    async def update_citation_format(
        self,
        project_id: str,
        new_format: str
    ) -> Dict[str, Any]:
        """
        Update citation format for all citations in project
        Requirements: 13.7
        
        Args:
            project_id: Project ID
            new_format: New citation format (APA, MLA, Chicago, IEEE)
        
        Returns:
            Status dict
        """
        if new_format not in ['APA', 'MLA', 'Chicago', 'IEEE']:
            return {'status': 'error', 'message': 'Invalid citation format'}
        
        conn = db_manager.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                UPDATE citations 
                SET citation_format = %s
                WHERE project_id = %s
                """
                cursor.execute(sql, (new_format, project_id))
                conn.commit()
                
                return {
                    'status': 'success',
                    'message': f'Citation format updated to {new_format}',
                    'updated_count': cursor.rowcount
                }
        except Exception as e:
            conn.rollback()
            logger.error(f"Error updating citation format: {e}")
            raise
        finally:
            conn.close()
    
    async def export_citations(
        self,
        project_id: str,
        format: str = 'bibtex'
    ) -> str:
        """
        Export citations in specified format
        Requirements: 13.9
        
        Args:
            project_id: Project ID
            format: Export format (bibtex, ris, endnote)
        
        Returns:
            Formatted citation string
        """
        citations = await self.get_citations(project_id)
        
        if format == 'bibtex':
            return self.exporter.export_bibtex(citations)
        elif format == 'ris':
            return self.exporter.export_ris(citations)
        elif format == 'endnote':
            return self.exporter.export_endnote(citations)
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Global citation service instance
citation_service = CitationService()
