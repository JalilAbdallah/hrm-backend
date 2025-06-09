from fastapi import FastAPI
from config.database import connect_to_mongo, close_mongo_connection
from routers import reports, auth
from middleware.cors import setup_cors
from routers.individuals import router as individuals_router


app = FastAPI(
    title="Human Rights Monitor API",
    description="API for Human Rights Violations Management System",
    version="1.0.0"
)

setup_cors(app)

@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
   await close_mongo_connection()


# Include the routers here guys!
app.include_router(reports.router, prefix="/reports", tags=["reports"])
app.include_router(individuals_router, prefix="/victims", tags=["individuals"])

app.include_router(auth.router, prefix="/auth", tags=["authorization"])

@app.get("/")
async def root():
    return {"message": "Human Rights Monitor API is running"}
