"""
PDF text extraction from all files in the docs/ directory.
Uses PyPDF2 to read each PDF and return structured data.
"""
import os
from PyPDF2 import PdfReader


def ingest_pdfs(docs_dir: str) -> list[dict]:
    """
    Extract text from all PDFs in the given directory.
    
    Args:
        docs_dir: Path to directory containing PDF files.
    
    Returns:
        List of dicts with keys: filename, text
    """
    documents = []
    
    if not os.path.isdir(docs_dir):
        raise FileNotFoundError(f"Docs directory not found: {docs_dir}")
    
    pdf_files = sorted([f for f in os.listdir(docs_dir) if f.lower().endswith(".pdf")])
    
    if not pdf_files:
        raise ValueError(f"No PDF files found in {docs_dir}")
    
    for filename in pdf_files:
        filepath = os.path.join(docs_dir, filename)
        try:
            reader = PdfReader(filepath)
            text_parts = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            
            full_text = "\n\n".join(text_parts)
            
            if full_text.strip():
                documents.append({
                    "filename": filename,
                    "text": full_text.strip()
                })
                print(f"  ✓ Ingested {filename} ({len(reader.pages)} pages, {len(full_text)} chars)")
            else:
                print(f"  ⚠ Skipped {filename} (no extractable text)")
        except Exception as e:
            print(f"  ✗ Error reading {filename}: {e}")
    
    print(f"  Total: {len(documents)} documents ingested")
    return documents
