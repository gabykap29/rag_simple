from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from src.documents.pdf_services import index_pdf

router = APIRouter()

@router.post(
    "/upload-pdf",
    summary="Subir e indexar un PDF",
    description="""
Sube un archivo PDF y lo indexa para permitir búsquedas semánticas posteriores.  
También asocia el archivo a un curso mediante el nombre proporcionado.
""",
    response_description="Resultado de la indexación del PDF"
)
async def upload_pdf(
    file: UploadFile = File(..., description="Archivo PDF del curso a indexar."),
    course_name: str = Form(..., description="Nombre del curso al que pertenece el PDF.")
):
    """
    Endpoint para subir un archivo PDF y asociarlo a un curso.  
    Internamente genera el hash, fragmenta el contenido y lo guarda en la base vectorial.
    """
    result = index_pdf(file, course_name)
    return JSONResponse(content=result)
