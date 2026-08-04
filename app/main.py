from fastapi import FastAPI
from app.api.item_router import router as item_router
from app.api.metadata_router import router as metadata_router

app = FastAPI(
    title="My FastAPI Backend",
    description="A basic FastAPI backend setup with Modular Architecture and Metadata Integrations",
    version="1.0.0"
)

# Registramos los controladores
app.include_router(item_router)
app.include_router(metadata_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Modular FastAPI Backend"}
