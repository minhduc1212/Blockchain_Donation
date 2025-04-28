from pycardano import (
    TransactionBody, TransactionInput, TransactionId, TransactionOutput,
    Address, Transaction, TransactionWitnessSet, BlockFrostChainContext,
    Value  # Import Value to handle Lovelace amounts
)

def get_utxo(amount_to_spend, fee_lovelace, sender_address, context):
    utxo_s = []
    first_valid_utxo_index = 0
    # Pass the string representation of the address
    utxos = context.utxos(str(sender_address))
    for utxo in utxos:
        utxo_s.append(utxo)

    for i, utxo in enumerate(utxo_s):
        if not utxo.output.amount.multi_asset:  # Checks if the dictionary is empty
            print(f"  UTXO {i} contains only ADA.")

            # Check if the ADA amount is sufficient
            utxo_value = utxo.output.amount.coin
            print(f"  UTXO {i} value: {utxo_value} lovelace.")

            if utxo_value > amount_to_spend:
                first_valid_utxo_index = i  # Store the index
                break
            else:
                print(f"  UTXO {i} does not have enough ADA ({utxo_value} <= {amount_to_spend}).")
        else:
            print(f"  UTXO {i} contains multi-asset (native tokens). Skipping.")

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

    return transaction_id, index, utxo_value


BLOCKFROST_PROJECT_ID = "previewJhNPT5QxoI6h2TujleChtJ7qTxNZqSAZ"
NETWORK = "https://cardano-preview.blockfrost.io/api/"

context = BlockFrostChainContext(BLOCKFROST_PROJECT_ID, base_url=NETWORK)

# Sender and receiver addresses
sender_address = "addr_test1qrufwlthgmawesrtj7ykvfh30kl6kjn3cz8sla769tjyngsxu7u7lu4xqq2jzkkc9ge0s7wra3yn2lztzfeh7xnu4ujs8l2avj"
receiver_address = "addr_test1qrufwlthgmawesrtj7ykvfh30kl6kjn3cz8sla769tjyngsxu7u7lu4xqq2jzkkc9ge0s7wra3yn2lztzfeh7xnu4ujs8l2avj"
fee_lovelace = 170000
send_amount_lovelace = 2000000

input_tx_id_hex, input_tx_index, input_amount_lovelace  = get_utxo(send_amount_lovelace, fee_lovelace, sender_address, context)

print(f"Transaction hash: {input_tx_id_hex}")
print(f"tx_id: {input_tx_index}")
print(f"Input amount: {input_amount_lovelace} lovelace")

try:
    my_address = Address.from_primitive(sender_address)
    recipient_address = Address.from_primitive(receiver_address)
except Exception as e:
    print(f"Error decoding address: {e}")
    exit()

# Create transaction input
tx_id = TransactionId(bytes.fromhex(input_tx_id_hex))
tx_in = TransactionInput(transaction_id=tx_id, index=input_tx_index)

# Create transaction outputs
output_send = TransactionOutput(
    address=recipient_address,
    amount=Value(coin=send_amount_lovelace)
)

change_amount_lovelace = input_amount_lovelace - send_amount_lovelace - fee_lovelace
if change_amount_lovelace < 0:
    print(f"Error: Insufficient balance ({input_amount_lovelace}) to send ({send_amount_lovelace}) and cover fees ({fee_lovelace}).")
    exit()
elif change_amount_lovelace == 0:
    print("Warning: No change will be returned.")
    outputs = [output_send]
else:
    output_change = TransactionOutput(
        address=my_address,
        amount=Value(coin=change_amount_lovelace)
    )
    outputs = [output_send, output_change]
    print(f"Input: {input_amount_lovelace / 1_000_000} ADA")
    print(f"Sending: {send_amount_lovelace / 1_000_000} ADA")
    print(f"Fee: {fee_lovelace / 1_000_000} ADA")
    print(f"Change: {change_amount_lovelace / 1_000_000} ADA")

# Get current slot and calculate TTL
try:
    current_slot = context.last_block_slot
    ttl = current_slot + 7200  # TTL set to ~2 hours
    print(f"Current slot: {current_slot}")
    print(f"TTL (Invalid Hereafter): {ttl}")
except Exception as e:
    print(f"Error fetching current slot from BlockFrost: {e}")
    ttl = 100_000_000  # Default TTL if unable to fetch

# Create transaction body
tx_body = TransactionBody(
    inputs=[tx_in],
    outputs=outputs,
    fee=fee_lovelace,
    ttl=ttl
)

# Create an empty witness set
witness_set = TransactionWitnessSet()

# Create the complete transaction
transaction = Transaction(
    transaction_body=tx_body,
    transaction_witness_set=witness_set,
    auxiliary_data=None
)

# Serialize transaction to CBOR hex
cbor_bytes = transaction.to_cbor()  # Ensure this returns bytes
print("Returned value:", cbor_bytes)

