from fastapi import FastAPI
from app.database.base import Base
from app.api.routes import accounts, complaints, customers, health
from app.database.connection import engine

Base.metadata.create_all(bind=engine)
app = FastAPI()
app.include_router(accounts.router)
app.include_router(complaints.router)
app.include_router(customers.router)
app.include_router(health.router)


@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to the Banking Resolution Assistant API. Visit /docs for API documentation."}