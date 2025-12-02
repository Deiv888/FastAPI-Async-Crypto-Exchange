from fastapi import APIRouter, status, HTTPException, Depends
from .. import schemas, models, utils, oauth2
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..database import get_db


router = APIRouter(
    tags = ['Users']
)

#endpoint per la creazione di un utente
@router.post("/user", status_code=status.HTTP_201_CREATED, response_model=schemas.UserResponse)
async def create_user(nuovo_utente: schemas.UserCreate, db: AsyncSession = Depends(get_db)):

    #controlliamo innanzitutto che la mail non sia già presente nel db con una richiesta asincrona, in modo che mentre viene 
    #processata restituiamo il controllo all'event loop 
    query = select(models.User).where(models.User.email == nuovo_utente.email)
    result = await db.execute(query)
    utente_esiste = result.scalar_one_or_none()
    if utente_esiste:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Esiste già un utente con questa mail: {nuovo_utente.email}")
    
    #hashiamo la password inserita dall'utente e la salviamo al posto di quella inserita
    hashed_password = utils.hash(nuovo_utente.password)
    nuovo_utente.password = hashed_password

    #aggiungiamo il nuovo utente al database
    new_user = models.User(**nuovo_utente.model_dump())

    #creiamo anche un wallet per l'utente
    new_wallet = models.Wallet(
                    currency = "EUR",
                    balance = 0,
                    )
    #aggiungiamo al utente il suo wallet, sqlalchemy capisce automaticamente che deve inserire l'id in owner_id
    new_user.wallets.append(new_wallet)

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user

#endpoint per permettere all'utente di aver accesso alle sue informazioni dell'account (dopo login)
@router.get("/user", response_model=schemas.UserResponse)
async def get_user_info(db: AsyncSession = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):

    #query per prendere le sue info
    query = select(models.User).where(models.User.id == current_user.id)
    result = await db.execute(query)
    utente = result.scalar_one_or_none()
    if not utente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Errore nella richiesta, non è stato possibile recuperare l'utente con id: {current_user.id}")
    return utente