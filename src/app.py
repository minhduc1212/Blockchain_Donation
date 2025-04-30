from flask import Flask, jsonify, render_template, request
from pycardano import *

app = Flask(__name__)

# Global variable to store the CBOR hex address and sender address
cbor_hex_address = None
sender_address = None

def get_utxo(amount_to_spend, fee_lovelace, sender_address, context):
    utxo_s = []
    first_valid_utxo_index = 0
    address = Address.from_primitive(sender_address)

    # Get all UTXOs
    utxos = context.utxos(str(address))
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

def decode_address(cbor_hex_address):
    """
    Decode the CBOR hex address and extract the sender address.
    """
    try:
        cbor_hex_string_base = "84a3008182582042263fc151905c8da840a984e9e57b05ca0323842c615585168721fa6f6700aa01018282583900f8977d7746faecc06b97896626f17dbfab4a71c08f0ff7da2ae449a206e7b9eff2a60015215ad82a32f879c3ec49357c4b12737f1a7caf251a001e848082583900415df791b636a194b1a16a1620d14ead89f75a7e6967376766f229ea317b386a943d141589fc7ac8b8e53fecb0acfd499b20125859c322d21b0000000253c9aae0021a00029810a0f5f6"
        cbor_hex_string = cbor_hex_string_base.replace("00415df791b636a194b1a16a1620d14ead89f75a7e6967376766f229ea317b386a943d141589fc7ac8b8e53fecb0acfd499b20125859c322d2", cbor_hex_address)
        reconstructed_transaction = Transaction.from_cbor(cbor_hex_string)
        reconstructed_tx_body = reconstructed_transaction.transaction_body
        tx_body = str(reconstructed_tx_body.outputs[1]).splitlines()
        for line in tx_body:
            if "address" in line:
                sender_address = line.split(': ')[1].replace(',', '')
                print(f"Sender Address: {sender_address}")
                return sender_address
    except Exception as e:
        print(f"Error decoding CBOR hex address: {e}")
        return None

# Configuration
BLOCKFROST_PROJECT_ID = "previewJhNPT5QxoI6h2TujleChtJ7qTxNZqSAZ"
NETWORK = "https://cardano-preview.blockfrost.io/api/"

# Receiver address
receiver_address = "addr_test1qrufwlthgmawesrtj7ykvfh30kl6kjn3cz8sla769tjyngsxu7u7lu4xqq2jzkkc9ge0s7wra3yn2lztzfeh7xnu4ujs8l2avj"

# Transaction fee
fee_lovelace = 170000

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/set_unused_address", methods=["POST"])
def set_unused_address():
    """
    Endpoint to set the unused CBOR hex address and decode it.
    """
    global cbor_hex_address, sender_address
    try:
        data = request.get_json()
        cbor_hex_address = data.get("cbor_hex_address", "")
        if not cbor_hex_address:
            return jsonify({"error": "Missing CBOR hex address"}), 400

        sender_address = decode_address(cbor_hex_address)
        if not sender_address:
            return jsonify({"error": "Failed to decode CBOR hex address"}), 500

        return jsonify({"sender_address": sender_address}), 200
    except Exception as e:
        print(f"Error setting unused address: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/build_tx", methods=["POST"])
def build_transaction():
    try:
        # Get the amount to send from the request
        data = request.get_json()
        send_amount_lovelace = int(data.get("amount", 0))
        if send_amount_lovelace <= 0:
            return jsonify({"error": "Invalid amount"}), 400

        if not sender_address:
            return jsonify({"error": "Sender address is not set. Please connect the wallet and fetch the unused address first."}), 400

        context = BlockFrostChainContext(BLOCKFROST_PROJECT_ID, base_url=NETWORK)
        input_tx_id_hex, input_tx_index, input_amount_lovelace = get_utxo(send_amount_lovelace, fee_lovelace, sender_address, context)

        print(f"Transaction hash: {input_tx_id_hex}")
        print(f"tx_id: {input_tx_index}")
        print(f"Input amount: {input_amount_lovelace} lovelace")

        my_address = Address.from_primitive(sender_address)
        recipient_address = Address.from_primitive(receiver_address)

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
            return jsonify({"error": "Insufficient balance to send the amount and cover fees."}), 400
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

        print("\n--- Raw Transaction CBOR (Hex - Unsigned) ---")
        print(cbor_hex)
        return jsonify({"cbor_hex": cbor_hex})
    except Exception as e:
        print(f"Error building transaction: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)