from pydantic import BaseModel

class CorrectionRequest(BaseModel):
    exercise: str
    response_user: str


class CorrectionResponse(BaseModel):
    full_response: str