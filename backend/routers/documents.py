"""Document upload and parsing endpoints."""
import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from database.session import get_db
from database.models import Document, Company
from services.document_parser import parse_document
from services.gemini_service import extract_structured_data
from config import UPLOAD_DIR, MAX_FILE_SIZE, ALLOWED_EXTENSIONS

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload/{company_id}")
async def upload_document(
    company_id: int,
    doc_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a document for a company, parse it, and extract structured data."""
    # Verify company exists
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Validate file extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type {ext} not allowed. Accepted: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Save file
    company_dir = os.path.join(UPLOAD_DIR, str(company_id))
    os.makedirs(company_dir, exist_ok=True)
    file_path = os.path.join(company_dir, file.filename)

    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(status_code=400, detail="File too large (max 50MB)")
            f.write(content)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Create document record
    doc = Document(
        company_id=company_id,
        filename=file.filename,
        file_path=file_path,
        doc_type=doc_type,
        file_size=len(content),
        upload_status="parsing"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Parse document
    try:
        extracted_text = parse_document(file_path)
        doc.extracted_text = extracted_text
        doc.upload_status = "parsed"
        db.commit()
    except Exception as e:
        doc.upload_status = "error"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to parse document: {str(e)}")

    # Update company status
    if company.status == "draft":
        company.status = "in_progress"
        db.commit()

    return {
        "id": doc.id,
        "filename": doc.filename,
        "doc_type": doc.doc_type,
        "file_size": doc.file_size,
        "upload_status": doc.upload_status,
        "text_length": len(extracted_text) if extracted_text else 0,
        "uploaded_at": doc.uploaded_at.isoformat()
    }


@router.post("/extract/{document_id}")
async def extract_data(document_id: int, db: Session = Depends(get_db)):
    """Run AI-based structured data extraction on a parsed document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if not doc.extracted_text:
        raise HTTPException(status_code=400, detail="Document has not been parsed yet")

    try:
        parsed_data = await extract_structured_data(doc.extracted_text, doc.doc_type)
        doc.parsed_data = parsed_data
        db.commit()
        return {
            "id": doc.id,
            "filename": doc.filename,
            "doc_type": doc.doc_type,
            "parsed_data": parsed_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@router.get("/company/{company_id}")
def list_documents(company_id: int, db: Session = Depends(get_db)):
    """List all documents for a company."""
    documents = db.query(Document).filter(
        Document.company_id == company_id
    ).order_by(Document.uploaded_at.desc()).all()

    return [{
        "id": doc.id,
        "filename": doc.filename,
        "doc_type": doc.doc_type,
        "file_size": doc.file_size,
        "upload_status": doc.upload_status,
        "has_extracted_text": bool(doc.extracted_text),
        "has_parsed_data": bool(doc.parsed_data),
        "uploaded_at": doc.uploaded_at.isoformat()
    } for doc in documents]


@router.get("/{document_id}")
def get_document(document_id: int, db: Session = Depends(get_db)):
    """Get a document's details including extracted data."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "id": doc.id,
        "company_id": doc.company_id,
        "filename": doc.filename,
        "doc_type": doc.doc_type,
        "file_size": doc.file_size,
        "upload_status": doc.upload_status,
        "extracted_text": doc.extracted_text[:5000] if doc.extracted_text else None,
        "full_text_length": len(doc.extracted_text) if doc.extracted_text else 0,
        "parsed_data": doc.parsed_data,
        "uploaded_at": doc.uploaded_at.isoformat()
    }


@router.delete("/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    """Delete a document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete file from disk
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    db.delete(doc)
    db.commit()
    return {"message": "Document deleted"}
