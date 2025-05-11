import requests
from pycardano import Address
from datetime import datetime

# Initialize BlockFrost API details
API_KEY = "previewJhNPT5QxoI6h2TujleChtJ7qTxNZqSAZ"  # Replace with your Blockfrost API key
BASE_URL = "https://cardano-preview.blockfrost.io/api/v0"  # Corrected URL with /v0

headers = {
    "project_id": API_KEY
}

# Specify the Cardano address
address = Address.from_primitive("addr_test1qrufwlthgmawesrtj7ykvfh30kl6kjn3cz8sla769tjyngsxu7u7lu4xqq2jzkkc9ge0s7wra3yn2lztzfeh7xnu4ujs8l2avj")

content = ""
try:
    # Fetch UTXOs for the address
    utxos_url = f"{BASE_URL}/addresses/{str(address)}/utxos"
    response = requests.get(utxos_url, headers=headers)
    print(f"Fetching UTXOs from: {utxos_url}")
    print(f"Response Status Code: {response.status_code}")
    # Check if the response is valid
    if response.status_code != 200:
        raise Exception(f"Failed to fetch UTXOs. Status Code: {response.status_code}, Response: {response.text}")

    utxos = response.json()
    with open("utxos.json", "w") as f:
        f.write(response.text)

    if not utxos:
        print(f"No UTXOs found for the address: {address}.")
        exit()

    transaction_details = []  # Store details of transactions

    for utxo in utxos:
        tx_id = utxo["tx_hash"]  
        tx_url = f"{BASE_URL}/txs/{tx_id}"  # Fetch transaction details
        tx_response = requests.get(tx_url, headers=headers)

        # Check if the transaction response is valid
        if tx_response.status_code != 200:
            raise Exception(f"Failed to fetch transaction details. Status Code: {tx_response.status_code}, Response: {tx_response.text}")

        transaction = tx_response.json()
        
        # Extract information from JSON
        block_time = datetime.fromtimestamp(transaction["block_time"])  # Convert block time
        amount_lovelace = int(transaction["output_amount"][0]["quantity"])  # Get lovelace amount
        amount_ada = amount_lovelace / 1_000_000  # Convert lovelace to ADA

        tx_detail_url = f"{BASE_URL}/txs/{tx_id}/utxos"  # Fetch UTXO details for the transaction
        tx_detail = requests.get(tx_detail_url, headers=headers)
        # Get address send, or receive and amount of ADA in output
        if tx_detail.status_code == 200:
            tx_detail_json = tx_detail.json()
            if "outputs" in tx_detail_json:  # Ensure the key exists
                for output in tx_detail_json["outputs"]:  # Iterate over the outputs
                    if output["address"] == str(address):
                        amount = int(output["amount"][0]["quantity"])
                        print(f"Transaction ID: {tx_id}")
                        print(f"  - Sent {amount / 1_000_000:.6f} ADA to your address: {address}")
                        content += f"Transaction {tx_id} sent {amount} lovelace to {address}\n"
                    else:
                        amount = int(output["amount"][0]["quantity"])
                        print(f"Transaction ID: {tx_id}")
                        print(f"  - Received {amount / 1_000_000:.6f} ADA from address: {output['address']}")
                        content += f"Transaction {tx_id} received {amount} lovelace from {output['address']}\n"
            else:
                print(f"Transaction ID: {tx_id}")
                print(f"  - Unexpected structure in UTXO details.")
        else:
            print(f"Transaction ID: {tx_id}")
            print(f"  - Failed to fetch UTXO details. Status Code: {tx_detail.status_code}, Response: {tx_detail.text}")

        # Print transaction summary
        print(f"Transaction Summary:")
        print(f"  - Transaction ID: {tx_id}")
        print(f"  - Block Time: {block_time}")
        print(f"  - Total Amount: {amount_ada:.6f} ADA")
        print("-" * 50)

except Exception as e:
    print("Error fetching transactions:", e)