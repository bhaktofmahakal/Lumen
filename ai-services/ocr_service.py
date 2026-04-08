"""
OCR Service for image text extraction
Requirements: 4.10
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging
import base64
import io
from PIL import Image
import pytesseract

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ocr", tags=["ocr"])


class OCRRequest(BaseModel):
    image_base64: str
    mime_type: str


class OCRResponse(BaseModel):
    text: str
    confidence: float


@router.post("/extract", response_model=OCRResponse)
async def extract_text_from_image(request: OCRRequest):
    """
    Extract text from image using Tesseract OCR
    Requirements: 4.10
    """
    try:
        # Decode base64 image
        image_data = base64.b64decode(request.image_base64)
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Extract text using Tesseract
        text = pytesseract.image_to_string(image)
        
        # Get confidence data
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        confidences = [int(conf) for conf in data['conf'] if conf != '-1']
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        logger.info(f"OCR extracted {len(text)} characters with {avg_confidence:.2f}% confidence")
        
        return OCRResponse(
            text=text.strip(),
            confidence=avg_confidence / 100.0  # Normalize to 0-1
        )
        
    except Exception as e:
        logger.error(f"OCR extraction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Tesseract availability
        version = pytesseract.get_tesseract_version()
        return {
            'status': 'healthy',
            'service': 'ocr',
            'tesseract_version': str(version)
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'service': 'ocr',
            'error': str(e)
        }
