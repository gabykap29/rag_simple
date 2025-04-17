from src.assistant_instructor.core.prompt import custom_template
from langchain_core.prompts import ChatPromptTemplate
from src.assistant_instructor.core.config import LLM_MODEL
from langchain_ollama.llms import OllamaLLM

model = OllamaLLM(model=LLM_MODEL, temperature=0.4, max_tokens= 2000, stream = True)


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