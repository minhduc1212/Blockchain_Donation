import pycardano
from pycardano.crypto.bip32 import HDWallet, BIP32ED25519PrivateKey, BIP32ED25519PublicKey
from pycardano import Address, Network

# --- 1. Define Mnemonic Phrase ---
mnemonic_phrase = "right quiz dragon salmon tattoo fork world cannon length brother scale fiction fence sorry midnight truly tobacco thrive woman drum finger bubble hedgehog notice"
passphrase = ""  # Leave empty if no passphrase is used

# Validate the mnemonic
if not HDWallet.is_mnemonic(mnemonic_phrase):
    print("Error: Invalid mnemonic phrase.")
    exit()

# --- 2. Create Root HDWallet from Mnemonic ---
root_hdwallet = HDWallet.from_mnemonic(mnemonic_phrase, passphrase)

# --- 3. Derive Payment Key Pair ---
derivation_path = "m/1852'/1815'/0'/0/0"
child_hdwallet = root_hdwallet.derive_from_path(derivation_path)

# Extract keys
payment_signing_key = BIP32ED25519PrivateKey(
    private_key=child_hdwallet.xprivate_key,
    chain_code=child_hdwallet.chain_code
)

payment_verification_key = BIP32ED25519PublicKey.from_private_key(payment_signing_key)

# --- 4. Save Payment Keys to Files ---
print(payment_signing_key.private_key.hex())
with open("src/keys/payment.skey", "wb") as sk_file:
    sk_file.write(payment_signing_key.private_key)

print(payment_verification_key.public_key.hex())
with open("src/keys/payment.vkey", "wb") as vk_file:
    vk_file.write(payment_verification_key.public_key)

print("Payment signing key and verification key generated and saved successfully.")

# --- 3.1 Derive Stake Key Pair ---
stake_derivation_path = "m/1852'/1815'/0'/2/0"
stake_hdwallet = root_hdwallet.derive_from_path(stake_derivation_path)

# Extract stake keys
stake_signing_key = BIP32ED25519PrivateKey(
    private_key=stake_hdwallet.xprivate_key,
    chain_code=stake_hdwallet.chain_code
)

stake_verification_key = BIP32ED25519PublicKey.from_private_key(stake_signing_key)

# Save Stake Keys to Files
with open("src/keys/stake.skey", "wb") as sk_file:
    sk_file.write(stake_signing_key.private_key)

with open("src/keys/stake.vkey", "wb") as vk_file:
    vk_file.write(stake_verification_key.public_key)

print("Stake signing key and verification key generated and saved successfully.")

# --- 5. Generate Address ---
payment_address = Address(payment_verification_key.public_key.hex(), stake_verification_key, network=Network.TESTNET)

# Print the generated address
print(f"Generated payment address: {payment_address}")

# Save the address to a file
with open("src/keys/payment.addr", "w") as addr_file:
    addr_file.write(str(payment_address))

print("Payment address generated and saved successfully.")