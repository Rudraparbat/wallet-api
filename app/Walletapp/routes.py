from fastapi import APIRouter, Depends, HTTPException, status , Response , Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
from app.Utils.database import get_db
from app.Walletapp.schema import TransactionCreate, TransactionHistory, UserDetailsWithWallet, UserInDB  , UserCreate, WalletCreate, WalletDetailsWithTransactions, WalletInDB, WalletUpdate
from app.Walletapp.services import TransactionService, UserService, WalletService

router = APIRouter()

########  routes for user operations ##########
@router.post("/create-user/" , status_code=status.HTTP_201_CREATED , response_model=UserInDB)
async def create_user(user_data : UserCreate ,db : Session = Depends(get_db)) :
    return await UserService.create_user(db , user_data)

@router.get("/users/{user_id}" , response_model=UserDetailsWithWallet)
async def get_user_by_id(user_id : int , db : Session = Depends(get_db)) :
    return await UserService.get_user_by_id(db , user_id)

@router.get("/users" , response_model=List[UserDetailsWithWallet])
async def get_users_list(db : Session = Depends(get_db)) :
    return await UserService.get_users_list(db)


########## routes for wallet operations ##########
@router.post("/create-wallet/" , status_code=status.HTTP_201_CREATED , response_model=WalletInDB)
async def create_wallet(wallet_details :  WalletCreate , db : Session = Depends(get_db)) :
    return await WalletService.create_wallet(db , wallet_details)

@router.get("/wallets/{user_id}" , response_model=list[WalletInDB])
async def get_wallet_by_user_id(user_id : int , db : Session = Depends(get_db)) :
    return await WalletService.get_wallet_by_user_id(db , user_id)

@router.put("edit/wallet/{wallet_id}" , response_model=WalletInDB)
async def update_wallet(wallet_id : int , wallet_data : WalletUpdate ,  db : Session = Depends(get_db)) :
    return await WalletService.update_wallet_amount(db , wallet_id , wallet_data)



########### routes for transaction operations ##########
@router.post("/create-transaction/" , status_code=status.HTTP_201_CREATED , response_model=dict)
async def create_transaction(transaction_data :  TransactionCreate , db : Session = Depends(get_db)) :
    return await TransactionService.create_transaction(db , transaction_data)

@router.get("/fetch-transactions/" , status_code=status.HTTP_201_CREATED , response_model=List[TransactionHistory])
async def all_transactions(user_id : int , db : Session = Depends(get_db)) :
    query =  await TransactionService.get_all_transaction_by_user_id(db=db, user_id=user_id)

    # Unpack the data tuple
    response_data = [
                TransactionHistory(
                    id=user_transaction.id,
                    amount=user_transaction.amount,
                    group_id=user_transaction.group_id,
                    transaction_type=user_transaction.transaction_type.value, 
                    description=user_transaction.description,
                    created_at=user_transaction.created_at,
                    credited_from_or_debited_to =other_user
                )
                for user_transaction, other_user in query
            ]
    
    return response_data


