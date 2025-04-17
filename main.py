from fastapi import FastAPI
from src.corrections import corrector_controllers
from src.documents import pdf_controllers
from src.assistant_instructor import assistant_instructor_controllers
app = FastAPI()

app.include_router(corrector_controllers.router, prefix="/correction", tags=["Asistente para corrección"])
app.include_router(pdf_controllers.router, prefix="/pdf", tags=["PDF"])
app.include_router(assistant_instructor_controllers.router, prefix="/assistant", tags=["Asistente del Instructor"])