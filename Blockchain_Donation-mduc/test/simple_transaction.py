import os
from blockfrost import ApiError, ApiUrls, BlockFrostApi, BlockFrostIPFS
from pycardano import *

# !!! KIỂM TRA LẠI NETWORK VÀ URL !!!
# Bạn đang dùng network = "testnet" (nghĩa là preprod)
# Nhưng BlockFrost URL lại là "preview"
# -> Chọn MỘT trong hai: preprod hoặc preview và dùng nhất quán
network = "preview" # Hoặc "preprod"

if network == "preview":
    base_url = ApiUrls.preview.value # Dùng preview URL
    cardano_network = Network.TESTNET # Testnet dùng cho preview và preprod
    blockfrost_project_id = "preview..." # API Key cho Preview
    blockfrost_base_url = "https://cardano-preview.blockfrost.io/api/"
elif network == "preprod":
    base_url = ApiUrls.preprod.value # Dùng preprod URL
    cardano_network = Network.TESTNET # Testnet dùng cho preview và preprod
    blockfrost_project_id = "preprod..." # API Key cho Preprod
    blockfrost_base_url = "https://cardano-preprod.blockfrost.io/api/"
else: # Mainnet
    base_url = ApiUrls.mainnet.value
    cardano_network = Network.MAINNET
    blockfrost_project_id = "mainnet..." # API Key cho Mainnet
    blockfrost_base_url = "https://cardano-mainnet.blockfrost.io/api/"


wallet_mnemonic = "right quiz dragon salmon tattoo fork world cannon length brother scale fiction fence sorry midnight truly tobacco thrive woman drum finger bubble hedgehog notice"

new_wallet = crypto.bip32.HDWallet.from_mnemonic(wallet_mnemonic)
payment_key = new_wallet.derive_from_path(f"m/1852'/1815'/0'/0/0")
staking_key = new_wallet.derive_from_path(f"m/1852'/1815'/0'/2/0")
payment_skey = ExtendedSigningKey.from_hdwallet(payment_key)
staking_skey = ExtendedSigningKey.from_hdwallet(staking_key)

print("Enterprise address (only payment):")
enterprise_address = Address(
    payment_part=payment_skey.to_verification_key().hash(), network=cardano_network
)
print(enterprise_address)

print("Staking enabled address:")
staking_enabled_address = Address(
    payment_part=payment_skey.to_verification_key().hash(),
    staking_part=staking_skey.to_verification_key().hash(),
    network=cardano_network,
)
print(staking_enabled_address)

print("Payment Signing Key:")
print(payment_skey)
print("Payment Verification Key:")
print(payment_skey.to_verification_key())

# --- Simple transaction: 2 ada to an address ---
recipient_address_str = "addr_test1qrufwlthgmawesrtj7ykvfh30kl6kjn3cz8sla769tjyngsxu7u7lu4xqq2jzkkc9ge0s7wra3yn2lztzfeh7xnu4ujs8l2avj"
amount_to_send = 2000000  # 2 ADA in lovelace
api_key = "previewJhNPT5QxoI6h2TujleChtJ7qTxNZqSAZ"

api_key = "previewJhNPT5QxoI6h2TujleChtJ7qTxNZqSAZ"  # Replace with your BlockFrost API key
context = BlockFrostChainContext(
    api_key, 
    base_url="https://cardano-preview.blockfrost.io/api/"
)

# Get the sender's address (Staking enabled address)
sender_address = staking_enabled_address
print(f"Sender address: {sender_address}")

# Fetch UTXOs for the sender's address
print("Fetching UTXOs...")
try:
    utxos = context.utxos(str(sender_address)) # Chuyển address thành string
    if not utxos:
        print(f"ERROR: No UTXOs found for address {sender_address}.")
        print(f"Please fund this address on the {network} network.")
        # Có thể kiểm tra tại faucet tương ứng (ví dụ: Preview Faucet, Preprod Faucet)
        exit() # Thoát nếu không có UTXO
    print(f"Found {len(utxos)} UTXO(s).")
    # In ra tổng số dư để kiểm tra
    total_balance = sum(utxo.output.amount.coin for utxo in utxos)
    print(f"Total ADA balance: {total_balance / 1_000_000} ADA ({total_balance} lovelace)")

    # Create a transaction builder
    builder = TransactionBuilder(context)

    # Add inputs from UTXOs 
    print("utxo is: ", utxos[13])
    builder.add_input(utxos[13])
    print("Added input UTXO: ", utxos[13])

    # Add the output (recipient address and amount)
    recipient_address = Address.from_primitive(recipient_address_str)
    builder.add_output(TransactionOutput(recipient_address, amount_to_send))

    # Build, Sign, and Submit
    print("Building and signing transaction...")
    # Change address nên là địa chỉ của người gửi để nhận lại tiền thừa
    signed_tx = builder.build_and_sign([payment_skey], change_address=sender_address)
    print("signed tx is: ", signed_tx)
    print("The signed tx to cbor is: ", signed_tx.to_cbor_hex())
    print("Submitting transaction...")
    """tx_id = context.submit_tx(signed_tx.to_cbor())
    print(f"Transaction submitted successfully.")
    print(f"Transaction ID: {tx_id}")
    print(f"Check on explorer (e.g., CExplorer for {network}): https://{network}.cexplorer.io/tx/{tx_id}")"""

except ApiError as e:
    print(f"Blockfrost API Error: {e}")
except InsufficientUTxOBalanceException as e:
    print(f"Error: Insufficient balance to complete the transaction.")
    print(f"Details: {e}")
    print(f"Check the total balance and ensure it's enough to cover {amount_to_send / 1_000_000} ADA + transaction fee.")
except UTxOSelectionException as e:
     print(f"Error during UTxO selection: {e}")
     # In lại thông tin lỗi chi tiết từ exception
     print(f"Requested output: {e.requested}")
     print(f"Pre-selected inputs value: {e.pre_selected}")
     print(f"Additional UTxO pool value: {e.pool}")
     print(f"Unfulfilled amount: {e.unfulfilled}")
     print(f"Ensure the address {sender_address} has enough funds.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    import traceback
    traceback.print_exc()
