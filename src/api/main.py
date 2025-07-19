from fastapi import FastAPI
from dotenv import load_dotenv
from src.api.endpoints import transactions

load_dotenv()

app = FastAPI()

app.include_router(transactions.router,
                   prefix="/transactions", tags=["transactions"])


@app.get("/")
async def read_main():
    return {"msg": "Blockchain Ethereum API"}
