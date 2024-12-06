from fastapi import FastAPI
from app.routes import pdf

app = FastAPI(title="GeminiAIApp")

# Register routes
app.include_router(pdf.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the GeminiAIApp"}
