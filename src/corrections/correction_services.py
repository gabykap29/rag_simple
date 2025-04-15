from src.corrections.core.prompts import custom_template
from langchain_core.prompts import ChatPromptTemplate
from src.corrections.core.config import LLM_MODEL
from langchain_ollama.llms import OllamaLLM

model = OllamaLLM(model=LLM_MODEL, temperature=0.4, max_tokens= 2000, stream = True)

def generate_response_stream(exercise, context, response_user):
    context = "\n\n".join([doc.page_content for doc in context])
    prompt = ChatPromptTemplate.from_template(custom_template)
    chain = prompt | model

    response_stream = chain.stream({
        "response_student": response_user,
        "ejercicio": exercise,
        "contexto": context
    })

    return response_stream
