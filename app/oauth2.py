from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from . import schemas, models, database
from .config import settings

#definiamo lo schema di autenticazione indicando qual'è l'url del login
schema_oauth2 = OAuth2PasswordBearer(tokenUrl='login')

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

#funzione per la creazione di un token di accesso (sincrona perchè è CPU-BOUND, non I/O)
#passiamo in ingresso un dizionario di dati
def crea_token_di_accesso(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
    #aggiungiamo la scadenza al dizionario
    to_encode.update({"exp": expire})
    # Per generare il token servono: i Dati (Payload con ID e scadenza) e la Firma (fatta con Secret Key e Algoritmo)
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Funzione che PRIMA verifica l'integrità del token (Firma valida? Non scaduto?) 
# e SOLO SE valido spacchetta il payload per ottenere l'ID.
def verifica_token_di_accesso(token: str, credentials_exceptions):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        id: str = payload.get("user_id")

        if not id:
            raise credentials_exceptions
        
        #creiamo un oggetto TokenData per restituire l'id del token
        token_data = schemas.TokenData(id=id)
    except JWTError:
        raise credentials_exceptions
    
    return token_data

#funzione asincrona per ottenere l'utente corrente tramite il token estratto usando lo schema oauth2
async def get_current_user(token: str = Depends(schema_oauth2), db: AsyncSession = Depends(database.get_db)):

    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                          detail="Credenziali non valide",
                                          headers={"WWW-Authenticate": "Bearer"})
    
    token_data = verifica_token_di_accesso(token, credentials_exception)

    #facciamo una query per ottenere l'utente tramite l'id che abbiamo ottenuto
    query = select(models.User).where(models.User.id == token_data.id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise credentials_exception
    return user 
