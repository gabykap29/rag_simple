from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from src.assistant_instructor.core.config import DB_DIRECTORY, EMBEDG_MODEL


embeddings = OllamaEmbeddings(model=EMBEDG_MODEL)
vector_store = Chroma(persist_directory=DB_DIRECTORY, embedding_function=embeddings)


def text_splitter(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        add_start_index=True,
    )
    return splitter.split_documents(documents)

def retrieve_docs(query, course_name=None):
    docs = vector_store.similarity_search(query, k=10) 
    if course_name:
        docs = [doc for doc in docs if doc.metadata.get("course_name") == course_name]
    return docs

def is_pdf_already_indexed(file_hash):
    result = vector_store.similarity_search(file_hash, k=1)
    return any(doc.metadata.get("file_hash") == file_hash for doc in result)