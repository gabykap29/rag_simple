from typing import AsyncGenerator
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from services.vector_store import retrieve_docs
from models.schemas import CorrectionRequest, CorrectionResponse
from services.correction_engine import generate_response_stream


router = APIRouter()

@router.get("/")
def server_on():
    return {"message": "server on"}

@router.post("/correct", response_model=CorrectionResponse,
    responses={
        200: {
            "content": {"text/plain": {}},
            "description": "Streaming text response with the correction.",
        }
    })
async def correct_exercise(request: CorrectionRequest):
    related_docs= retrieve_docs(request.exercise)

    async def response_generator() -> AsyncGenerator[str, None]:
        for chunk in generate_response_stream(request.exercise, related_docs, request.response_user):
            yield chunk

    return StreamingResponse(response_generator(), media_type="text/plain")