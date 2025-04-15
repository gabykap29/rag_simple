import os
from langchain_community.document_loaders import PDFPlumberLoader
from src.corrections.core.config import PDF_DIRECTORY
from src.corrections.vector_store import vector_store, text_splitter, is_pdf_already_indexed
from src.documents.utils.get_hash import get_file_hash


def index_pdf(file, course_name: str):
    os.makedirs(PDF_DIRECTORY, exist_ok=True)

    # Guardar archivo
    file_path = os.path.join(PDF_DIRECTORY, file.filename)
    with open(file_path, "wb") as f:
        f.write(file.file.read())

    # Hash
    file_hash = get_file_hash(file_path)
    if is_pdf_already_indexed(file_hash):
        return {"message": "PDF ya fue indexado", "indexed": False}

    # Cargar contenido y fragmentarlo
    documents = PDFPlumberLoader(file_path).load()
    chunks = text_splitter(documents)

    for chunk in chunks:
        chunk.metadata["file_hash"] = file_hash
        chunk.metadata["course_name"] = course_name

    vector_store.add_documents(chunks)
    vector_store.persist()

    return {"message": "PDF procesado e indexado correctamente", "indexed": True}