from pycardano import (
    BlockFrostChainContext,
    PaymentSigningKey,
    PaymentVerificationKey,
    Address,
    Network  # Import Network enum
)

# 1. Set up your Blockfrost project ID
BLOCKFROST_PROJECT_ID = "previewJhNPT5QxoI6h2TujleChtJ7qTxNZqSAZ"  # Replace this with your actual project ID
NETWORK = Network.TESTNET  # Use Network.MAINNET for mainnet

# 2. Create a Blockfrost chain context
context = BlockFrostChainContext(BLOCKFROST_PROJECT_ID, base_url="https://cardano-testnet.blockfrost.io/api/v0")

# 3. Load your signing and verification keys
skey = PaymentSigningKey.load("payment.skey")  # or generate using PaymentSigningKey.generate()
vkey = PaymentVerificationKey.load("payment.vkey")

# 4. Create wallet address
address = Address(vkey.hash(), network=NETWORK)

# Print wallet address
print("Wallet address:", address)

# 5. Fetch balance by summing UTXOs
utxos = context.utxos(address)
balance = sum(utxo.output.amount for utxo in utxos)
print("Balance:", balance)