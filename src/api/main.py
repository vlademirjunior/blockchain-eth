from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv
from src.api.endpoints import transactions
from src.infra.database.config import engine
from src.infra.database import models as db_models
from src.api.dependencies import _get_initialized_nonce_manager, get_address_repository, get_blockchain_service, get_db

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for the API.
    This is the new, recommended way to manage startup and shutdown events.
    """
    print("API starting up...")

    # Initialize Database Tables
    async with engine.begin() as conn:
        # This will run the synchronous create_all method in an async-safe way.
        # TODO: Alembic for production migrations
        await conn.run_sync(db_models.Base.metadata.create_all)
    print("Database tables initialized.")

    try:
        async for db_session in get_db():  # This gets an async session
            temp_address_repo = get_address_repository(db_session)
            temp_blockchain_service = get_blockchain_service()

            async for _ in _get_initialized_nonce_manager(
                address_repo=temp_address_repo,
                blockchain_service=temp_blockchain_service
            ):
                pass
            break

    except Exception as e:
        print(f"Error during NonceManager initialization: {e}")
        # Depending on error handling strategy, I might want to raise here
        # to prevent the API from starting if this critical component fails.
        raise

    yield  # The API runs here

    # Shutdown event: Perform cleanup tasks here
    print("API shutting down...")
    # Add any cleanup for nonce_manager_instance if necessary (e.g., persistence)


app = FastAPI(
    title="Ethereum Interaction API",
    description="A secure API to interact with the Ethereum blockchain.",
    version="1.0.0",
    lifespan=lifespan
)


# Include routers
app.include_router(transactions.router)


@app.get("/")
async def read_main():
    return {"msg": "Ethereum Interaction API"}
