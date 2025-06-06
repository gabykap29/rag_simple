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
Actúa como asistente para profesores de una plataforma de cursos (de cualquier tema).

Tu única tarea:
- Redactar actividades prácticas y breves para principiantes.
- Basarte 100% en el pedido del instructor, sin cambiarlo ni interpretarlo.
- Si "Contexto" está vacío, ignóralo.

Reglas estrictas:
- No expliques, no resumas, no reformules, no agregues texto extra.
- Responde siempre en español, en el formato indicado.
- Si el contexto esta vacio o no es relevante, ignóralo.
- No incluyas ejemplos ni respuestas correctas.

Datos:
Título del curso: {course_title}
Título de la lección: {lesson_title}
Pedido del instructor: {instructor_request}
Contexto: {contexto}
Cantidad de actividades: {amount} (por defecto: 5)

Formato obligatorio: 
"ejercicio1:" "[Texto del ejercicio]"
"ejercicio2": "[Texto del ejercicio]"
"ejercicio3": "[Texto del ejercicio]"
...

Importante:
- Cada ejercicio debe ser breve, práctico y pensado para un principiante.
- No usar opción múltiple ni largos textos teóricos.
- No agregar información adicional ni explicaciones.
- No incluir ejemplos ni respuestas correctas.

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
def text_splitter(documents, course_name=None):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents)
    if course_name:
        for chunk in chunks:
            chunk.page_content = f"Curso: {course_name}\n{chunk.page_content}"
    return chunks


def index_docs(documents):
    vector_store.add_documents(documents)
    vector_store.persist()
    

def retrieve_docs(query, course_name=None):
    docs = vector_store.similarity_search(query, k=10)  # Podés ajustar k
    if course_name:
        docs = [doc for doc in docs if doc.metadata.get("course_name") == course_name]
    return docs


def generate_response_stream(contexto, course_title, lesson_title ,instructor_request, amount):
    prompt = ChatPromptTemplate.from_template(custom_template)
    chain = prompt | model

    response_stream = chain.stream({
        "amount": amount,
        "contexto": contexto,
        "course_title": course_title,   
        "instructor_request": instructor_request,
        "lesson_title": lesson_title,

        

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
name_course = st.text_input("Nombre del curso")

if uploaded_file and name_course:
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
        doc.metadata["course_name"] = name_course

    index_docs(chunked_documents)

course_title = st.text_input("Titulo del curso")
lesson_title = st.text_input("Titulo de la lección")
instructor_request = st.text_area("Ordenes para el asistente")
amount = st.number_input("Cantidad de ejercicios a generar")
    

if course_title != "" and lesson_title != "" and instructor_request != "":
    st.chat_message("user").write(f"Título del curso: {course_title}")
    st.chat_message("user").write(f"Título de la lección: {lesson_title}")
    st.chat_message("user").write(f"Pedido del instructor: {instructor_request}")
    st.chat_message("user").write(f"Cantidad de ejercicios: {amount}")
    st.markdown("---")

    # 2. Recuperar contexto relevante (si existe)
    related_documents = retrieve_docs(lesson_title, course_title)

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
        full_response += chunk  # cada chunk trae parte del texto
        message_placeholder.markdown(full_response)  # vamos actualizando
