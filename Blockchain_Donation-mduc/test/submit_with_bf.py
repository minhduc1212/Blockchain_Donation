import requests
import sys
import binascii

# Blockfrost API details
NETWORK = "preview"  # Or "preprod", "mainnet"
BASE_URL = f"https://cardano-{NETWORK}.blockfrost.io/api/v0"
SUBMIT_ENDPOINT = f"{BASE_URL}/tx/submit"
PROJECT_ID = "previewJhNPT5QxoI6h2TujleChtJ7qTxNZqSAZ"  # Replace with your valid Blockfrost API key

# Transaction data (CBOR format as a hexadecimal string)
hex_data = b"\x84\xa3\x00\xd9\x01\x02\x81\x82X \x00\x8fio\xaf\xf9\xc2\xcb\xda\xcb\xd2'\xf1\x8c\x9f\xcf26\xdb}\xcf\x03\xee\x03\xffT\xf0\xcf\\\xbew{\x01\x01\x82\x82X9\x00\xf8\x97}wF\xfa\xec\xc0k\x97\x89f&\xf1}\xbf\xabJq\xc0\x8f\x0f\xf7\xda*\xe4I\xa2\x06\xe7\xb9\xef\xf2\xa6\x00\x15!Z\xd8*2\xf8y\xc3\xecI5|K\x12s\x7f\x1a|\xaf%\x1a\x00\x1e\x84\x80\x82X9\x00\xf8\x97}wF\xfa\xec\xc0k\x97\x89f&\xf1}\xbf\xabJq\xc0\x8f\x0f\xf7\xda*\xe4I\xa2\x06\xe7\xb9\xef\xf2\xa6\x00\x15!Z\xd8*2\xf8y\xc3\xecI5|K\x12s\x7f\x1a|\xaf%\x1a\x04\xbeS\x1d\x02\x1a\x00\x02\x90\xcd\xa1\x00\xd9\x01\x02\x81\x82X \xd2\x17n\xafU\xf6=\x96 U\x0e_F,\xe6\x1e\x00\x81\x7f<\xb4B\x84\x1av\xf9,\xb1\xd3c>\xc6X@\x17L\xaa\x7f?\x19\x19&\x98\xf8!\x18,\r.\xb5\xfe\xff!o\xbe\x08\xb6O\xe5\xf4\x08\xe6\xc1\x0c\xf8\xbb\xc4\xf2\x9ec\xb0\xcf`-\xaeD\xaa[-\xd1\xfco\xa4\xa3\xd8\xccx#\x04\x07\xc6q)c\x85\xce\x08\x04\xf5\xf6"

def submit_transaction(api_url, project_id, hex_data):
    # Convert the hexadecimal string to binary data
    try:
        binary_data = binascii.unhexlify(hex_data)
    except binascii.Error as e:
        print(f"Error converting hex data to binary: {e}")
        sys.exit(1)

    # Prepare the headers
    headers = {
        "project_id": project_id,  # Correct header key
        "Content-Type": "application/cbor"
    }

    print(f"Submitting transaction to {api_url}...")

    try:
        # Make the POST request with binary data
        response = requests.post(
            api_url,
            headers=headers,
            data=binary_data,
            timeout=30  # Add a timeout
        )

        # Check for HTTP errors (4xx or 5xx)
        response.raise_for_status()

        # If successful, Blockfrost returns the transaction hash as plain text
        tx_hash = response.text
        print("\n--- Success! ---")
        print(f"Transaction submitted successfully.")
        print(f"Transaction Hash (TxId): {tx_hash}")
        return tx_hash

    except requests.exceptions.HTTPError as http_err:
        print(f"\n--- HTTP Error Occurred ---")
        print(f"Status Code: {http_err.response.status_code}")
        print(f"Reason: {http_err.response.reason}")
        print(f"Response Body: {http_err.response.text}")  # Blockfrost often provides error details here
    except requests.exceptions.ConnectionError as conn_err:
        print(f"\n--- Connection Error Occurred ---")
        print(f"Error: Could not connect to the Blockfrost API.")
        print(f"Details: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        print(f"\n--- Timeout Error Occurred ---")
        print(f"Error: The request timed out.")
        print(f"Details: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"\n--- An Unexpected Request Error Occurred ---")
        print(f"Error: {req_err}")
    except Exception as e:
        print(f"\n--- An Unexpected Error Occurred ---")
        print(f"Error: {e}")

    return None  # Indicate failure


# --- Main execution block ---
if __name__ == "__main__":
    # Call the function to submit the transaction
    submitted_tx_hash = submit_transaction(SUBMIT_ENDPOINT, PROJECT_ID, hex_data)

    if submitted_tx_hash:
        sys.exit(0)  # Exit with success code
    else:
        sys.exit(1)  # Exit with failure code