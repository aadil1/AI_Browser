"""
OCR Scanner Module.
Extract text from images and PDFs, then scan for prompt injection.
"""
import io
import logging
from dataclasses import dataclass
from typing import BinaryIO

logger = logging.getLogger(__name__)

# Optional imports - graceful degradation if not installed
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("Pillow not installed - image scanning disabled")

try:
    import pytesseract
    # Set Tesseract path for Windows (winget installation)
    import os
    tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(tesseract_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.warning("pytesseract not installed - OCR disabled")

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    logger.warning("PyMuPDF not installed - PDF scanning disabled")


@dataclass
class OCRResult:
    """Result of OCR text extraction."""
    success: bool
    text: str
    error: str | None = None
    page_count: int = 1


@dataclass
class DocumentScanResult:
    """Result of scanning a document (image or PDF)."""
    is_safe: bool
    risk_score: float
    extracted_text: str
    reason: str | None = None
    explanations: list[str] | None = None
    policy_violations: list[str] | None = None
    page_count: int = 1


def check_ocr_available() -> tuple[bool, str]:
    """Check if OCR capabilities are available."""
    if not PIL_AVAILABLE:
        return False, "Pillow library not installed"
    if not TESSERACT_AVAILABLE:
        return False, "pytesseract library not installed"
    
    # Check if Tesseract binary is available
    try:
        pytesseract.get_tesseract_version()
        return True, "OCR available"
    except Exception as e:
        return False, f"Tesseract not found: {e}"


def check_pdf_available() -> tuple[bool, str]:
    """Check if PDF capabilities are available."""
    if not PYMUPDF_AVAILABLE:
        return False, "PyMuPDF library not installed"
    return True, "PDF scanning available"


def extract_text_from_image(image_data: bytes) -> OCRResult:
    """
    Extract text from an image using OCR.
    
    Args:
        image_data: Raw image bytes
        
    Returns:
        OCRResult with extracted text or error
    """
    available, error = check_ocr_available()
    if not available:
        return OCRResult(success=False, text="", error=error)
    
    try:
        image = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB if necessary
        if image.mode not in ('L', 'RGB'):
            image = image.convert('RGB')
        
        # Extract text
        text = pytesseract.image_to_string(image)
        
        return OCRResult(success=True, text=text.strip())
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        return OCRResult(success=False, text="", error=str(e))


def extract_text_from_pdf(pdf_data: bytes) -> OCRResult:
    """
    Extract text from a PDF file.
    
    Uses native text extraction first, falls back to OCR if needed.
    
    Args:
        pdf_data: Raw PDF bytes
        
    Returns:
        OCRResult with extracted text or error
    """
    available, error = check_pdf_available()
    if not available:
        return OCRResult(success=False, text="", error=error)
    
    try:
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        all_text = []
        page_count = len(doc)
        
        for page in doc:
            # Try native text extraction first
            text = page.get_text()
            
            if text.strip():
                all_text.append(text)
            else:
                # Fall back to OCR for image-based pages
                ocr_available, _ = check_ocr_available()
                if ocr_available:
                    # Render page to image
                    pix = page.get_pixmap(dpi=150)
                    img_data = pix.tobytes("png")
                    
                    # OCR the image
                    ocr_result = extract_text_from_image(img_data)
                    if ocr_result.success:
                        all_text.append(ocr_result.text)
        
        doc.close()
        
        return OCRResult(
            success=True, 
            text="\n\n".join(all_text),
            page_count=page_count
        )
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return OCRResult(success=False, text="", error=str(e))


def scan_document_text(
    text: str,
    source: str = "document",
    page_count: int = 1,
) -> DocumentScanResult:
    """
    Scan extracted document text for safety issues.
    
    Args:
        text: Extracted text from document
        source: Source identifier for policy evaluation
        page_count: Number of pages in document
        
    Returns:
        DocumentScanResult with safety information
    """
    from app.heuristic_safety import is_page_safe
    from app.policy_engine import get_policy_engine
    
    policy_engine = get_policy_engine()
    all_explanations = []
    policy_violations = []
    
    # Policy check
    policy_result = policy_engine.evaluate(text, source)
    if policy_result.violations:
        policy_violations = policy_result.explanations
        all_explanations.extend(policy_violations)
    
    # Safety check
    try:
        is_safe, risk = is_page_safe(text)
    except Exception as e:
        return DocumentScanResult(
            is_safe=False,
            risk_score=1.0,
            extracted_text=text[:500],  # Truncate for response
            reason="Safety check failed",
            explanations=["Safety system error (fail-closed)"],
            page_count=page_count,
        )
    
    # Combine risks
    combined_risk = max(risk, policy_result.risk_score)
    final_is_safe = is_safe and policy_result.allowed
    
    if not is_safe:
        all_explanations.append("Document text matched prompt injection patterns")
    
    return DocumentScanResult(
        is_safe=final_is_safe,
        risk_score=round(combined_risk, 3),
        extracted_text=text[:1000] if len(text) > 1000 else text,  # Truncate
        reason=None if final_is_safe else "Document content flagged",
        explanations=all_explanations if all_explanations else None,
        policy_violations=policy_violations if policy_violations else None,
        page_count=page_count,
    )


def scan_image(image_data: bytes, source: str = "image") -> DocumentScanResult:
    """
    Scan an image for prompt injection via OCR.
    
    Args:
        image_data: Raw image bytes
        source: Source identifier
        
    Returns:
        DocumentScanResult with safety information
    """
    ocr_result = extract_text_from_image(image_data)
    
    if not ocr_result.success:
        return DocumentScanResult(
            is_safe=False,
            risk_score=1.0,
            extracted_text="",
            reason=f"OCR failed: {ocr_result.error}",
            explanations=["Could not extract text from image"],
        )
    
    if not ocr_result.text:
        # No text found - image is safe
        return DocumentScanResult(
            is_safe=True,
            risk_score=0.0,
            extracted_text="",
            reason=None,
        )
    
    return scan_document_text(ocr_result.text, source)


def scan_pdf(pdf_data: bytes, source: str = "pdf") -> DocumentScanResult:
    """
    Scan a PDF for prompt injection.
    
    Args:
        pdf_data: Raw PDF bytes
        source: Source identifier
        
    Returns:
        DocumentScanResult with safety information
    """
    ocr_result = extract_text_from_pdf(pdf_data)
    
    if not ocr_result.success:
        return DocumentScanResult(
            is_safe=False,
            risk_score=1.0,
            extracted_text="",
            reason=f"PDF extraction failed: {ocr_result.error}",
            explanations=["Could not extract text from PDF"],
        )
    
    if not ocr_result.text:
        # No text found - PDF is safe
        return DocumentScanResult(
            is_safe=True,
            risk_score=0.0,
            extracted_text="",
            reason=None,
            page_count=ocr_result.page_count,
        )
    
    return scan_document_text(
        ocr_result.text, 
        source, 
        page_count=ocr_result.page_count
    )
