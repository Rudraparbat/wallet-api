from ast import List
import uuid
from sqlalchemy import case, func, select, text
from sqlalchemy.orm import Session ,aliased 
from sqlalchemy.orm.exc import NoResultFound
from fastapi import HTTPException, status 
from sqlalchemy.exc import SQLAlchemyError
from app.Walletapp.models import User, Wallet, Transactions, TransactionType
from app.Walletapp.schema import TransactionCreate, UserCreate, UserDetailsWithWallet, UserInDB, WalletCreate, WalletDetailsWithTransactions,TransactionHistory, WalletInDB, WalletUpdate
from dotenv import load_dotenv
load_dotenv()




class UserService :

    @staticmethod
    async def create_user(db : Session , user_data : UserCreate) -> UserInDB :
        try:
            # Check if the user with the same username  already exists or not
            existing_user = db.query(User).filter(
                (User.username == user_data.username) 
            ).first()

            if existing_user :
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST , detail="User with given username, already exists")
            
            # save the user data to db
            user_dict_data = user_data.model_dump()
            data = User(**user_dict_data)
            db.add(data)
            db.commit()
            db.refresh(data)
            return data
        
        # handle exceptions
        except HTTPException as http_error :
            db.rollback()
            raise http_error
        except SQLAlchemyError as db_error :
            db.rollback()
            raise db_error
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        
    
    @staticmethod
    async def get_user_by_id(db : Session , user_id : int) -> UserDetailsWithWallet :
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user :
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="User not found")
            return user
        except HTTPException as http_error :
            raise http_error
        except SQLAlchemyError as db_error :
            raise db_error
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        

    @staticmethod
    async def get_users_list(db : Session) -> list[UserDetailsWithWallet] :
        try:
            users = db.query(User).all()
            return users
        except HTTPException as http_error :
            raise http_error
        except SQLAlchemyError as db_error :
            raise db_error
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        


################### Wallet Services ##################

class WalletService :
    @staticmethod
    async def create_wallet(db : Session , wallet_details : WalletCreate) -> WalletInDB :
        try:
            # Check if the user exists
            user = db.query(User).filter(User.id == wallet_details.user_id).first()
            if not user :
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="User not found")
            
            # Create and save the wallet
            wallet_data = wallet_details.model_dump()
            wallet = Wallet(**wallet_data)
            db.add(wallet)
            db.commit()
            db.refresh(wallet)
            return wallet

        except HTTPException as http_error :
            db.rollback()
            raise http_error
        except SQLAlchemyError as db_error :
            db.rollback()
            raise db_error
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        

    @staticmethod
    async def get_wallet_by_user_id(db : Session , user_id : int) -> list[WalletInDB] :
        try:
            wallets = db.query(Wallet).filter(Wallet.user_id == user_id).all()
            if not wallets :
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="No wallets found for the user")
            return wallets
        except HTTPException as http_error :
            raise http_error
        except SQLAlchemyError as db_error :
            raise db_error
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        

    @staticmethod
    async def update_wallet_amount(db : Session , wallet_id : int ,  wallet_data : WalletUpdate) -> WalletInDB :
        try:
            # Fetch the wallet
            wallet = db.query(Wallet).filter(Wallet.id == wallet_id).first()
            if not wallet :
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="Wallet not found")
            
            # Update the balance based on transaction type
            wallet.balance += wallet_data.balance
            db.commit()
            db.refresh(wallet)
            return wallet

        except HTTPException as http_error :
            db.rollback()
            raise http_error
        except SQLAlchemyError as db_error :
            db.rollback()
            raise db_error
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        

################### Transaction Services ##################

class TransactionService :

    async def create_transaction(db : Session , transaction_data : TransactionCreate) -> dict :
        try:
            # Check if the sender and reciever wallet id is equal or not 
            if transaction_data.sender_wallet_id == transaction_data.receiver_wallet_id :
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST , detail="Sender and Receiver wallet cannot be the same")
            
            # Searching for both wallets and lock them for update
            sender_wallet = db.query(Wallet).filter(Wallet.id == transaction_data.sender_wallet_id).with_for_update().one()
            receiver_wallet = db.query(Wallet).filter(Wallet.id == transaction_data.receiver_wallet_id).with_for_update().one()

            # check the amount is eligble or not
            if sender_wallet.balance < transaction_data.amount:
                raise ValueError("Insufficient funds")

            if transaction_data.amount <= 0 :
                raise ValueError("Given Input Amount is not eligble")
            
            # Stage balance updates
            sender_wallet.balance -= transaction_data.amount
            receiver_wallet.balance += transaction_data.amount

            # Create a single group ID for this transfer
            transfer_group_id = uuid.uuid4()

            # Create the DEBIT record for the sender
            debit_record = Transactions(
                wallet_id=sender_wallet.id,
                group_id=transfer_group_id,
                amount=transaction_data.amount,
                transaction_type= TransactionType.DEBIT,
                description= None if not transaction_data.description else transaction_data.description
            )

            # Create the CREDIT record for the receiver
            credit_record = Transactions(
                wallet_id= receiver_wallet.id,
                group_id= transfer_group_id,
                amount=transaction_data.amount,
                transaction_type=TransactionType.CREDIT,
                description= None if not transaction_data.description else transaction_data.description
            )

            db.add_all([debit_record, credit_record])
            db.commit() 
            db.refresh(debit_record)
            db.refresh(credit_record)
            
            return {"status": "success", "group_id": debit_record.group_id}
        except HTTPException as http_error :
            db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(http_error))
        except NoResultFound as not_found_error :
            db.rollback()
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(not_found_error))
        except SQLAlchemyError as db_error :
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(db_error))
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
        

    async def get_all_transaction_by_user_id(db : Session , user_id : int) -> list[TransactionHistory] : 
        try :
            # Get the wallet 
            user_wallet = db.query(Wallet).filter(Wallet.user_id == user_id).all()
            # Get the All Transaction of the user
            if not user_wallet :
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail="No wallets found for the user")
            user_wallet_ids = [wallet.id for wallet in user_wallet]

        
            UserTransaction = aliased(Transactions, name="user_transaction")
            OtherSideTransaction = aliased(Transactions, name="other_transaction")
            OtherPartyWallet = aliased(Wallet, name="other_wallet")
            OtherPartyUser = aliased(User, name="other_user")

            # The query fetches the user's transaction and the other user's full object
            transactions_with_details = (
                db.query(UserTransaction, OtherPartyUser)
                .join(OtherSideTransaction, UserTransaction.group_id == OtherSideTransaction.group_id)
                .filter(UserTransaction.id != OtherSideTransaction.id)
                .join(OtherPartyWallet, OtherSideTransaction.wallet_id == OtherPartyWallet.id)
                .join(OtherPartyUser, OtherPartyWallet.user_id == OtherPartyUser.id)
                .filter(UserTransaction.wallet_id.in_(user_wallet_ids))
                .order_by(UserTransaction.created_at.desc())
                .all()
            )

            return transactions_with_details
            

        except HTTPException as http_error :
            db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(http_error))
        except NoResultFound as not_found_error :
            db.rollback()
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(not_found_error))
        except SQLAlchemyError as db_error :
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(db_error))
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))