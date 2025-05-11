from flask import Flask, jsonify, render_template, request # Add request
from pycardano import *
import logging # Add logging

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# ... (keep get_utxo function as is for now, but it will use the dynamic address)

# Configuration (keep these)
BLOCKFROST_PROJECT_ID = "previewJhNPT5QxoI6h2TujleChtJ7qTxNZqSAZ"
NETWORK_URL = "https://cardano-preview.blockfrost.io/api/" # Renamed for clarity
NETWORK = Network.TESTNET # Define the network object for pycardano

# Remove hardcoded sender/receiver here - they become dynamic or parameters
# sender_address = "..."
receiver_address_str = "addr_test1qrufwlthgmawesrtj7ykvfh30kl6kjn3cz8sla769tjyngsxu7u7lu4xqq2jzkkc9ge0s7wra3yn2lztzfeh7xnu4ujs8l2avj" # Keep receiver if it's fixed

# Transaction constants (keep these)
fee_lovelace = 170000
send_amount_lovelace = 3000000

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/build_tx", methods=["POST"]) # Change to POST to receive data
def build_transaction():
    # --- Get data from frontend ---
    data = request.get_json()
    if not data or 'sender_address' not in data:
        logging.error("Missing 'sender_address' in POST request body")
        return jsonify({"error": "Missing 'sender_address' in request body"}), 400

    sender_address_str = data['sender_address']
    logging.info(f"Received request to build TX for sender: {sender_address_str}")
    # You could also pass receiver and amount from frontend if needed
    # receiver_address_str = data.get('receiver_address', default_receiver)
    # send_amount_lovelace = data.get('amount', default_amount)


    # --- Build Transaction ---
    try:
        context = BlockFrostChainContext(BLOCKFROST_PROJECT_ID, base_url=NETWORK_URL, network=NETWORK)

        # Use the address received from the frontend
        sender_address_obj = Address.from_primitive(sender_address_str)
        receiver_address_obj = Address.from_primitive(receiver_address_str) # Use the fixed receiver or one from frontend data

        logging.info(f"Fetching UTXOs for: {sender_address_str}")
        # Pass the actual sender ADDRESS OBJECT to get_utxo might be cleaner
        # Or modify get_utxo to accept the string address
        input_tx_id_hex, input_tx_index, input_amount_lovelace = get_utxo(
            send_amount_lovelace, fee_lovelace, sender_address_str, context
        )

        if not input_tx_id_hex: # Check if get_utxo failed
             logging.error(f"Could not find suitable UTXO for {sender_address_str} to spend {send_amount_lovelace}")
             return jsonify({"error": "Insufficient funds or no suitable UTXO found"}), 400


        logging.info(f"Selected UTXO: {input_tx_id_hex}#{input_tx_index} ({input_amount_lovelace} lovelace)")

        # Create transaction input
        tx_id = TransactionId(bytes.fromhex(input_tx_id_hex))
        tx_in = TransactionInput(transaction_id=tx_id, index=input_tx_index)

        # Create transaction outputs
        output_send = TransactionOutput(
            address=receiver_address_obj,
            amount=Value(coin=send_amount_lovelace)
        )

        change_amount_lovelace = input_amount_lovelace - send_amount_lovelace - fee_lovelace

        outputs = [output_send] # Always include the main output
        if change_amount_lovelace < 0:
             logging.error(f"Insufficient balance: Input {input_amount_lovelace}, Send {send_amount_lovelace}, Fee {fee_lovelace}")
             # This check should ideally happen in get_utxo or just after
             return jsonify({"error": "Insufficient balance to cover amount and fees"}), 400
        elif change_amount_lovelace >= 1_000_000: # Only add change if it's >= 1 ADA (minUTXOValue approx) - ADJUST AS NEEDED
             output_change = TransactionOutput(
                 address=sender_address_obj, # Change goes back to the ACTUAL sender
                 amount=Value(coin=change_amount_lovelace)
             )
             outputs.append(output_change)
             logging.info(f"Change output added: {change_amount_lovelace} lovelace")
        elif change_amount_lovelace > 0:
            logging.warning(f"Change amount {change_amount_lovelace} is less than 1 ADA, adding to fee.")
            # Adjust fee if necessary, though often simpler to just require input > send + fee + minChange
            # For simplicity here, we just won't add the change output if it's too small
            # Note: This might lead to a slightly higher effective fee if change is dust.
            pass


        # Get current slot and calculate TTL
        try:
            current_slot = context.last_block_slot
            ttl = current_slot + 7200
            logging.info(f"Current slot: {current_slot}, TTL: {ttl}")
        except Exception as e:
            logging.error(f"Error fetching current slot from BlockFrost: {e}")
            # Fallback TTL - consider making this more robust or failing
            ttl = context.last_block_slot + 3600 # Shorter fallback?

        # Create transaction body
        tx_body = TransactionBody(
            inputs=[tx_in],
            outputs=outputs,
            fee=fee_lovelace,
            ttl=ttl,
            network=NETWORK # Explicitly set network if needed, though context should handle it
        )

        # Create the complete transaction (unsigned)
        transaction = Transaction(tx_body, TransactionWitnessSet())

        # Serialize transaction to CBOR hex
        cbor_hex = transaction.to_cbor_hex()

        logging.info("Successfully built unsigned transaction.")
        # print("\n--- Raw Transaction CBOR (Hex - Unsigned) ---")
        # print(cbor_hex)
        return jsonify({"cbor_hex": cbor_hex})

    except Exception as e:
        logging.error(f"Unexpected error building transaction: {e}", exc_info=True)
        return jsonify({"error": f"An unexpected error occurred: {e}"}), 500


