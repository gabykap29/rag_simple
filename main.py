from fastapi import FastAPI
from controllers import corrector_controllers

app = FastAPI()

app.include_router(corrector_controllers.router, prefix="/api")