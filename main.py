from ollama import embeddings
import streamlit as st
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM
from langchain_community.vectorstores import Chroma
import os
import hashlib

custom_template = """
Actúa como un corrector experto de ejercicios de cursos en idioma español.

Tarea:
- Corrige el ejercicio proporcionado utilizando únicamente el contexto entregado.
- Si el contexto no contiene suficiente información para corregir adecuadamente, responde indicando que no es posible corregirlo por falta de información.
- No inventes información adicional que no esté en el contexto.

Instrucciones específicas:
- Siempre responde en español, de forma breve, clara y precisa.
- No agregues comentarios personales ni introducciones innecesarias.
- Si el ejercicio es correcto según el contexto, indícalo explícitamente.
- Si el ejercicio contiene errores (que no sean de gramatica), señala los errores y proporciona la corrección adecuada.

Contenido (formato markdown):
Ejercicio: {ejercicio} (salto de línea)
Respuesta del estudiante: {response_student} (salto de línea)
Contexto: {contexto}

Respuesta esperada:
- Calificacion: [Correcto/Incorrecto]
- Corrección: [Breve corrección del ejercicio (solo si es incorrecto)]
- Comentarios: [Comentarios adicionales sobre el ejercicio, si es necesario]
- Respuesta correcta: [Respuesta correcta al ejercicio, si es necesario]
"""


pdfs_directory = "./pdfs"
db_directory = "./vector_db"
if not os.path.exists(db_directory):
    os.makedirs(db_directory)
if not os.path.exists(pdfs_directory):
    os.makedirs(pdfs_directory)

#La libreria de ollama, provee un modelo de embeddings para generar embeddings de texto
# y un modelo de LLM para generar respuestas a preguntas.
embeddings = OllamaEmbeddings(model="nomic-embed-text")
vector_store = Chroma(persist_directory=db_directory, embedding_function=embeddings)
model = OllamaLLM(model="phi4-mini:3.8b-q4_K_M", temperature=0.4, max_tokens=2000, stream = True)

# Cargar el PDF y dividirlo en fragmentos
def upload_pdf(file):
    with open(pdfs_directory + file.name, "wb") as f:
        f.write(file.getbuffer())

def load_pdf(file_path):
    loader = PDFPlumberLoader(file_path)
    documents = loader.load()
    return documents
def text_splitter(documents):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        add_start_index=True,
    )
    return text_splitter.split_documents(documents)

def index_docs(documents):
    vector_store.add_documents(documents)
    vector_store.persist()
    

def retrieve_docs(query):
    docs = vector_store.similarity_search(query)
    return docs

def generate_response_stream(exercise, context, response_user):
    context = "\n\n".join([doc.page_content for doc in context])
    prompt = ChatPromptTemplate.from_template(custom_template)
    chain = prompt | model

    response_stream = chain.stream({
        "response_student": response_user,
        "ejercicio": exercise,
        "contexto": context
    })

    return response_stream


def get_file_hash(file_path):
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def is_pdf_already_indexed(file_hash):
    result = vector_store.similarity_search(file_hash, k=1)
    if result:
        for doc in result:
            if doc.metadata.get("file_hash") == file_hash:
                return True
    return False

uploaded_file = st.file_uploader("Sube un PDF", type="pdf", accept_multiple_files=False)

if uploaded_file:
    upload_pdf(uploaded_file)
    documents = load_pdf(pdfs_directory + uploaded_file.name)

    file_hash = get_file_hash(pdfs_directory + uploaded_file.name)
    if is_pdf_already_indexed(file_hash):
        st.warning("Este PDF ya ha sido indexado.")
    else:
        st.success("PDF subido y procesado correctamente.")
        


    chunked_documents = text_splitter(documents)
    for doc in chunked_documents:
        doc.metadata["file_hash"] = file_hash

    index_docs(chunked_documents)

exercice = st.text_area("Ejercicio")
response_user = st.text_area("Ejercicio a corregir")
    
if exercice and response_user:
        st.chat_message("user").write(exercice)
        st.chat_message("user").write(response_user)
        st.markdown("---")
        related_documents = retrieve_docs(exercice)

        message_placeholder = st.chat_message("assistant").empty()

        full_response = ""

        for chunk in generate_response_stream(exercice, related_documents, response_user):
            full_response += chunk  # cada chunk trae parte del texto
            message_placeholder.markdown(full_response)  # vamos actualizando
