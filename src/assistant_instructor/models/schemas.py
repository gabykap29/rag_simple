from pydantic import BaseModel

class AssistantRequest(BaseModel):
    course_title: str
    lesson_title: str
    instructor_request: str
    amount: str


class AssistantResponse(BaseModel):
    full_response: str