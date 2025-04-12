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
Actúa como un asistente para profesores de una plataforma de cursos en español.

Tarea:
- Generar actividades sobre un tema dado.
- Las actividades deben ser de dificultad sencilla, pensadas para principiantes.

Instrucciones específicas:
- Responde siempre en español, de forma breve, clara y precisa.
- No agregues saludos, comentarios personales ni introducciones o conclusiones.
- Si el "Contexto" está vacío, ignóralo y genera las actividades basándote solo en el Título del curso, titulo de la lección y el Pedido del instructor.

Contenido proporcionado:
Título del curso: {course_title}
Titulo de la lección: {lesson_title}
Pedido del instructor: {instructor_request}
Contexto: {contexto}
Cantidad de actividades solicitadas: {amount} (por defecto: 5)

Formato de respuesta (obligatorio):
Ejercicio1: [Contenido del ejercicio 1]
Ejercicio2: [Contenido del ejercicio 2]
Ejercicio3: [Contenido del ejercicio 3]
...
(Ejercicios según la cantidad solicitada)

Importante:
- No agregues texto fuera del formato pedido.
- Cada ejercicio debe ser una consigna breve, enfocada en que el estudiante practique el tema.
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

def generate_response_stream(contexto, course_title, lesson_title ,instructor_request, amount):
    context = "\n\n".join(contexto)
    prompt = ChatPromptTemplate.from_template(custom_template)
    chain = prompt | model

    response_stream = chain.stream({
        "course_title": course_title,   
        "lesson_title": lesson_title,
        "instructor_request": instructor_request,
        "amount": amount,
        "contexto": context,
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

course_title = st.text_input("Titulo del curso")
lesson_title = st.text_input("Titulo de la lección")
instructor_request = st.text_area("Ordenes para el asistente")
amount = st.number_input("Cantidad de ejercicios a generar")
    

if course_title and lesson_title and instructor_request:
    st.chat_message("user").write(f"Título del curso: {course_title}")
    st.chat_message("user").write(f"Título de la lección: {lesson_title}")
    st.chat_message("user").write(f"Pedido del instructor: {instructor_request}")
    st.chat_message("user").write(f"Cantidad de ejercicios: {amount}")
    st.markdown("---")

    # 2. Recuperar contexto relevante (si existe)
    related_documents = retrieve_docs(lesson_title)
    # Extraer el texto de cada Document
    contexto = "\n".join(doc.page_content for doc in related_documents) if related_documents else ""
    # 3. Armar el prompt rellenando el template
    prompt = custom_template.format(
        course_title=course_title,
        lesson_title= lesson_title,
        instructor_request=instructor_request,
        contexto=contexto,
        amount=int(amount)
    )

    # 4. Generar respuesta
    message_placeholder = st.chat_message("assistant").empty()
    full_response = ""

    for chunk in generate_response_stream(contexto, course_title, lesson_title ,instructor_request, amount):
        full_response += chunk
        message_placeholder.markdown(full_response)
