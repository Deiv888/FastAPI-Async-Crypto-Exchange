FastAPI Async Crypto Exchange
Un backend ad alte prestazioni per una piattaforma di scambio di criptovalute (Exchange), costruito con Python e FastAPI. Il progetto simula un sistema finanziario reale gestendo transazioni atomiche, aggiornamenti di prezzo in tempo reale e prevenzione di frodi (Double Spending).

Caratteristiche Principali:
🔐 Sicurezza & Autenticazione
JWT Authentication: Sistema di login e registrazione sicuro con hashing delle password (Bcrypt).

Role Based Access: Gli utenti possono accedere e operare solo sui propri wallet.

💰 Gestione Finanziaria (Critical)
Transazioni Atomiche: Deposito, Prelievo, Acquisto e Vendita gestiti con ACID compliance(Atomicità, Coerenza, Isolamento, Durabilità).

Prevenzione Race Conditions: Utilizzo di SELECT ... FOR UPDATE (Row Locking) per prevenire il Double Spending in caso di richieste concorrenti simultanee.

🚀 Performance & Caching
Architettura Asincrona: Utilizzo completo di async/await (Database, API esterne, Cache) per massimizzare il throughput.

Integrazione Redis:

Pattern Cache-Aside: Riduzione delle chiamate API verso Binance salvando i prezzi in cache RAM.

Pub/Sub: Canali per la distribuzione dei prezzi in tempo reale.

🌐 Integrazioni Esterne
Binance API: Recupero dei prezzi di mercato in tempo reale tramite chiamate HTTP asincrone (HTTPX).

🛠️ Tech Stack
Language: Python 3.11+
Framework: FastAPI
Database: PostgreSQL (con driver asyncpg)
ORM: SQLAlchemy (Async Session)
Caching/Broker: Redis
Data Validation: Pydantic V2
Authentication: OAuth2 con JWT

🏛️ Architettura del Progetto
Il progetto segue una struttura modulare e scalabile:

- models.py: Definizioni delle tabelle DB con relazioni ORM (lazy="selectin" per compatibilità async).

- schemas.py: Validazione dati in ingresso/uscita con Pydantic e Nesting dei modelli (es. User -> Wallets -> Transactions).

- routers/: Endpoint REST divisi per logica (Auth, Users, Transactions).

- oauth2.py: Gestione logica JWT e dipendenze di sicurezza (get_current_user).
