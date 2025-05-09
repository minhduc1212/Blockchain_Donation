# 🌐 Blockchain Donation Platform

A decentralized application (DApp) that enables secure, transparent, and borderless donations using blockchain technology. Built to empower individuals and organizations to receive cryptocurrency donations with full transparency and traceability.

## 🚀 Features

- ✅ Create donation campaigns
- 💰 Accept donations in ADA (Cardano)
- 🔍 Track donations on the blockchain
- 📊 Real-time donation statistics
- 🌍 Global access with Web3 integration
- 🔒 Secure blockchain transactions

## 🛠️ Tech Stack

- **Backend:** Flask with PyCardano
- **Frontend:** HTML, CSS, JavaScript
- **Blockchain:** Cardano (Preview Testnet)
- **Database:** SQLite
- **Wallet Support:** Eternl

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Eternl Wallet browser extension (for Cardano)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/blockchain-donation-platform.git
   cd blockchain-donation-platform
   ```

2. Set up a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run the application:
   ```
   python app.py
   ```

5. Open your browser and navigate to:
   ```
   http://127.0.0.1:5000/
   ```

## 💡 How to Use

### Connect Your Wallet

1. Click on "Connect Wallet" in the navigation bar
2. Connect using Eternl wallet or manually enter your wallet address

### Create a Campaign

1. Click on "New Campaign" in the navigation bar
2. Fill in the campaign details (name, description, goal amount, and end date)
3. Submit the form to create your campaign

### Make a Donation

1. Browse the campaigns on the home page
2. Click on a campaign to view details
3. Enter the donation amount and click "Donate"
4. Complete the transaction using your Eternl wallet
5. Submit the transaction hash to verify your donation

### View Transactions

1. Click on "Transactions" in the navigation bar
2. View all your donation transactions
3. Click on transaction IDs to view details on the Cardano blockchain explorer

## 🧪 Testing

The application is configured to use the Cardano Preview Testnet. You'll need test ADA to make donations.

## 📚 API Documentation

The application provides the following API endpoints:

- `GET /api/campaigns` - List all campaigns
- `POST /api/campaigns` - Create a new campaign
- `GET /api/campaigns/<id>` - Get campaign details
- `POST /api/donations` - Record a donation
- `GET /api/donations/campaign/<id>` - Get donations for a campaign
- `GET /api/donations/user/<wallet_address>` - Get donations made by a user
- `POST /api/verify_transaction` - Verify a donation transaction

## 📷 Screenshots

![Home page](static/assets/screenshots/home.png)
![Campaign details](static/assets/screenshots/campaign.png)
![Make donation](static/assets/screenshots/donation.png)

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


