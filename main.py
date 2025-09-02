from fastapi import FastAPI
from app.Utils.database import engine, Base
from app.Walletapp.routes import router
app = FastAPI()

@app.get("/")
async def read_root():
    return {"Grettings": "Welcome to The Wallet app api"}


Base.metadata.create_all(bind=engine)


app.include_router(router, prefix="/api/wallet", tags=["Wallet Operations"])