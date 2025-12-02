from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import transactions, users, auth
from .database import engine
from . import models
from fastapi.responses import ORJSONResponse

#definiamo la logica che deve essere eseguita prima dell'avvio dell'applicazione
#questo codice viene eseguito una volta, prima dell'avvio
@asynccontextmanager
async def lifespan(app: FastAPI):
    #istruzioni da eseguire prima che l'app si avvii
    #qui avvio l'engine, e creo le tabelle del database se non esistono già, prima di integrare alembic
    #async with engine.begin() as conn:
    #     await conn.run_sync(models.Base.metadata.create_all)
    yield
    #istruzioni da eseguire dopo l'arresto
    #spegniamo l'engine
    engine.dispose()


app = FastAPI(lifespan= lifespan, default_response_class=ORJSONResponse)

#cors(condivisione delle risorse tra origini)
origins = ["*"]#url che possono fare richieste a questa app

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

#impostiamo i routers
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(transactions.router)

#api home
app.get("/home")
async def home():
    return {"message": "Benvenuto nel Backend Fastapi completamente asincrono"}

