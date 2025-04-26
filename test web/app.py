from flask import Flask, jsonify, render_template
from pycardano import *

app = Flask(__name__)

# Configuration
BLOCKFROST_PROJECT_ID = "previewJhNPT5QxoI6h2TujleChtJ7qTxNZqSAZ"
NETWORK = "https://cardano-preview.blockfrost.io/api/"

# Sender and Receiver Addresses
SENDER = "addr_test1qrufwlthgmawesrtj7ykvfh30kl6kjn3cz8sla769tjyngsxu7u7lu4xqq2jzkkc9ge0s7wra3yn2lztzfeh7xnu4ujs8l2avj"  # Eternl Address
RECEIVER = "addr_test1qrufwlthgmawesrtj7ykvfh30kl6kjn3cz8sla769tjyngsxu7u7lu4xqq2jzkkc9ge0s7wra3yn2lztzfeh7xnu4ujs8l2avj"  # Receiver Address
amount_to_send = 2_000_000


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/build_tx", methods=["GET"])
def build_transaction():
    context = BlockFrostChainContext(BLOCKFROST_PROJECT_ID, base_url=NETWORK)
    sender_address = Address.from_primitive(SENDER)
    receiver_address = Address.from_primitive(RECEIVER)

    builder = TransactionBuilder(context)
    builder.add_input_address(sender_address)
    builder.add_output(TransactionOutput(receiver_address, amount_to_send))  # 2 ADA

    unsigned_tx_body = builder.build()  # Build the transaction body
    unsigned_tx = Transaction(unsigned_tx_body, TransactionWitnessSet())  # Provide an empty TransactionWitnessSet
    cbor_hex = unsigned_tx.to_cbor().hex()  # Serialize the full transaction to CBOR

    return jsonify({"cbor_hex": cbor_hex})

if __name__ == "__main__":
    app.run(debug=True)
