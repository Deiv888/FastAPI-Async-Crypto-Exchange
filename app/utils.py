from decimal import Decimal
import httpx
from passlib.context import CryptContext
import redis.asyncio as redis
import json

#instanza di CryptoContext che supporta l'algoritmo che voglio usare
pwd_context = CryptContext(schemes="bcrypt", deprecated="auto")

#funzione per hashare un password
def hash(password_inserita: str):
    return pwd_context.hash(password_inserita)

#funzione per verificare la password inserita dall'utente e poi hashata
def verify(password_inserita, password):
    return pwd_context.verify(password_inserita, password)


#qui connetiamo redis, che useremo per implementare il pattern Cache Aside
#se 100 utenti richiedono il prezzo, viene fatta solo una chiamata, gli altri leggono il prezzo dalla cache di redis
try:
    redis_client = redis.from_url("redis://localhost", decode_responses=True)
except Exception as e:
    print(f"Impossibili configurare redis: {e}")
    redis_client = None

#funzione per ottenere il prezzo di una crypto da un api di binance (asincrona)
#indichiamo un tipo di ritorno: la funzione deve restituire o un decimal o niente
async def get_binance_price(ticker: str) -> Decimal | None:
    simbolo = f"{ticker.upper()}USDT"
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={simbolo}"

    #come client per effettuare la richiesta di prezzo usiamo httpx,la libreria standard per richieste HTTP asincrone
    async with httpx.AsyncClient() as client:
        try:
            #mentre scarica i dati lasciamo il controllo all'Event Loop di Python tramite await
            response = await client.get(url, timeout=5.0)

            #se la richiesta va a buon fine salviamo il json in data e restituiamo il prezzo in Decimal
            if response.status_code == 200:
                data = response.json()
                return Decimal(data["price"])
            else:
                return None

        except Exception as e:
            print(f"Errore nel recuper del prezzo per {ticker}: {e}")
            return None
      

#ora useremo la funzione appena creata in una funzione che implementa il pattern Cache Aside
async def get_real_price(ticker: str) -> Decimal | None:

    simbolo = f"{ticker.upper()}USDT"
    #1)cerchiamo nella cache ram di redis
    #2)se non c'è nulla chiamiamo get_binance_price
    #3)e lo salviamo nella cache di redis per le prossime richieste

    if redis_client:
        try:
            #vediamo se c'è gia il prezzo in memoria
            prezzo_della_cache = await redis_client.get(ticker)
            #se c'è lo restituiamo
            if prezzo_della_cache:
                return Decimal(prezzo_della_cache)
        except Exception:
            pass #altrimenti ingoriamo e andiamo avanti

    crypto_list = ["BTC", "ETH"]
    price = None

    #controlliamo che il simbolo inserito dall'utente sia nella lista
    #se c'è recuperiamo il prezzo da binance
    if ticker in crypto_list:
        price = await get_binance_price(ticker)

    #se abbiamo il prezzo proviamo a salvarlo nella cache di redis
    if price and redis_client:
        try:
            #salviamo il prezzo in cache con nome=simbolo, scadenza di 5 secondi, valore=prezzo ottenuto
            await redis_client.setex(name=ticker, time=5, value=str(price))
            #pubblichiamo anche il prezzo su un canale 
            #cosi chi si connette al websocket lo puo ricevere subito
            canale = f"prezzo_di_{ticker}"
            await redis_client.publish(canale, str(price))
        
        except Exception as e:
            print(f"Errore Redis: {e}")
        
    return price

    
#ora creiamo una cosa redis per accumulare piu richieste e fare un unico commi
ORDER_QUEUE_KEY = "coda_ordini"

async def manda_ordine_in_coda(order_data: dict):
    if redis_client:
        #convertiamo il dizionario in una stringa json per redis
        order_json = json.dumps(order_data)
        #LPUSH aggiunge l'elemento in testa alla lista
        await redis_client.lpush(ORDER_QUEUE_KEY, order_json)

#da qui creiamo il worker