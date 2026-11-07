from io import BytesIO

from django.core.files.storage import default_storage
from docx import Document
from pypdf import PdfReader


MAX_CV_TEXT_CHARS = 30000


def extract_revision_text(revision) -> str:
    if not revision.cv_file_path:
        return ""
    with default_storage.open(revision.cv_file_path, "rb") as cv_file:
        content = cv_file.read()
    if revision.cv_file_path.lower().endswith(".pdf"):
        text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(content)).pages)
    elif revision.cv_file_path.lower().endswith(".docx"):
        document = Document(BytesIO(content))
        text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    else:
        raise ValueError("El formato del CV no es compatible.")
    return text.strip()[:MAX_CV_TEXT_CHARS]
