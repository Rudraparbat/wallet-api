import uuid
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum as PyEnum

# Enum for transaction types, mirroring the SQLAlchemy enum
class TransactionType(str, PyEnum):
    CREDIT = "credit"
    DEBIT = "debit"

# ===================================================================
# Transaction Schemas
# ===================================================================

class TransactionCreate(BaseModel):
    sender_wallet_id: int
    receiver_wallet_id: int
    amount: float
    description: Optional[str] = None

# --- Schemas for Displaying Transaction History ---
class OtherPartyInfo(BaseModel):
    """
    A nested schema to hold the public information of the
    other user involved in a transaction.Like where the amount sended or from where the amount is received
    """
    id: int
    username: str
    first_name: str
    last_name: str

    class Config:
        from_attributes = True 
class TransactionHistory(BaseModel):
    """A single, clear entry in a user's transaction history."""
    id: int
    group_id: uuid.UUID
    amount: float
    transaction_type : TransactionType
    description: Optional[str] = None
    created_at: datetime
    credited_from_or_debited_to : OtherPartyInfo

    class Config:
        from_attributes = True


# ===================================================================
# Wallet Schemas
# ===================================================================

class WalletBase(BaseModel):
    """Base schema for a wallet's core fields."""
    balance: float = 0.0
    currency: str = "USD"

class WalletCreate(WalletBase):
    """Schema for creating a new wallet, linked to a user."""
    user_id: int

class WalletUpdate(BaseModel):
    """Schema for updating a wallet. All fields are optional."""
    balance: Optional[float] = None
    currency: Optional[str] = None

class WalletInDB(WalletBase):
    """Schema representing a wallet as it is in the database."""
    id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True

# ===================================================================
# User Schemas
# ===================================================================

class UserBase(BaseModel):
    """Base schema for a user's core fields."""
    first_name: str
    last_name: str
    username: str
    email: str # Changed from EmailStr to avoid dependency issues
    phone_number: str

class UserCreate(UserBase):
    """Schema for creating a new user"""
    pass

class UserUpdate(BaseModel):
    """Schema for updating a user. All fields are optional."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None

class UserInDB(UserBase):
    """Schema representing a user as it is in the database."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ===================================================================
# Schemas for API Output 
# ===================================================================


class WalletDetailsWithTransactions(WalletInDB):
    """Wallet output that includes a list of its transactions."""
    transactions: Optional[List[TransactionHistory]] = []

class UserDetailsWithWallet(UserInDB):
    """Comprehensive user output including all their wallets."""
    wallets: List[WalletInDB] = []


