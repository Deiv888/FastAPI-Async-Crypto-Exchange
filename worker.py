import asyncio
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import database, models, utils

#usiamo il batching e write-behind
#il worker è un loop infinito che controlla se ci sono richieste nella coda redis
#se ci sono le processa
#scrive nel db

#CONFIGURAZIONE BATCH:
BATCH_SIZE = 100 #100 ORDINI ALLA VOLTA
POLLING_INTERVAL = 0.1 #ogni tot secondi controlla se ci sono ordini

async def process_orders_batch():
    while True:
        if not utils.redis_client:
            await asyncio.sleep(5)
            continue
        
        ordini_da_processare = []
        for i in range(BATCH_SIZE):
            #rpop prende l'ultimo elemento della coda
            ordine = await utils.redis_client.rpop(utils.ORDER_QUEUE_KEY)
            if ordine:
                ordini_da_processare.append(json.loads(ordine))
            else:
                break

        if not ordini_da_processare:
            await asyncio.sleep(POLLING_INTERVAL)
            continue
        
        #apriamo una sessione dedicata per processario gli ordini
        async with database.SessionLocal() as db:
            print(f"Sto processando un batch di {len(ordini_da_processare)} ordini")

            for ordini in ordini_da_processare:
                try:
                    await esegui_singolo_ordine(db, ordini)
                except Exception as e:
                    print(f"Errore processando ordine {ordini}: {e}")

            await db.commit()

#funziona per processare un singolo ordine
async def esegui_singolo_ordine(db: AsyncSession, data: dict):

    #dati che passeremo nell'endpoint trade del router transactions
    user_id = data["owner_id"]
    asset = data["asset"]
    amount = data["amount"]
    price = data["price"]

    #qui facciamo le stesse cose che facevamo nel router transactions
    #query per ottenere il wallet
    query = select(models.Wallet).where(models.Wallet.owner_id == user_id)
    result = await db.execute(query)
    wallet = result.scalar_one_or_none()

    if not wallet:
        print(f"Wallet non trovato per {user_id}")
        return
    
#riprendi da qui
