from pycardano import (
    Address,
    BlockFrostChainContext
)


utxo_s = []
context = BlockFrostChainContext(
    "previewJhNPT5QxoI6h2TujleChtJ7qTxNZqSAZ",
    base_url="https://cardano-preview.blockfrost.io/api/",
)

address = Address.from_primitive("addr_test1qrufwlthgmawesrtj7ykvfh30kl6kjn3cz8sla769tjyngsxu7u7lu4xqq2jzkkc9ge0s7wra3yn2lztzfeh7xnu4ujs8l2avj")
                                    
try:
    utxos = context.utxos(address)
    print("UTXOs for the address:")
    for utxo in utxos:
        utxo_s.append(utxo)  

except Exception as e:
    print("Error fetching UTXOs or processing transaction:", e)

with open ("utxo.txt", "w") as f:
    f.write(str(utxo_s))

utxo_lines = str(utxo_s[0]).splitlines()

# Iterate through each line and process it
if "'multi_asset': {}" in str(utxo_s[0]):
    for line in utxo_lines:
        print(line)
else:
    print("UTXO contains multi_asset")
