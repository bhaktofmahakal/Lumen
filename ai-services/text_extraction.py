"""
Text extraction from PDF documents using multiple strategies
"""

import fitz  # PyMuPDF
from typing import Dict, List, Tuple, Optional
import logging
import re
from pathlib import Path

from models import DocumentType

logger = logging.getLogger(__name__)


class PDFMetadataExtractor:
    """Extract metadata from PDF documents"""
    
    def extract_metadata(self, pdf_path: str) -> Dict[str, Optional[str]]:
        """
        Extract metadata from PDF
        Requirements: 1.2
        """
        try:
            doc = fitz.open(pdf_path)
            metadata = doc.metadata
            
            # Extract basic metadata
            result = {
                'title': metadata.get('title', '').strip() or None,
                'author': metadata.get('author', '').strip() or None,
                'subject': metadata.get('subject', '').strip() or None,
                'keywords': metadata.get('keywords', '').strip() or None,
                'creator': metadata.get('creator', '').strip() or None,
                'producer': metadata.get('producer', '').strip() or None,
                'creation_date': metadata.get('creationDate', '').strip() or None,
                'modification_date': metadata.get('modDate', '').strip() or None,
            }
            
            # Parse authors if available
            authors = []
            if result['author']:
                # Split by common delimiters
                authors = [a.strip() for a in re.split(r'[,;]|\sand\s', result['author']) if a.strip()]
            
            result['authors'] = authors if authors else None
            
            doc.close()
            return result
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return {}


class StandardPDFExtractor:
    """Extract text from standard PDFs using PyMuPDF"""
    
    def extract_text(self, pdf_path: str) -> Tuple[str, Dict]:
        """
        Extract text from standard PDF
        Requirements: 1.2
        
        Returns:
            Tuple of (extracted_text, metadata)
        """
        try:
            doc = fitz.open(pdf_path)
            
            # Extract text from all pages
            text_parts = []
            for page_num, page in enumerate(doc, start=1):
                page_text = page.get_text()
                if page_text.strip():
                    text_parts.append(f"[Page {page_num}]\n{page_text}")
            
            full_text = "\n\n".join(text_parts)
            
            # Extract metadata
            metadata_extractor = PDFMetadataExtractor()
            metadata = metadata_extractor.extract_metadata(pdf_path)
            page_count = doc.page_count
            metadata['page_count'] = page_count
            
            doc.close()
            
            logger.info(f"Extracted {len(full_text)} characters from {page_count} pages")
            return full_text, metadata
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise


class ScannedPDFExtractor:
    """Extract text from scanned PDFs using Tesseract OCR"""
    
    def __init__(self):
        self.tesseract_available = self._check_tesseract()
    
    def _check_tesseract(self) -> bool:
        """Check if Tesseract is available"""
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            return True
        except:
            logger.warning("Tesseract OCR not available")
            return False
    
    def extract_text(self, pdf_path: str) -> Tuple[str, Dict]:
        """
        Extract text from scanned PDF using OCR
        Requirements: 1.3
        
        Returns:
            Tuple of (extracted_text, metadata)
        """
        if not self.tesseract_available:
            raise RuntimeError("Tesseract OCR is not installed or not available")
        
        try:
            import pytesseract
            from PIL import Image
            
            doc = fitz.open(pdf_path)
            text_parts = []
            
            # Convert each page to image and OCR
            for page_num, page in enumerate(doc, start=1):
                # Render page to image
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x resolution for better OCR
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # Apply OCR
                page_text = pytesseract.image_to_string(img, lang='eng')
                
                if page_text.strip():
                    text_parts.append(f"[Page {page_num}]\n{page_text}")
            
            full_text = "\n\n".join(text_parts)
            
            metadata = {
                'page_count': doc.page_count,
                'extraction_method': 'tesseract_ocr'
            }
            
            doc.close()
            
            logger.info(f"OCR extracted {len(full_text)} characters from {doc.page_count} pages")
            return full_text, metadata
            
        except Exception as e:
            logger.error(f"Error extracting text with OCR: {e}")
            raise


