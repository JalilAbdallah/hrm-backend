from fastapi import FastAPI
from app.config.database import connect_to_mongo, close_mongo_connection
from app.routers import reports
from app.middleware.cors import setup_cors


app = FastAPI(
    title="Human Rights Monitor API",
    description="API for Human Rights Violations Management System",
    version="1.0.0"
)

setup_cors(app)

@app.on_event("startup")
async def startup_db_client():
    connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    close_mongo_connection()


# Include the routers here guys!


@app.get("/")
async def root():
    return {"message": "Human Rights Monitor API is running"}