# --- Minor improvements to get_utxo ---
def get_utxo(amount_to_spend, fee_lovelace, sender_address_str, context):
    total_needed = amount_to_spend + fee_lovelace
    logging.info(f"Searching for UTXO for address {sender_address_str} needing >= {total_needed} lovelace")
    try:
        address = Address.from_primitive(sender_address_str)
        utxos = context.utxos(str(address))
    except Exception as e:
         logging.error(f"Failed to fetch UTXOs or decode address {sender_address_str}: {e}")
         return None, None, None # Indicate failure

    if not utxos:
        logging.warning(f"No UTXOs found for address {sender_address_str}")
        return None, None, None

    best_utxo = None
    for i, utxo in enumerate(utxos):
        # Simple strategy: Find the smallest UTXO that covers the cost and has no native assets
        if not utxo.output.amount.multi_asset:
            utxo_value = utxo.output.amount.coin
            logging.debug(f"  Checking UTXO {i}: Value={utxo_value}, TxId={utxo.input.transaction_id.hex()}")
            if utxo_value >= total_needed:
                # This UTXO is sufficient
                if best_utxo is None or utxo_value < best_utxo.output.amount.coin:
                     best_utxo = utxo
                     logging.debug(f"    -> Found potential candidate UTXO {i}")

        else:
            logging.debug(f"  Skipping UTXO {i} (contains native assets): TxId={utxo.input.transaction_id.hex()}")


    if best_utxo:
        tx_id_hex = best_utxo.input.transaction_id.hex()
        index = best_utxo.input.index
        value = best_utxo.output.amount.coin
        logging.info(f"Selected UTXO: TxId={tx_id_hex}, Index={index}, Value={value}")
        return tx_id_hex, index, value
    else:
        logging.warning(f"No suitable UTXO found for {sender_address_str} needing {total_needed} lovelace (only ADA, >= needed amount).")
        return None, None, None


if __name__ == "__main__":
    # Use waitress or gunicorn in production instead of app.run(debug=True)
    app.run(debug=True, host='0.0.0.0', port=5000) # Listen on all interfaces if needed