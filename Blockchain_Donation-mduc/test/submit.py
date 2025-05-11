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



api_key = "previewJhNPT5QxoI6h2TujleChtJ7qTxNZqSAZ"

context = BlockFrostChainContext(
    api_key, 
    base_url="https://cardano-preview.blockfrost.io/api/"
)


try:
    print("Submitting transaction...")
    tx_id = context.submit_tx(b'\x84\xa3\x00\xd9\x01\x02\x81\x82X N=\x89\x15"\x99BX\xb1[\xcf+\xf6\xa2\xd6>\x1c\xf7\xd6\x90\x1eX\x8b\x116\x1e\x90\xbfK \xe8\x88\x01\x01\x82\x82X9\x00\xf8\x97}wF\xfa\xec\xc0k\x97\x89f&\xf1}\xbf\xabJq\xc0\x8f\x0f\xf7\xda*\xe4I\xa2\x06\xe7\xb9\xef\xf2\xa6\x00\x15!Z\xd8*2\xf8y\xc3\xecI5|K\x12s\x7f\x1a|\xaf%\x1a\x00\x1e\x84\x80\x82X9\x00\xf8\x97}wF\xfa\xec\xc0k\x97\x89f&\xf1}\xbf\xabJq\xc0\x8f\x0f\xf7\xda*\xe4I\xa2\x06\xe7\xb9\xef\xf2\xa6\x00\x15!Z\xd8*2\xf8y\xc3\xecI5|K\x12s\x7f\x1a|\xaf%\x1b\x00\x00\x00\x029\xd9\x99\xfb\x02\x1a\x00\x02\x91}\xa1\x00\xd9\x01\x02\x81\x82X \xd2\x17n\xafU\xf6=\x96 U\x0e_F,\xe6\x1e\x00\x81\x7f<\xb4B\x84\x1av\xf9,\xb1\xd3c>\xc6X@L#\x8cn\xb4\xd8\n\xa0\x01&\xcfr\xdd\x8c\xbftI}\xc7\x8c\xe6\xb0D;\x8a\x98\xdac\xaep\x80B\xf1\xba\xff\xefJ\xa75z\x01Sc\xa0!Q\x1d,\x9bush\xa4\x85\x06\x10\x99.\xf8\xc5\x9e_\t\x0e\xf5\xf6')
    print(f"Transaction submitted successfully.")
    print(f"Transaction ID: {tx_id}")
    print(f"Check on explorer (e.g., CExplorer for {network}): https://{network}.cexplorer.io/tx/{tx_id}")

except ApiError as e:
    print(f"Blockfrost API Error: {e}")
except InsufficientUTxOBalanceException as e:
    print(f"Error: Insufficient balance to complete the transaction.")
    print(f"Details: {e}")

except UTxOSelectionException as e:
     print(f"Error during UTxO selection: {e}")
     # In lại thông tin lỗi chi tiết từ exception
     print(f"Requested output: {e.requested}")
     print(f"Pre-selected inputs value: {e.pre_selected}")
     print(f"Additional UTxO pool value: {e.pool}")
     print(f"Unfulfilled amount: {e.unfulfilled}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    import traceback
    traceback.print_exc()
