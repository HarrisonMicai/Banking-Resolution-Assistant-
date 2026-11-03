from fastapi import FastAPI
from app.database.base import Base
from app.api.routes import accounts, complaints, customers, health
from app.core.logging_config import configure_logging
from app.database.connection import engine
from app.error_handlers import register_error_handlers
from app.middleware import CorrelationIdMiddleware

Base.metadata.create_all(bind=engine)
configure_logging()
app = FastAPI()
app.add_middleware(CorrelationIdMiddleware)
register_error_handlers(app)
app.include_router(accounts.router)
app.include_router(complaints.router)
app.include_router(customers.router)
app.include_router(health.router)


@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Welcome to the Banking Resolution Assistant API. Visit /docs for API documentation."}