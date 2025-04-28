from pycardano import (
    Address,
    BlockFrostChainContext
)
 
context = BlockFrostChainContext(
    "previewJhNPT5QxoI6h2TujleChtJ7qTxNZqSAZ",
    base_url="https://cardano-preview.blockfrost.io/api/",
)

address = Address.from_primitive("")
                                    
try:
    utxos = context.utxos(address)
    print("UTXOs for the address:")
    for utxo in utxos:
        print(utxo) 

except Exception as e:
    print("Error fetching UTXOs or processing transaction:", e)