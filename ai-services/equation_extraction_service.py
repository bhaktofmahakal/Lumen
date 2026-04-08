"""
Equation Extraction and LaTeX Conversion Service
Extracts equations from PDFs and converts to LaTeX format
Requirements: 6.7, 14.1, 14.2, 14.8
"""

import logging
import time
from typing import List, Dict, Optional, Any, Tuple
from pydantic import BaseModel
import asyncio
import tempfile
import os

logger = logging.getLogger(__name__)


class ExtractedEquation(BaseModel):
    """Extracted equation model"""
    equation_id: str
    original_image: Optional[str] = None  # Base64 encoded image
    latex_code: str
    equation_type: str  # "inline" or "display"
    page_number: Optional[int] = None
    confidence: float = 0.0
    bounding_box: Optional[Dict[str, float]] = None


class EquationExtractionService:
    """
    Equation extraction and LaTeX conversion service
    Requirements: 6.7, 14.1, 14.2
    """
    
    def __init__(self):
        """Initialize equation extraction service"""
        self.nougat_available = self._check_nougat_availability()
        
        if not self.nougat_available:
            logger.warning(
                "Nougat not available. Equation extraction will use fallback OCR method."
            )
    
    def _check_nougat_availability(self) -> bool:
        """Check if Nougat is available"""
        try:
            import subprocess
            result = subprocess.run(
                ['nougat', '--version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    async def extract_equations_from_pdf(
        self,
        pdf_path: str,
        page_numbers: Optional[List[int]] = None
    ) -> List[ExtractedEquation]:
        """
        Extract equations from PDF using Nougat
        Requirements: 6.7, 14.1
        
        Args:
            pdf_path: Path to PDF file
            page_numbers: Optional list of page numbers to process
        
        Returns:
            List of ExtractedEquation objects
        """
        start_time = time.time()
        
        try:
            logger.info(f"Extracting equations from PDF: {pdf_path}")
            
            if self.nougat_available:
                equations = await self._extract_with_nougat(pdf_path, page_numbers)
            else:
                equations = await self._extract_with_fallback(pdf_path, page_numbers)
            
            elapsed = time.time() - start_time
            logger.info(
                f"Extracted {len(equations)} equations from PDF in {elapsed:.2f}s"
            )
            
            return equations
            
        except Exception as e:
            logger.error(f"Error extracting equations from PDF: {e}")
            raise
    
    async def _extract_with_nougat(
        self,
        pdf_path: str,
        page_numbers: Optional[List[int]] = None
    ) -> List[ExtractedEquation]:
        """
        Extract equations using Nougat
        
        Args:
            pdf_path: Path to PDF file
            page_numbers: Optional list of page numbers
        
        Returns:
            List of ExtractedEquation objects
        """
        import subprocess
        import re
        
        try:
            # Create temporary output directory
            with tempfile.TemporaryDirectory() as temp_dir:
                # Run Nougat
                cmd = [
                    'nougat',
                    pdf_path,
                    '-o', temp_dir,
                    '--no-skipping'
                ]
                
                if page_numbers:
                    # Nougat uses 0-indexed pages
                    pages_str = ','.join([str(p - 1) for p in page_numbers])
                    cmd.extend(['--pages', pages_str])
                
                logger.info(f"Running Nougat: {' '.join(cmd)}")
                
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    logger.error(f"Nougat failed: {stderr.decode()}")
                    raise RuntimeError(f"Nougat extraction failed: {stderr.decode()}")
                
                # Read output markdown file
                output_files = [f for f in os.listdir(temp_dir) if f.endswith('.mmd')]
                
                if not output_files:
                    logger.warning("No output files from Nougat")
                    return []
                
                output_path = os.path.join(temp_dir, output_files[0])
                
                with open(output_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract equations from markdown
                equations = self._parse_equations_from_markdown(content)
                
                return equations
                
        except Exception as e:
            logger.error(f"Error in Nougat extraction: {e}")
            # Fallback to alternative method
            return await self._extract_with_fallback(pdf_path, page_numbers)
    
    def _parse_equations_from_markdown(self, markdown_content: str) -> List[ExtractedEquation]:
        """
        Parse equations from Nougat markdown output
        
        Args:
            markdown_content: Markdown content from Nougat
        
        Returns:
            List of ExtractedEquation objects
        """
        import re
        import uuid
        
        equations = []
        
        # Extract display equations ($$...$$)
        display_pattern = r'\$\$(.*?)\$\$'
        display_matches = re.finditer(display_pattern, markdown_content, re.DOTALL)
        
        for match in display_matches:
            latex_code = match.group(1).strip()
            
            equation = ExtractedEquation(
                equation_id=str(uuid.uuid4()),
                latex_code=latex_code,
                equation_type="display",
                confidence=0.9  # Nougat is generally reliable
            )
            equations.append(equation)
        
        # Extract inline equations ($...$)
        inline_pattern = r'(?<!\$)\$(?!\$)(.*?)(?<!\$)\$(?!\$)'
        inline_matches = re.finditer(inline_pattern, markdown_content)
        
        for match in inline_matches:
            latex_code = match.group(1).strip()
            
            # Skip if it's just a number or simple text
            if len(latex_code) > 2 and any(c in latex_code for c in ['\\', '^', '_', '{', '}']):
                equation = ExtractedEquation(
                    equation_id=str(uuid.uuid4()),
                    latex_code=latex_code,
                    equation_type="inline",
                    confidence=0.85
                )
                equations.append(equation)
        
        logger.info(f"Parsed {len(equations)} equations from markdown")
        return equations
    
    async def _extract_with_fallback(
        self,
        pdf_path: str,
        page_numbers: Optional[List[int]] = None
    ) -> List[ExtractedEquation]:
        """
        Fallback equation extraction using PyMuPDF and OCR
        
        Args:
            pdf_path: Path to PDF file
            page_numbers: Optional list of page numbers
        
        Returns:
            List of ExtractedEquation objects
        """
        try:
            import fitz  # PyMuPDF
            import uuid
            
            equations = []
            
            doc = fitz.open(pdf_path)
            
            pages_to_process = page_numbers if page_numbers else range(len(doc))
            
            for page_num in pages_to_process:
                if isinstance(page_num, int) and page_num > 0:
                    page_num = page_num - 1  # Convert to 0-indexed
                
                if page_num >= len(doc):
                    continue
                
                page = doc[page_num]
                
                # Extract text and look for equation patterns
                text = page.get_text()
                
                # Simple heuristic: look for mathematical symbols
                import re
                
                # Look for LaTeX-like patterns in text
                latex_patterns = [
                    r'\\frac\{[^}]+\}\{[^}]+\}',
                    r'\\sum_\{[^}]+\}',
                    r'\\int_\{[^}]+\}',
                    r'\\alpha|\\beta|\\gamma|\\delta',
                    r'x\^[0-9]+',
                    r'[a-z]_[0-9]+'
                ]
                
                for pattern in latex_patterns:
                    matches = re.finditer(pattern, text)
                    for match in matches:
                        equation = ExtractedEquation(
                            equation_id=str(uuid.uuid4()),
                            latex_code=match.group(0),
                            equation_type="inline",
                            page_number=page_num + 1,
                            confidence=0.5  # Low confidence for fallback
                        )
                        equations.append(equation)
            
            doc.close()
            
            logger.info(f"Fallback extraction found {len(equations)} potential equations")
            return equations
            
        except Exception as e:
            logger.error(f"Error in fallback extraction: {e}")
            return []
    
    async def extract_equation_from_image(
        self,
        image_data: bytes,
        image_format: str = "png"
    ) -> ExtractedEquation:
        """
        Extract equation from image using OCR
        Requirements: 14.1, 14.2
        
        Args:
            image_data: Image bytes
            image_format: Image format (png, jpg, etc.)
        
        Returns:
            ExtractedEquation object
        """
        try:
            import uuid
            import base64
            
            logger.info("Extracting equation from image")
            
            # Save image to temporary file
            with tempfile.NamedTemporaryFile(
                suffix=f'.{image_format}',
                delete=False
            ) as temp_file:
                temp_file.write(image_data)
                temp_path = temp_file.name
            
            try:
                # Use Nougat or fallback OCR
                if self.nougat_available:
                    # Convert image to PDF first
                    pdf_path = await self._image_to_pdf(temp_path)
                    equations = await self._extract_with_nougat(pdf_path, None)
                    
                    if equations:
                        equation = equations[0]
                        equation.original_image = base64.b64encode(image_data).decode()
                        return equation
                
                # Fallback: use simple OCR
                latex_code = await self._ocr_equation_image(temp_path)
                
                equation = ExtractedEquation(
                    equation_id=str(uuid.uuid4()),
                    original_image=base64.b64encode(image_data).decode(),
                    latex_code=latex_code,
                    equation_type="display",
                    confidence=0.6
                )
                
                return equation
                
            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                
        except Exception as e:
            logger.error(f"Error extracting equation from image: {e}")
            raise
    
    async def _image_to_pdf(self, image_path: str) -> str:
        """Convert image to PDF"""
        try:
            import fitz
            
            doc = fitz.open()
            img_doc = fitz.open(image_path)
            
            pdf_bytes = img_doc.convert_to_pdf()
            img_doc.close()
            
            pdf_doc = fitz.open("pdf", pdf_bytes)
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(
                suffix='.pdf',
                delete=False
            ) as temp_file:
                pdf_doc.save(temp_file.name)
                pdf_path = temp_file.name
            
            pdf_doc.close()
            doc.close()
            
            return pdf_path
            
        except Exception as e:
            logger.error(f"Error converting image to PDF: {e}")
            raise
    
    async def _ocr_equation_image(self, image_path: str) -> str:
        """
        OCR equation from image (fallback method)
        
        Args:
            image_path: Path to image file
        
        Returns:
            LaTeX code (best effort)
        """
        try:
            # Try using pytesseract if available
            import pytesseract
            from PIL import Image
            
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img)
            
            # Very basic conversion to LaTeX
            # This is a placeholder - real conversion would be much more complex
            latex_code = text.strip()
            
            logger.info(f"OCR extracted text: {latex_code}")
            return latex_code
            
        except ImportError:
            logger.warning("pytesseract not available for OCR")
            return "\\text{Equation extraction failed}"
        except Exception as e:
            logger.error(f"Error in OCR: {e}")
            return "\\text{Equation extraction failed}"
    
    def convert_to_latex(
        self,
        equation_text: str,
        equation_type: str = "display"
    ) -> str:
        """
        Convert equation text to LaTeX format
        Requirements: 14.2
        
        Args:
            equation_text: Equation text
            equation_type: "inline" or "display"
        
        Returns:
            LaTeX formatted equation
        """
        # Clean up the equation text
        latex_code = equation_text.strip()
        
        # Wrap in appropriate delimiters
        if equation_type == "inline":
            return f"${latex_code}$"
        else:
            return f"$$\n{latex_code}\n$$"
    
    async def verify_equation_round_trip(
        self,
        original_image: bytes,
        latex_code: str
    ) -> Tuple[bool, float]:
        """
        Verify equation round-trip by rendering LaTeX and comparing to original
        Requirements: 14.8
        
        Args:
            original_image: Original equation image bytes
            latex_code: LaTeX code to verify
        
        Returns:
            Tuple of (is_valid, similarity_score)
            is_valid is True if SSIM > 0.9
        """
        try:
            # Render LaTeX to image
            rendered_image = await self._render_latex_to_image(latex_code)
            
            # Compare images using SSIM
            similarity = await self._compare_images_ssim(
                original_image,
                rendered_image
            )
            
            is_valid = similarity > 0.9
            
            logger.info(
                f"Equation round-trip verification: SSIM={similarity:.3f}, "
                f"valid={is_valid}"
            )
            
            return is_valid, similarity
            
        except Exception as e:
            logger.error(f"Error in round-trip verification: {e}")
            return False, 0.0
    
    async def _render_latex_to_image(self, latex_code: str) -> bytes:
        """
        Render LaTeX code to image
        
        Args:
            latex_code: LaTeX code
        
        Returns:
            Image bytes (PNG)
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
            import io
            
            # Create figure
            fig = plt.figure(figsize=(6, 2))
            fig.text(0.5, 0.5, f"${latex_code}$", size=20, ha='center', va='center')
            plt.axis('off')
            
            # Save to bytes
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
            plt.close(fig)
            
            buf.seek(0)
            return buf.read()
            
        except Exception as e:
            logger.error(f"Error rendering LaTeX: {e}")
            raise
    
    async def _compare_images_ssim(
        self,
        image1_bytes: bytes,
        image2_bytes: bytes
    ) -> float:
        """
        Compare two images using SSIM (Structural Similarity Index)
        
        Args:
            image1_bytes: First image bytes
            image2_bytes: Second image bytes
        
        Returns:
            SSIM score (0-1, higher is more similar)
        """
        try:
            from PIL import Image
            import io
            import numpy as np
            
            # Load images
            img1 = Image.open(io.BytesIO(image1_bytes)).convert('L')
            img2 = Image.open(io.BytesIO(image2_bytes)).convert('L')
            
            # Resize to same dimensions
            size = (min(img1.width, img2.width), min(img1.height, img2.height))
            img1 = img1.resize(size)
            img2 = img2.resize(size)
            
            # Convert to numpy arrays
            arr1 = np.array(img1)
            arr2 = np.array(img2)
            
            # Try using skimage SSIM if available
            try:
                from skimage.metrics import structural_similarity as ssim
                score = ssim(arr1, arr2)
                return float(score)
            except ImportError:
                # Fallback: simple MSE-based similarity
                mse = np.mean((arr1 - arr2) ** 2)
                max_pixel = 255.0
                psnr = 20 * np.log10(max_pixel / np.sqrt(mse)) if mse > 0 else 100
                # Convert PSNR to 0-1 scale (rough approximation)
                similarity = min(1.0, psnr / 50.0)
                return float(similarity)
                
        except Exception as e:
            logger.error(f"Error comparing images: {e}")
            return 0.0
