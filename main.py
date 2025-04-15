from fastapi import FastAPI
from src.corrections import corrector_controllers
from src.documents import pdf_controllers

app = FastAPI()

app.include_router(corrector_controllers.router, prefix="/api")
app.include_router(pdf_controllers.router, prefix="/pdf", tags=["PDF"])