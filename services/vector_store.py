from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from core.config import DB_DIRECTORY, EMBEDG_MODEL

embeddings = OllamaEmbeddings(model= EMBEDG_MODEL)
vector_store = Chroma(persist_directory=DB_DIRECTORY, embedding_function=embeddings)

def text_splitter(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size = 1000,
        chunk_overlap = 100,
        add_start_index = True,
    )
    return splitter.split_documents(documents)

def retrieve_docs(query):
    return vector_store.similarity_search(query)

def is_pdf_already_indexed(file_hash):
    result = vector_store.similarity_search(file_hash, k=1)
    if result:
        for doc in result:
            if doc.metadata.get("file_hash") == file_hash:
                return True
    return False
