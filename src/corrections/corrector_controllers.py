from typing import AsyncGenerator
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from src.corrections.vector_store import retrieve_docs
from src.corrections.models.schemas import CorrectionRequest, CorrectionResponse
from src.corrections.correction_services import generate_response_stream

router = APIRouter()

@router.get(
    "/",
    summary="Verificar estado del servidor",
    description="Endpoint simple para verificar que el servidor está corriendo."
)
def server_on():
    return {"message": "server on"}

@router.post(
    "/correct",
    response_model=CorrectionResponse,
    summary="Corregir ejercicio del estudiante",
    description="""
Corrige una respuesta del estudiante basándose en el contexto obtenido desde los documentos PDF previamente indexados.  
La corrección se realiza con una IA y se transmite en tiempo real como texto.
""",
    responses={
        200: {
            "content": {"text/plain": {}},
            "description": "Respuesta de corrección generada en tiempo real (streaming)."
        }
    }
)
async def correct_exercise(request: CorrectionRequest):
    """
    Corrige una respuesta dada por el usuario basándose en un enunciado (ejercicio) y el contenido de los documentos relacionados.

    Se realiza una búsqueda semántica con el enunciado, y se genera una respuesta evaluativa para el texto del usuario.
    """
    related_docs = retrieve_docs(request.exercise)

    async def response_generator() -> AsyncGenerator[str, None]:
        for chunk in generate_response_stream(request.exercise, related_docs, request.response_user):
            yield chunk

    return StreamingResponse(response_generator(), media_type="text/plain")
