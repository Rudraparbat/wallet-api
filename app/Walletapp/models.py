from enum import Enum
from select import select
from unittest import case
import uuid
from sqlalchemy.dialects.postgresql import UUID 
from sqlalchemy import JSON, Column, Integer, String, Float, ForeignKey, DateTime , Enum as SqlEnum, Text
from sqlalchemy.orm import relationship
from app.Utils.database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime


# User Model
class User(Base) :

    __tablename__ = "users"
    id = Column(Integer , primary_key=True , index=True)
    first_name = Column(String , nullable=False)
    last_name = Column(String , nullable=False)
    username = Column(String , unique=True , index=True , nullable=False)
    email = Column(String , unique=True , index=True , nullable=False)
    phone_number = Column(String , unique=True , nullable=False)
    created_at = Column(DateTime , default=datetime.utcnow)
    updated_at = Column(DateTime , default=datetime.utcnow , onupdate=datetime.utcnow)

    # Relationship to Wallets 
    wallets = relationship("Wallet", back_populates="user", cascade="all, delete-orphan")
    



# Wallet Model
class Wallet(Base) :

    __tablename__ = "wallets"
    id = Column(Integer , primary_key=True , index=True)
    user_id = Column(Integer , ForeignKey("users.id" , ondelete="CASCADE") , nullable=False)
    balance = Column(Float , default=0.0)
    currency = Column(String , default="USD")
    created_at = Column(DateTime , default=datetime.utcnow)

    # Relationship to User
    user = relationship("User", back_populates="wallets")
    # Relationship to Transactions 
    transactions = relationship(
        "Transactions",
        back_populates="wallet",
        cascade="all, delete-orphan"
    )


class TransactionType(str , Enum) :
    CREDIT = "credit"
    DEBIT = "debit"


# Transactions Model
class Transactions(Base) :

    __tablename__ = "transactions"
    id = Column(Integer , primary_key=True , index=True)
     # Each transaction belongs to ONE wallet
    wallet_id = Column(Integer, ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False)
    
    # This links the debit and credit of a single transfer
    group_id = Column(UUID(as_uuid=True), default=uuid.uuid4, index=True) 
    
    amount = Column(Float, nullable=False)
    transaction_type = Column(SqlEnum(TransactionType), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    
    wallet = relationship("Wallet", back_populates="transactions")
    
