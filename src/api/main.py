from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv
from src.api.endpoints import transactions, addresses
from src.infra.database.config import engine
from src.infra.database.config import Base
from src.core.constants import API_VERSION, API_PREFIX

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan manager for the API.
    Handles startup and shutdown events.
    """
    print("API is starting up...")

    # Use Alembic for production
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Database tables created.")

    yield  # The API runs here

    # Code to run on shutdown
    print("API is shutting down...")


app = FastAPI(
    title="Ethereum Interaction API",
    description="A secure API to interact with the Ethereum blockchain.",
    version=API_VERSION,
    lifespan=lifespan
)


# Include the API routers
app.include_router(
    transactions.router,
    prefix=f"{API_PREFIX}/transactions",
    tags=["Transactions"]
)
app.include_router(
    addresses.router,
    prefix=f"{API_PREFIX}/addresses",
    tags=["Addresses"]
)


@app.get(
    "/",
    summary="Root endpoint for health checks",
    description="Check if the Blockchain Ethereum API is healthy."
)
async def health_checks():
    return {"healthy": True}
