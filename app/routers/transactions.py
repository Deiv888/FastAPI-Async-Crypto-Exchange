from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import case, func
from .. import models, schemas, oauth2, utils
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..database import get_db

router = APIRouter(
    tags = ['Transactions']
)

#endpoint per il deposito sul wallet dell'utente
@router.post("/deposit", status_code=status.HTTP_202_ACCEPTED, response_model=schemas.TransactionResponse)
async def deposit(deposito: schemas.WalletDeposit, db: AsyncSession = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    
    #recuperiamo il wallet dell'utente
    query = select(models.Wallet).where(models.Wallet.owner_id == current_user.id).with_for_update()
    result = await db.execute(query)
    wallet = result.scalar_one_or_none()
    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Errore: wallet dell'utente: {current_user.email} non trovato")
    #se abbiamo il wallet facciamo il deposito
    #il controllo del deposito maggiore di zero viene già effettuato dal nostro schema Pydantic
    wallet.balance += deposito.deposit

    #creiamo la transazione
    transazione = models.Transaction(
        wallet_id = wallet.id,
        type = "DEPOSIT",
        asset = wallet.currency,
        amount = deposito.deposit,
        price_at_the_moment = "1",
        total_payed = deposito.deposit,
        status = "COMPLETED",
    )
    wallet.transactions.append(transazione)
    await db.commit()
    await db.refresh(transazione)
    return transazione

#endpoint per il prelievo di un utente
@router.post("/withdrawal", status_code=status.HTTP_202_ACCEPTED, response_model=schemas.TransactionResponse)
async def withdrawal(prelievo: schemas.WalletWithdrawal, db: AsyncSession = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    #recuperiamo il wallet dell'utente
    query = select(models.Wallet).where(models.Wallet.owner_id == current_user.id).with_for_update()
    result = await db.execute(query)
    wallet = result.scalar_one_or_none()
    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Non è stato possibile recuperare il wallet di: {current_user.email}")
    #facciamo il prelievo solo se ha abbastanza soldi sul conto
    #il controllo che sia maggiore di zero lo fa gia il nostro schema pydantic
    if wallet.balance >= prelievo.withdrawal:
        wallet.balance -= prelievo.withdrawal
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Stai cercando di prelevare un import maggiore di quello disponibile")
    #creiamo la transazione
    transaction = models.Transaction(
        wallet_id = wallet.id,
        type = "WITHDRAWAL",
        asset = wallet.currency,
        amount = prelievo.withdrawal,
        price_at_the_moment = "1",
        total_payed = prelievo.withdrawal,
        status = "COMPLETED",
        )
    #aggiungiamo la transazione al wallet
    wallet.transactions.append(transaction)
    await db.commit()
    await db.refresh(transaction)
    return transaction

#endpoint per le transazioni buy o sell
@router.post("/trade", status_code=status.HTTP_202_ACCEPTED, response_model=schemas.TransactionResponse)
async def trade(trade: schemas.TransactionCreate, db: AsyncSession = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):

    #recupero il wallet utente
    query = select(models.Wallet).where(models.Wallet.owner_id == current_user.id).with_for_update()
    result = await db.execute(query)
    wallet = result.scalar_one_or_none()
    if not wallet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Impossibile trovare il wallet associato al tuo account, contatta l'assistenza")
    
    #trovato il wallet prendiamo il prezzo, lui ci fornisce solo type, asset e amount(con controllo > 0 già fatto da Pydantic)
    prezzo = await utils.get_real_price(trade.asset)
    totale_da_pagare = trade.amount * prezzo

    #controllo che abbia abbastanza saldo disponibile sul wallet se è un'acquisto
    if trade.type == "BUY":
        if totale_da_pagare > wallet.balance:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=f"Hai un saldo troppo basso: {wallet.balance}")
        else:
            wallet.balance -= totale_da_pagare
    
    #se è una vendita controlliamo se ci sono transazioni passate di aquisto e le sommiamo
    #prendiamo transazioni collegate al wallet, dove l'asset è lo stesso che desidera vendere, e sottraiamo la somma di tutti i buy con tutti i sell
    elif trade.type == "SELL":
        # Query SQL ottimizzata che fa la somma matematica direttamente nel DB
        query = select(
            func.sum(
                case(
                    (models.Transaction.type == "BUY", models.Transaction.amount), # Se è BUY, aggiungi amount
                    (models.Transaction.type == "SELL", -models.Transaction.amount), # Se è SELL, sottrai amount
                    else_=0
                )
            )
        ).where(
            models.Transaction.wallet_id == wallet.id, 
            models.Transaction.asset == trade.asset
        )
        result = await db.execute(query)
        #le sommiamo tutte e ottiamo il totale in Decimal
        totale = result.scalar() or Decimal(0)
        #controlliamo se il totale degli euro è inferiore della somma che lui vuole vendere
        if trade.amount > totale:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=f"non hai crypto sufficienti da vendere, hai aquistato: {totale}")
        else: 
            wallet.balance += totale_da_pagare
        
    #creiamo la transazione
    transazione = models.Transaction(
        wallet_id = wallet.id,
        price_at_the_moment = prezzo,
        total_payed = totale_da_pagare,
        status = "COMPLETED",
        **trade.model_dump()
    )
    wallet.transactions.append(transazione)
    await db.commit()
    await db.refresh(transazione)
    return transazione



