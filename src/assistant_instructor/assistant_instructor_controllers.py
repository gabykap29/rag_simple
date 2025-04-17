from typing import AsyncGenerator
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from src.assistant_instructor.vector_store import retrieve_docs
from src.assistant_instructor.models.schemas import AssistantRequest, AssistantResponse
from src.assistant_instructor.assistant_instructor_services import generate_response_stream

router = APIRouter()


@router.post(
    "/correct",
    response_model=AssistantResponse,
    summary="Generar ejercicios para el instructor",
    description="""
Genera ejercicios basados en el titulo del curso, titulo de la lección y el pedido del instructor.
""",
    responses={
        200: {
            "content": {"text/plain": {}},
            "description": "Respuesta generada en tiempo real (streaming)."
        }
    }
)
async def request_assitant(request: AssistantRequest):
    """
    Envia una petición al asistente de IA para generar ejercicios
    teniendo en cuenta: El titulo de curso, el titulo del ejericio,
    cantidad de actividades solicitadas y el pedido especifico del instructor

    Args:
        request (AssistantRequest): _description_
    """
    related_docs = retrieve_docs(request.instructor_request ,request.course_title)
    
    async def response_generator() -> AsyncGenerator[str, None]:
        for chunk in generate_response_stream(related_docs, request.course_title, request.lesson_title, request.instructor_request, request.amount):
            yield chunk
            
    return StreamingResponse(response_generator(), media_type="text/plain")