from pycardano import (
    Address,
    BlockFrostChainContext
)

utxo_s = []
amount_to_spend = 2000000  # 2 ADA in lovelace
valid_utxo = 0
first_valid_utxo_index = 0

context = BlockFrostChainContext(
    "previewJhNPT5QxoI6h2TujleChtJ7qTxNZqSAZ",
    base_url="https://cardano-preview.blockfrost.io/api/",
)

address = Address.from_primitive("addr_test1qrufwlthgmawesrtj7ykvfh30kl6kjn3cz8sla769tjyngsxu7u7lu4xqq2jzkkc9ge0s7wra3yn2lztzfeh7xnu4ujs8l2avj")

try:
    utxos = context.utxos(str(address))
    for utxo in utxos:
        utxo_s.append(utxo)

except Exception as e:
    print("Error fetching UTXOs or processing transaction:", e)

with open("utxo.txt", "w") as f:
    f.write(str(utxo_s))

# Iterate through UTXOs to find the one that meets the criteria
for i, utxo in enumerate(utxo_s):
    if not utxo.output.amount.multi_asset: # Checks if the dictionary is empty
        print(f"  UTXO {i} contains only ADA.")

        # 2. Check if the ADA amount is sufficient
        utxo_value = utxo.output.amount.coin
        print(f"  UTXO {i} value: {utxo_value} lovelace.")

        if utxo_value > amount_to_spend:
            first_valid_utxo_index = i    # Store the index
            break 
        else:
            print(f"  UTXO {i} does not have enough ADA ({utxo_value} <= {amount_to_spend}).")
    else:
        print(f"  UTXO {i} contains multi-asset (native tokens). Skipping.")

print(f"First valid UTXO index: {first_valid_utxo_index} has {utxo_value}")

utxo_lines = str(utxo_s[first_valid_utxo_index]).splitlines()
for line in utxo_lines:
    if "transaction_id" in line:
        # Extract the transaction hash
        transaction_id = line.split("'")[-2].strip()
        print("Transaction ID:", transaction_id)
    if "index" in line:
        # Extract the index and convert it to an integer
        index = int(line.split()[1].replace(",", "").strip())
        print("Index:", index)
        
    