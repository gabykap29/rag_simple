import os

PDF_DIRECTORY = "./pdfs"
DB_DIRECTORY = "./vector_db"
EMBEDG_MODEL = "nomic-embed-text"
LLM_MODEL = "phi4-mini:3.8b-q4_K_M"

os.makedirs(PDF_DIRECTORY, exist_ok = True)
os.makedirs(DB_DIRECTORY, exist_ok= True)