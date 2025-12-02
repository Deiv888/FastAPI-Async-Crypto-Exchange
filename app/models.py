from .database import Base
from sqlalchemy import TIMESTAMP, Column, Integer, ForeignKey, Numeric, String, Boolean, text
from sqlalchemy.orm import relationship

#L'ORM(Object Relational Mapping) è una tecnica di programmazione che crea un ponte tra la progemmazione O.O.
#e i database relazionali, permette di interagire con il database tramite linguaggio di programmazione, senza query

#creiamo le diverse tabelle che erediteranno da Base
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    #con relationship creiamo un collegamento logico tra due modelli per poter navigare tra i dati
    #in pratica gli sto dicendo che ogni utente ha dei portafogli
    #selectin è fondamentale per il codice asincrono, dice a SQLAlchemy di scaricare tutti i Wallet mentre scarica l'utente
    #rendendo subito disponibili tutti i dati
    wallets = relationship("Wallet", back_populates="owner", lazy="selectin")

class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    currency = Column(String, nullable=False, server_default=text("'EUR'"))
    balance = Column(Numeric(18, 8), nullable=False, server_default=text("0"))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    #ogni wallet ha un proprietario nella tabella User
    owner = relationship("User", back_populates="wallets", lazy="selectin")
    #ogni wallet è collegato a piu transazioni della tabella Transaction
    transactions = relationship("Transaction", back_populates="wallet", lazy="selectin")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, nullable=False)
    wallet_id = Column(Integer, ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False)
    type = Column(String, nullable=False)
    asset = Column(String, nullable=False)
    amount = Column(Numeric(18, 8), nullable=False)
    price_at_the_moment = Column(Numeric(18, 8), nullable=False)
    total_payed = Column(Numeric(18, 8), nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    #ogni transazione è collegata al suo wallet della tabella Wallet
    wallet = relationship("Wallet", back_populates="transactions", lazy="selectin")


