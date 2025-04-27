with open("utxo.txt", "r") as f:
    lines = f.readlines()
    
    for line in lines:
        if "coin" in line:
            # Extract and print the UTXO value
            utxo_value = line.split()[1].replace(",", "")
            print("Value ",utxo_value)
        if "transaction_id" in line:
            # Extract and print the hex: 'transaction_id': TransactionId(hex='ba12b6df66856ee2c5908ea7cd1b8053ef77dbf756e234fe9e688b0b1d24c5d4'),
            hex = line.split("'")[-2]
            print("Hex ",hex)
        if "index" in line:
            # Extract and print the index: 'index': 0
            index = line.split()[1].replace(",", "")
            print("index ",index)
      

