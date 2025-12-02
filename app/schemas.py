from decimal import Decimal
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import List, Literal, Optional

#con la libreria BaseModel di Pydantic possiamo creare dei modelli che sono classi che ereditano BaseModel e definiscono
#i campi come attributi e servono per la validazione dei dati

#modello per la creazione dell'utente
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8) #usiamo field per validare la lunghezza min della password
    #se è troppo corta restituisce eccezione 422 automaticamente

#modello per la restituzione dei dati dell'utente 
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    #restituiamo anche il wallet creato e envenutali transazioni se esistono (codice annidato in WalletResponse)
    wallets: List[WalletResponse] = []

    class Config:
        from_attributes = True #per dire a pydantic di non aspettarsi un dizionario ma di leggere i dati dagli attributi dell'oggetto

#modello per il login
class UserLogin(BaseModel):
    email: EmailStr
    password: str

#modello per la restituzione del token di autenticazione dopo il login
class Token(BaseModel):
    access_token: str
    token_type: str

#modello per la verifica del token
class TokenData(BaseModel):
    id: Optional[int] = None


#nessun modello per la creazione di wallet, perchè lo creiamo in automatico alla registrazione dell'utente

#modello per la restituzione del wallet di un utente
class WalletResponse(BaseModel):
    id: int
    owner_id: int
    currency: str
    balance: Decimal
    created_at: datetime

    #restituiamo anche le transazioni associate
    transactions: List[TransactionResponse] = []

    class Config:
        from_attributes = True 

#modelli per deposito e prelievo su wallet
class WalletDeposit(BaseModel):
    deposit: Decimal = Field(gt=0) #greater than 0 --> l'utente deve inserire un numero maggiore di zero

class WalletWithdrawal(BaseModel):
    withdrawal: Decimal = Field(gt=0)

#modello per la creazione di una transazione
class TransactionCreate(BaseModel):
    type: str = Literal["BUY", "SELL"]
    asset: str
    amount: Decimal = Field(gt=0)

#modello per la restituzione di una transazione
class TransactionResponse(BaseModel):
    id: int
    wallet_id: int
    type: str
    asset: str
    amount: Decimal
    price_at_the_moment: Decimal
    total_payed: Decimal
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