class ScientificPDFExtractor:
    """Extract text from scientific PDFs with equations using Marker and Nougat"""
    
    def __init__(self):
        self.marker_available = self._check_marker()
        self.nougat_available = self._check_nougat()
    
    def _check_marker(self) -> bool:
        """Check if Marker is available"""
        try:
            import marker
            return True
        except ImportError:
            logger.warning("Marker not available - install with: pip install marker-pdf")
            return False
    
    def _check_nougat(self) -> bool:
        """Check if Nougat is available"""
        try:
            import nougat
            return True
        except ImportError:
            logger.warning("Nougat not available - install with: pip install nougat-ocr")
            return False
    
    def extract_with_marker(self, pdf_path: str) -> Tuple[str, Dict]:
        """
        Extract text using Marker for scientific document parsing
        Marker handles complex layouts, tables, and figures
        """
        try:
            from marker.convert import convert_single_pdf
            from marker.models import load_all_models
            
            # Load Marker models
            models = load_all_models()
            
            # Convert PDF to markdown
            full_text, images, metadata = convert_single_pdf(pdf_path, models)
            
            result_metadata = {
                'extraction_method': 'marker',
                'page_count': metadata.get('page_count', 0),
                'has_tables': metadata.get('has_tables', False),
                'has_figures': len(images) > 0,
                'figure_count': len(images)
            }
            
            logger.info(f"Marker extracted {len(full_text)} characters with {len(images)} figures")
            return full_text, result_metadata
            
        except Exception as e:
            logger.error(f"Marker extraction failed: {e}")
            raise
    
    def extract_equations_with_nougat(self, pdf_path: str) -> List[Dict]:
        """
        Extract equations using Nougat for LaTeX conversion
        Requirements: 1.12
        """
        try:
            from nougat import NougatModel
            from nougat.utils.checkpoint import get_checkpoint
            
            # Load Nougat model
            checkpoint = get_checkpoint()
            model = NougatModel.from_pretrained(checkpoint)
            
            # Extract equations
            equations = model.predict(pdf_path)
            
            logger.info(f"Nougat extracted {len(equations)} equations")
            return equations
            
        except Exception as e:
            logger.error(f"Nougat extraction failed: {e}")
            return []
    
    def extract_text(self, pdf_path: str) -> Tuple[str, Dict]:
        """
        Extract text from scientific PDF
        Requirements: 1.12
        
        Strategy:
        1. Try Marker for full document parsing (tables, figures, equations)
        2. If Marker unavailable, use Nougat for equations + PyMuPDF for text
        3. Fall back to standard PyMuPDF if neither available
        """
        
        # Try Marker first (best for scientific PDFs)
        if self.marker_available:
            try:
                return self.extract_with_marker(pdf_path)
            except Exception as e:
                logger.warning(f"Marker extraction failed, falling back: {e}")
        
        # Try Nougat + PyMuPDF combination
        if self.nougat_available:
            try:
                # Extract text with PyMuPDF
                extractor = StandardPDFExtractor()
                text, metadata = extractor.extract_text(pdf_path)
                
                # Extract equations with Nougat
                equations = self.extract_equations_with_nougat(pdf_path)
                
                # Append equations to text
                if equations:
                    text += "\n\n[Extracted Equations]\n"
                    for i, eq in enumerate(equations, 1):
                        text += f"\nEquation {i}:\n{eq.get('latex', '')}\n"
                
                metadata['extraction_method'] = 'pymupdf_nougat'
                metadata['equation_count'] = len(equations)
                
                return text, metadata
                
            except Exception as e:
                logger.warning(f"Nougat extraction failed, falling back: {e}")
        
        # Fall back to standard extraction
        logger.info("Scientific PDF extraction - using standard PyMuPDF (Marker/Nougat not available)")
        extractor = StandardPDFExtractor()
        text, metadata = extractor.extract_text(pdf_path)
        metadata['extraction_method'] = 'pymupdf_scientific_fallback'
        
        return text, metadata


class TextExtractionService:
    """Main text extraction service that routes to appropriate extractor"""
    
    def __init__(self):
        self.standard_extractor = StandardPDFExtractor()
        self.scanned_extractor = ScannedPDFExtractor()
        self.scientific_extractor = ScientificPDFExtractor()
    
    def extract_text(self, pdf_path: str, document_type: DocumentType) -> Tuple[str, Dict]:
        """
        Extract text from PDF based on document type
        Requirements: 1.2, 1.3, 1.12
        
        Args:
            pdf_path: Path to PDF file
            document_type: Type of document (standard, scientific, complex, scanned)
        
        Returns:
            Tuple of (extracted_text, metadata)
        """
        try:
            if document_type == DocumentType.SCANNED:
                return self.scanned_extractor.extract_text(pdf_path)
            elif document_type == DocumentType.SCIENTIFIC:
                return self.scientific_extractor.extract_text(pdf_path)
            else:
                # Standard and complex both use standard extraction
                return self.standard_extractor.extract_text(pdf_path)
        
        except Exception as e:
            logger.error(f"Text extraction failed for {pdf_path}: {e}")
            raise


# Global text extraction service instance
text_extraction_service = TextExtractionService()
