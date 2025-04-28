import os
from dotenv import load_dotenv
import json
from pycardano import (
    BlockFrostChainContext,
    Address,
    Network,
    TransactionBuilder,
    TransactionOutput,
    Value,
    MultiAsset,
    UTxO,
    HDWallet,
    BIP32ED25519PrivateKey,
    BIP32ED25519PublicKey,
    Transaction,
    TransactionWitnessSet
)

# Load environment variables
load_dotenv()

# Blockfrost configuration
BLOCKFROST_PROJECT_ID = os.getenv("BLOCKFROST_PROJECT_ID", "previewJhNPT5QxoI6h2TujleChtJ7qTxNZqSAZ")
NETWORK = Network.TESTNET if os.getenv("NETWORK", "testnet").lower() == "testnet" else Network.MAINNET
BASE_URL = "https://cardano-preview.blockfrost.io/api/" if NETWORK == Network.TESTNET else "https://cardano-mainnet.blockfrost.io/api/"

# Initialize chain context
context = BlockFrostChainContext(BLOCKFROST_PROJECT_ID, base_url=BASE_URL)

def generate_wallet_from_mnemonic(mnemonic, passphrase=""):
    """Generate a wallet from a mnemonic phrase."""
    if not HDWallet.is_mnemonic(mnemonic):
        raise ValueError("Invalid mnemonic phrase")
    
    # Create root HDWallet from mnemonic
    root_hdwallet = HDWallet.from_mnemonic(mnemonic, passphrase)
    
    # Derive payment key pair
    payment_path = "m/1852'/1815'/0'/0/0"
    payment_hdwallet = root_hdwallet.derive_from_path(payment_path)
    
    payment_signing_key = BIP32ED25519PrivateKey(
        private_key=payment_hdwallet.xprivate_key,
        chain_code=payment_hdwallet.chain_code
    )
    
    payment_verification_key = BIP32ED25519PublicKey.from_private_key(payment_signing_key)
    
    # Derive stake key pair
    stake_path = "m/1852'/1815'/0'/2/0"
    stake_hdwallet = root_hdwallet.derive_from_path(stake_path)
    
    stake_signing_key = BIP32ED25519PrivateKey(
        private_key=stake_hdwallet.xprivate_key,
        chain_code=stake_hdwallet.chain_code
    )
    
    stake_verification_key = BIP32ED25519PublicKey.from_private_key(stake_signing_key)
    
    # Generate address
    address = Address(
        payment_part=payment_verification_key.public_key.hex(),
        staking_part=stake_verification_key.public_key.hex(),
        network=NETWORK
    )
    
    return {
        "address": str(address),
        "payment_signing_key": payment_signing_key,
        "payment_verification_key": payment_verification_key,
        "stake_signing_key": stake_signing_key,
        "stake_verification_key": stake_verification_key
    }

def get_wallet_balance(address):
    """Get the balance of an address."""
    try:
        address_obj = Address.from_primitive(address)
        utxos = context.utxos(address_obj)
        
        total_lovelace = 0
        for utxo in utxos:
            total_lovelace += utxo.output.amount.coin
        
        # Convert lovelace to ADA
        ada_balance = total_lovelace / 1_000_000
        
        return {
            "success": True,
            "balance_lovelace": total_lovelace,
            "balance_ada": ada_balance
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def get_transaction_history(address):
    """Get transaction history for an address."""
    try:
        address_obj = Address.from_primitive(address)
        transactions = context.transactions(address_obj)
        
        tx_history = []
        for tx_hash in transactions:
            tx_info = context.transaction(tx_hash)
            tx_history.append({
                "hash": tx_hash,
                "block_height": tx_info.block_height,
                "timestamp": tx_info.timestamp,
                "fee": tx_info.fee,
                "deposit": tx_info.deposit,
                "size": tx_info.size
            })
        
        return {
            "success": True,
            "transactions": tx_history
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def create_campaign_address():
    """Create a new address for a campaign."""
    try:
        # Generate mnemonic for the campaign
        wallet = HDWallet.generate()
        mnemonic = wallet.to_mnemonic()
        
        # Create wallet from mnemonic
        wallet_data = generate_wallet_from_mnemonic(mnemonic)
        
        return {
            "success": True,
            "address": wallet_data["address"],
            "mnemonic": mnemonic
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def verify_transaction(tx_hash):
    """Verify a transaction on the blockchain."""
    try:
        tx_info = context.transaction(tx_hash)
        return {
            "success": True,
            "verified": True,
            "transaction": {
                "hash": tx_hash,
                "block_height": tx_info.block_height,
                "timestamp": tx_info.timestamp,
                "fee": tx_info.fee,
                "deposit": tx_info.deposit,
                "size": tx_info.size
            }
        }
    except Exception as e:
        return {
            "success": False,
            "verified": False,
            "error": str(e)
        }

# Load wallet from Eternl export
def load_eternl_wallet(json_file_path):
    """Load wallet from Eternl export file."""
    try:
        with open(json_file_path, 'r') as file:
            wallet_data = json.load(file)
        
        # Extract address
        address = None
        if 'wallet' in wallet_data and 'accountList' in wallet_data and len(wallet_data['accountList']) > 0:
            account_id = wallet_data['accountList'][0]['account']['id']
            network_id = wallet_data['wallet']['networkId']
            
            # This is a simplified approach; in a real application, you'd need to
            # derive the address from the key material properly
            return {
                "success": True,
                "wallet_id": wallet_data['wallet']['id'],
                "network": network_id,
                "account_id": account_id
            }
        else:
            return {
                "success": False,
                "error": "Invalid Eternl wallet export format"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def build_donation_transaction(sender_address, receiver_address, amount_lovelace):
    """
    Build a transaction for donation
    
    Args:
        sender_address (str): The sender's wallet address
        receiver_address (str): The campaign's wallet address
        amount_lovelace (int): The amount to send in lovelace (1 ADA = 1,000,000 lovelace)
        
    Returns:
        dict: Result with CBOR hex string for wallet signing
    """
    try:
        # Convert addresses to Address objects
        sender = Address.from_primitive(sender_address)
        receiver = Address.from_primitive(receiver_address)
        
        # Create transaction builder
        builder = TransactionBuilder(context)
        
        # Add sender's address as input
        builder.add_input_address(sender)
        
        # Add output to receiver (campaign)
        builder.add_output(
            TransactionOutput(
                address=receiver,
                amount=Value(coin=amount_lovelace)
            )
        )
        
        # Calculate fee and build transaction
        tx_body = builder.build(change_address=sender)
        
        # Create unsigned transaction with empty witness set
        unsigned_tx = Transaction(tx_body, TransactionWitnessSet())
        
        # Convert to CBOR hex
        cbor_hex = unsigned_tx.to_cbor_hex()
        
        return {
            "success": True,
            "cbor_hex": cbor_hex,
            "fee": tx_body.fee
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        } 