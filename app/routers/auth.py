from fastapi import APIRouter, Depends, HTTPException, status
from .. import utils, models, schemas, oauth2
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..database import get_db
from fastapi.security.oauth2 import OAuth2PasswordRequestForm

router = APIRouter(
    tags = ['Authentication']
)

@router.post("/login", response_model=schemas.Token)
async def login(credenziali: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):

    #facciamo una query per ottenere l'utente in base alla mail inserita, che in OAuth2PasswordRequestForm è chiamato username
    query = select(models.User).where(models.User.email == credenziali.username)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Credenziali errate")
    
    #se la password non è corretta lanciamo un eccezione
    if not utils.verify(credenziali.password, user.password):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Credenziali errate")
    
    #se invece è corretta creo il token e lo restituisco
    access_token = oauth2.crea_token_di_accesso(data= {"user_id": user.id})

    return {"access_token": access_token, "token_type": "bearer"}
