from pycardano import (
    TransactionBody, TransactionInput, TransactionId, TransactionOutput,
    Address, Transaction, TransactionWitnessSet, BlockFrostChainContext,
    Value  # Import Value to handle Lovelace amounts
)

# --- Replace Placeholder Values ---
# Blockfrost Project ID (register for free at Blockfrost.io)
BLOCKFROST_PROJECT_ID = "previewJhNPT5QxoI6h2TujleChtJ7qTxNZqSAZ"
NETWORK = "https://cardano-preview.blockfrost.io/api/"

context = BlockFrostChainContext(BLOCKFROST_PROJECT_ID, base_url=NETWORK)

# Sender and receiver addresses
sender_address = "addr_test1qrufwlthgmawesrtj7ykvfh30kl6kjn3cz8sla769tjyngsxu7u7lu4xqq2jzkkc9ge0s7wra3yn2lztzfeh7xnu4ujs8l2avj"
receiver_address = "addr_test1qrufwlthgmawesrtj7ykvfh30kl6kjn3cz8sla769tjyngsxu7u7lu4xqq2jzkkc9ge0s7wra3yn2lztzfeh7xnu4ujs8l2avj"

# Transaction input details
input_tx_id_hex = "c21db19ce16e5f3e77c8b086e07077859378b8564cc7ffb3c7d30114950c17e9"
input_tx_index = 1

# Fetch UTXOs for the sender address
"""utxos = context.utxos(str(sender_address))
if not utxos:
    print(f"ERROR: No UTXOs found for address {sender_address}.")
    print(f"Please fund this address on the testnet network.")
    exit()

print(f"Found {len(utxos)} UTXO(s).")
total = sum(utxo.output.amount.coin for utxo in utxos)
print(f"Total ADA balance: {sum / 1_000_000} ADA ({sum} lovelace)")"""

input_amount_lovelace = 9639141629

# Amount to send and estimated fee
send_amount_lovelace = 2_000_000
fee_lovelace = 170_000

# Create address objects
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
cbor_hex = transaction.to_cbor_hex()

# Print results
print("\n--- Transaction Object (Python) ---")
print(transaction)

print("\n--- Raw Transaction CBOR (Hex - Unsigned) ---")
print(cbor_hex)

print("\n--- Next Steps ---")
print("1. Save this CBOR hex to a file (e.g., tx.raw.cborhex).")
print("2. Use cardano-cli or another library to SIGN this transaction with the private key corresponding to the input address.")
print("3. Submit the signed transaction to the Cardano network.")
