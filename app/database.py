from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from .config import settings

#URL= "postgres://username:password@hostname:port/name"
#aggiungiamo il driver asyncpg per codice asincrono
DB_URL = f'postgresql+asyncpg://{settings.DATABASE_USERNAME}:{settings.DATABASE_PASSWORD
            }@{settings.DATABASE_HOSTNAME}:{settings.DATABASE_PORT}/{settings.DATABASE_NAME}'

#un engine(motore) è ciò che contiene le connessioni al db
engine = create_async_engine(DB_URL, echo=True) #echo serve per stampare tutte le query a terminale

#mentre l'engine è la connessione fisica al db, la session è l'area di lavoro temporanea
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

#declarative_base è una funzione che restituisce una classe base, tutte le tabelle erediteranno da questa classe
Base = declarative_base()

#funzione per dipendency injection
async def get_db():
    async with SessionLocal() as session: #crea una nuova sessione e la apre
        yield session #consegna la sessione alla funzione che la richiede e mette in pausa fino alla chiusura quando la richiesta finisce

