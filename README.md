# Cardano Donation Platform

A transparent donation platform built on the Cardano blockchain. This platform allows users to create campaigns, accept donations in ADA, and track all transactions on the blockchain.

## Features

- Create donation campaigns with customizable goals and end dates
- Automatic wallet generation for each campaign
- Accept donations through Cardano blockchain transactions
- View all transaction history with blockchain verification
- Dashboard to manage campaigns and track donations
- Transparent fund usage tracking

## Prerequisites

- Python 3.8+
- Pip (Python package manager)
- Cardano node (for testing on the Cardano network)
- BlockFrost API key (for interacting with the Cardano blockchain)

## Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/cardano-donation-platform.git
cd cardano-donation-platform
```

2. Create a virtual environment:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```
pip install -r requirements.txt
```

4. Set up environment variables in `.env` file:
```
NETWORK=testnet
BLOCKFROST_PROJECT_ID=your_blockfrost_api_key
ETERNL_WALLET_PATH=path_to_your_eternl_wallet_export.json
```

5. Initialize the database:
```
python app.py
```

## Running the Application

1. Start the Flask development server:
```
python app.py
```

2. Open your browser and navigate to `http://localhost:5000`.

## Usage

### Creating a Campaign

1. Click on "Create Campaign" in the navigation menu.
2. Fill in the campaign details: title, description, goal amount, and end date.
3. Submit the form to create your campaign. A new Cardano wallet will be automatically generated for your campaign.

### Making a Donation

1. Browse campaigns on the home page.
2. Click on a campaign to view details.
3. Click the "Donate" button.
4. Choose whether to connect your wallet or make a manual transfer.
5. If using manual transfer, send ADA to the campaign's wallet address.

### Viewing Transactions

1. All transactions are visible on the campaign detail page.
2. For a complete transaction history, click on "Transactions" in the navigation menu.

## Testing on Testnet

This platform is configured to work with the Cardano testnet by default. You can obtain test ADA from the [Cardano testnet faucet](https://testnets.cardano.org/en/testnets/cardano/tools/faucet/).

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgements

- [Cardano](https://cardano.org/)
- [PyCardano](https://pycardano.readthedocs.io/)
- [BlockFrost](https://blockfrost.io/)
- [Flask](https://flask.palletsprojects.com/)
- [Bootstrap](https://getbootstrap.com/) 