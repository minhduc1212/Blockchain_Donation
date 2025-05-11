from flask import Flask, jsonify, render_template, request, redirect, url_for, send_from_directory
from pycardano import *
import os
from models import db, User, Campaign, Donation
import requests
import json
from datetime import datetime
import base64
from werkzeug.utils import secure_filename
import time
import shutil
import hashlib
from pycardano import Address, Network

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blockchain_donation.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
db.init_app(app)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global storage (in a real app, this would be a database)
campaigns = {}
donations = {}
uploaded_images = {}
# Add storage for community posts
community_posts = [
    {
        "id": 1,
        "title": "Help build a school in rural areas",
        "description": "We're looking to raise funds for building schools in underprivileged areas. Anyone interested in creating a campaign?",
        "author": "addr_test1...9a43d1",
        "created_at": "2023-05-15T10:30:00Z",
        "type": "campaign_idea"
    },
    {
        "id": 2,
        "title": "Clean water initiative",
        "description": "I have an idea for a campaign to fund clean water projects in developing countries. Looking for partners!",
        "author": "addr_test1...8b52e3",
        "created_at": "2023-05-10T08:15:00Z",
        "type": "campaign_idea"
    },
    {
        "id": 3,
        "title": "Animal shelter fundraising",
        "description": "Our local animal shelter needs funds for renovation and supplies. Anyone interested in helping create a campaign?",
        "author": "addr_test1...7c21f9",
        "created_at": "2023-05-05T14:45:00Z",
        "type": "campaign_idea"
    }
]
# Keep track of the next post ID
next_post_id = 4

# Global variable to store the CBOR hex address and sender address
cbor_hex_address = None
sender_address = None

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_utxo(amount_to_spend, fee_lovelace, sender_address, context):
    utxo_s = []
    first_valid_utxo_index = 0
    address = Address.from_primitive(sender_address)

    # Get all UTXOs
    utxos = context.utxos(str(address))
    for utxo in utxos:
        utxo_s.append(utxo)

    for i, utxo in enumerate(utxo_s):
        if not utxo.output.amount.multi_asset:  # Checks if the dictionary is empty
            print(f"  UTXO {i} contains only ADA.")

            # Check if the ADA amount is sufficient
            utxo_value = utxo.output.amount.coin
            print(f"  UTXO {i} value: {utxo_value} lovelace.")

            if utxo_value > amount_to_spend:
                first_valid_utxo_index = i  # Store the index
                break
            else:
                print(f"  UTXO {i} does not have enough ADA ({utxo_value} <= {amount_to_spend}).")
        else:
            print(f"  UTXO {i} contains multi-asset (native tokens). Skipping.")

    utxo_lines = str(utxo_s[first_valid_utxo_index]).splitlines()
    for line in utxo_lines:
        if "transaction_id" in line:
            # Extract the transaction hash
            transaction_id = line.split("'")[-2].strip()
            print("Transaction ID:", transaction_id)
        if "index" in line:
            # Extract the index and convert it to an integer
            index = int(line.split()[1].replace(",", "").strip())
            print("Index:", index)

    return transaction_id, index, utxo_value

def decode_address(cbor_hex_address):
    """
    Decode the CBOR hex address and extract the sender address.
    """
    try:
        cbor_hex_string_base = "84a3008182582042263fc151905c8da840a984e9e57b05ca0323842c615585168721fa6f6700aa01018282583900f8977d7746faecc06b97896626f17dbfab4a71c08f0ff7da2ae449a206e7b9eff2a60015215ad82a32f879c3ec49357c4b12737f1a7caf251a001e848082583900415df791b636a194b1a16a1620d14ead89f75a7e6967376766f229ea317b386a943d141589fc7ac8b8e53fecb0acfd499b20125859c322d21b0000000253c9aae0021a00029810a0f5f6"
        cbor_hex_string = cbor_hex_string_base.replace("00415df791b636a194b1a16a1620d14ead89f75a7e6967376766f229ea317b386a943d141589fc7ac8b8e53fecb0acfd499b20125859c322d2", cbor_hex_address)
        reconstructed_transaction = Transaction.from_cbor(cbor_hex_string)
        reconstructed_tx_body = reconstructed_transaction.transaction_body
        tx_body = str(reconstructed_tx_body.outputs[1]).splitlines()
        for line in tx_body:
            if "address" in line:
                sender_address = line.split(': ')[1].replace(',', '')
                print(f"Decoded Address: {sender_address}")
                return sender_address
    except Exception as e:
        print(f"Error decoding CBOR hex address: {e}")
        return None

def validate_address(address):
    """
    Validate a Cardano address format.
    Returns the address if valid, None otherwise.
    """
    try:
        # Attempt to create a pycardano Address object to validate the format
        Address.from_primitive(address)
        return address
    except Exception as e:
        print(f"Invalid address format: {e}")
        return None

# Configuration
BLOCKFROST_PROJECT_ID = "previewJhNPT5QxoI6h2TujleChtJ7qTxNZqSAZ"
NETWORK = "https://cardano-preview.blockfrost.io/api/"
# Transaction fee
fee_lovelace = 170000

# Create database tables
def create_tables():
    with app.app_context():
        db.create_all()

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/connect_wallet')
def connect_wallet():
    return render_template('connect_wallet.html')

@app.route('/new_campaign')
def new_campaign():
    return render_template('new_campaign.html')

@app.route('/my_campaigns')
def my_campaigns():
    return render_template('my_campaigns.html')

@app.route('/transaction')
def transaction():
    return render_template('transaction.html')

@app.route('/campaign/<int:id>')
def view_campaign(id):
    return render_template('campaign_details.html', campaign_id=id)

# API Endpoints for Campaigns
@app.route('/api/campaigns', methods=['GET'])
def get_campaigns():
    campaigns = Campaign.query.all()
    return jsonify([campaign.to_dict() for campaign in campaigns])

@app.route('/api/campaigns/<int:id>', methods=['GET'])
def get_campaign(id):
    campaign = Campaign.query.get_or_404(id)
    return jsonify(campaign.to_dict())

@app.route('/api/campaigns', methods=['POST'])
def create_campaign():
    data = request.get_json()
    
    # Check if the user exists, otherwise create a new user
    creator_address = data.get('creator_address')
    # Validate creator address
    if not validate_address(creator_address):
        return jsonify({"error": "Invalid creator wallet address format"}), 400
        
    user = User.query.filter_by(wallet_address=creator_address).first()
    if not user:
        user = User(wallet_address=creator_address)
        db.session.add(user)
        db.session.commit()
    
    # Handle image upload if provided
    image_url = None
    if data.get('image_data'):
        try:
            # Get base64 image data and file extension
            image_parts = data.get('image_data').split(';base64,')
            image_type_aux = image_parts[0].split('image/')
            image_type = image_type_aux[1]
            image_base64 = image_parts[1]
            
            # Generate unique filename
            filename = f"campaign_{datetime.now().strftime('%Y%m%d%H%M%S')}_{user.id}.{image_type}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Save the file
            with open(filepath, "wb") as f:
                f.write(base64.b64decode(image_base64))
                
            # Set the image URL relative to static folder
            image_url = f"/static/uploads/{filename}"
        except Exception as e:
            print(f"Error saving image: {e}")
    
    # Validate wallet address (which will be used as receiver for donations)
    wallet_address = data.get('wallet_address')
    if not validate_address(wallet_address):
        return jsonify({"error": "Invalid wallet address format"}), 400
    
    # Create a new campaign
    campaign = Campaign(
        title=data.get('title'),
        description=data.get('description'),
        goal_amount=data.get('goal_amount'),
        wallet_address=wallet_address,
        image_url=image_url or data.get('image_url', ''),
        end_date=datetime.fromisoformat(data.get('end_date')) if data.get('end_date') else None,
        creator_id=user.id
    )
    
    db.session.add(campaign)
    db.session.commit()
    
    return jsonify(campaign.to_dict()), 201

# API Endpoints for Donations
@app.route('/api/donations', methods=['POST'])
def add_donation():
    data = request.get_json()
    
    # Check if transaction already recorded
    existing_donation = Donation.query.filter_by(transaction_id=data.get('transaction_id')).first()
    if existing_donation:
        return jsonify({'error': 'Transaction already recorded'}), 400
    
    # Create a new donation
    donation = Donation(
        amount=data.get('amount'),
        donor_address=data.get('donor_address'),
        transaction_id=data.get('transaction_id'),
        campaign_id=data.get('campaign_id')
    )
    
    # Update campaign's current amount
    campaign = Campaign.query.get(data.get('campaign_id'))
    if not campaign:
        return jsonify({'error': 'Campaign not found'}), 404
    
    campaign.current_amount += data.get('amount')
    
    db.session.add(donation)
    db.session.commit()
    
    return jsonify(donation.to_dict()), 201

@app.route('/api/donations/campaign/<int:campaign_id>', methods=['GET'])
def get_campaign_donations(campaign_id):
    donations = Donation.query.filter_by(campaign_id=campaign_id).all()
    return jsonify([donation.to_dict() for donation in donations])

@app.route('/api/donations/user/<string:wallet_address>', methods=['GET'])
def get_user_donations(wallet_address):
    donations = Donation.query.filter_by(donor_address=wallet_address).all()
    return jsonify([donation.to_dict() for donation in donations])

@app.route("/set_unused_address", methods=["POST"])
def set_unused_address():
    """
    Endpoint to set the unused CBOR hex address and decode it.
    """
    global cbor_hex_address, sender_address
    try:
        data = request.get_json()
        cbor_hex_address = data.get("cbor_hex_address", "")
        if not cbor_hex_address:
            return jsonify({"error": "Missing CBOR hex address"}), 400

        sender_address = decode_address(cbor_hex_address)
        if not sender_address:
            return jsonify({"error": "Failed to decode CBOR hex address"}), 500

        return jsonify({"sender_address": sender_address}), 200
    except Exception as e:
        print(f"Error setting unused address: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/build_tx", methods=["POST"])
def build_transaction():
    try:
        # Get the amount to send from the request
        data = request.get_json()
        send_amount_lovelace = int(data.get("amount", 0))
        campaign_id = data.get("campaign_id")
        
        if send_amount_lovelace <= 0:
            return jsonify({"error": "Invalid amount"}), 400

        if not sender_address:
            return jsonify({"error": "Sender address is not set. Please connect the wallet and fetch the unused address first."}), 400
            
        # Validate sender address
        validated_sender_address = validate_address(sender_address)
        if not validated_sender_address:
            return jsonify({"error": "Invalid sender address format. Please reconnect your wallet."}), 400

        # Get the campaign's wallet address
        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            return jsonify({"error": "Campaign not found"}), 404
        
        # Always use the campaign wallet address as the receiver and validate it
        campaign_wallet_address = campaign.wallet_address
        if not campaign_wallet_address:
            return jsonify({"error": "Campaign wallet address is not set"}), 400
            
        # Validate receiver address
        validated_receiver_address = validate_address(campaign_wallet_address)
        if not validated_receiver_address:
            return jsonify({"error": "Invalid campaign wallet address format"}), 400
        
        print(f"Donation of {send_amount_lovelace} lovelace")
        print(f"From: {validated_sender_address}")
        print(f"To: {validated_receiver_address}")
        
        context = BlockFrostChainContext(BLOCKFROST_PROJECT_ID, base_url=NETWORK)
        input_tx_id_hex, input_tx_index, input_amount_lovelace = get_utxo(send_amount_lovelace, fee_lovelace, validated_sender_address, context)

        print(f"Transaction hash: {input_tx_id_hex}")
        print(f"tx_id: {input_tx_index}")
        print(f"Input amount: {input_amount_lovelace} lovelace")

        my_address = Address.from_primitive(validated_sender_address)
        recipient_address = Address.from_primitive(validated_receiver_address)

        # Create transaction input
        tx_id = TransactionId(bytes.fromhex(input_tx_id_hex))
        tx_in = TransactionInput(transaction_id=tx_id, index=input_tx_index)

        # Create transaction outputs
        output_send = TransactionOutput(
            address=recipient_address,
            amount=Value(coin=send_amount_lovelace)
        )

        change_amount_lovelace = input_amount_lovelace - send_amount_lovelace - fee_lovelace

        if change_amount_lovelace < 0:
            return jsonify({"error": "Insufficient balance to send the amount and cover fees."}), 400
        elif change_amount_lovelace == 0:
            print("Warning: No change will be returned.")
            outputs = [output_send]
        else:
            output_change = TransactionOutput(
                address=my_address,
                amount=Value(coin=change_amount_lovelace)
            )
            outputs = [output_send, output_change]
            print(f"Input: {input_amount_lovelace / 1_000_000} ADA")
            print(f"Sending: {send_amount_lovelace / 1_000_000} ADA")
            print(f"Fee: {fee_lovelace / 1_000_000} ADA")
            print(f"Change: {change_amount_lovelace / 1_000_000} ADA")

        # Get current slot and calculate TTL
        try:
            current_slot = context.last_block_slot
            ttl = current_slot + 7200  # TTL set to ~2 hours
            print(f"Current slot: {current_slot}")
            print(f"TTL (Invalid Hereafter): {ttl}")
        except Exception as e:
            print(f"Error fetching current slot from BlockFrost: {e}")
            ttl = 100_000_000  # Default TTL if unable to fetch

        # Create transaction body
        tx_body = TransactionBody(
            inputs=[tx_in],
            outputs=outputs,
            fee=fee_lovelace,
            ttl=ttl
        )

        # Create an empty witness set
        witness_set = TransactionWitnessSet()

        # Create the complete transaction
        transaction = Transaction(
            transaction_body=tx_body,
            transaction_witness_set=witness_set,
            auxiliary_data=None
        )

        # Serialize transaction to CBOR hex
        cbor_hex = transaction.to_cbor_hex()

        print("\n--- Raw Transaction CBOR (Hex - Unsigned) ---")
        print(cbor_hex)
        return jsonify({"cbor_hex": cbor_hex, "campaign_id": campaign_id})
    except Exception as e:
        print(f"Error building transaction: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/verify_transaction", methods=["POST"])
def verify_transaction():
    try:
        data = request.get_json()
        tx_hash = data.get("tx_hash")
        amount = int(data.get("amount", 0))
        campaign_id = data.get("campaign_id")
        donor_address = data.get("donor_address")
        
        if not tx_hash:
            return jsonify({"error": "Missing transaction hash"}), 400
            
        # Validate donor address
        if not validate_address(donor_address):
            return jsonify({"error": "Invalid donor address format"}), 400
        
        # Check if the transaction is already recorded in the database
        existing_donation = Donation.query.filter_by(transaction_id=tx_hash).first()
        if existing_donation:
            return jsonify({"success": False, "message": "Transaction already recorded"}), 400
        
        # Verify the transaction on the blockchain
        api_url = f"{NETWORK}v0/txs/{tx_hash}"
        headers = {"project_id": BLOCKFROST_PROJECT_ID}
        
        try:
            response = requests.get(api_url, headers=headers)
            response.raise_for_status()  # Raise an exception for non-200 status codes
            
            # Get transaction details to verify donation
            tx_details = response.json()
            print(f"Transaction verified on blockchain: {tx_hash}")
            
            # Record the donation
            donation = Donation(
                amount=amount,
                donor_address=donor_address,
                transaction_id=tx_hash,
                campaign_id=campaign_id
            )
            
            # Update campaign's current amount
            campaign = Campaign.query.get(campaign_id)
            if not campaign:
                return jsonify({"success": False, "message": "Campaign not found"}), 404
            
            campaign.current_amount += amount
            
            db.session.add(donation)
            db.session.commit()
            
            return jsonify({
                "success": True,
                "message": "Donation recorded successfully",
                "donation": donation.to_dict()
            }), 201
        except requests.exceptions.RequestException as e:
            return jsonify({
                "success": False,
                "message": f"Error verifying transaction: {str(e)}"
            }), 500
    
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error processing donation: {str(e)}"
        }), 500

@app.route('/community')
def community():
    return render_template('community.html')

@app.route('/api/community_posts', methods=['GET'])
def get_community_posts():
    # Return the community posts sorted by most recent first
    sorted_posts = sorted(community_posts, key=lambda x: x['created_at'], reverse=True)
    return jsonify(sorted_posts)

@app.route('/api/community_posts', methods=['POST'])
def create_community_post():
    global community_posts, next_post_id
    
    # Check if request has form data (for multipart/form-data with image) or JSON
    if request.content_type and 'multipart/form-data' in request.content_type:
        # Handle form data with potential image
        title = request.form.get('title')
        description = request.form.get('description')
        author = request.form.get('author')
        post_type = request.form.get('type')
        
        # Validate required fields
        if not title or not description or not author or not post_type:
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Handle image upload if present
        image_url = None
        if 'image' in request.files and request.files['image'].filename:
            image_file = request.files['image']
            
            # Validate file type
            if not allowed_file(image_file.filename):
                return jsonify({'error': 'Invalid file type. Only images are allowed.'}), 400
            
            # Create unique filename
            filename = secure_filename(image_file.filename)
            timestamp = int(time.time())
            unique_filename = f"{timestamp}_{filename}"
            
            # Save the file
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            image_file.save(file_path)
            
            # Create URL for the image
            image_url = f"/static/uploads/{unique_filename}"
    else:
        # Handle JSON data
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        # Validate required fields
        required_fields = ['title', 'description', 'author', 'type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
                
        title = data['title']
        description = data['description']
        author = data['author']
        post_type = data['type']
        image_url = None
    
    # Create the new post
    new_post = {
        'id': next_post_id,
        'title': title,
        'description': description,
        'author': author,
        'created_at': datetime.now().isoformat(),
        'type': post_type,
        'image_url': image_url
    }
    
    # Add to posts and increment ID counter
    community_posts.append(new_post)
    next_post_id += 1
    
    return jsonify(new_post), 201

@app.route('/api/user/<string:wallet_address>', methods=["GET"])
def get_user_by_wallet(wallet_address):
    user = User.query.filter_by(wallet_address=wallet_address).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user.to_dict())

@app.route("/api/user_campaigns/<string:wallet_address>", methods=["GET"])
def get_user_campaigns(wallet_address):
    user = User.query.filter_by(wallet_address=wallet_address).first()
    if not user:
        return jsonify([])
    campaigns = Campaign.query.filter_by(creator_id=user.id).all()
    return jsonify([campaign.to_dict() for campaign in campaigns])

@app.route('/api/campaigns/<int:id>', methods=['DELETE'])
def delete_campaign(id):
    # Get the campaign
    campaign = Campaign.query.get_or_404(id)
    
    # Get the requester's wallet address
    wallet_address = request.json.get('wallet_address')
    if not wallet_address:
        return jsonify({'error': 'Wallet address is required'}), 400
    
    # Find the user by wallet address
    user = User.query.filter_by(wallet_address=wallet_address).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if this user is the campaign creator
    if campaign.creator_id != user.id:
        return jsonify({'error': 'Unauthorized. Only the campaign creator can delete this campaign'}), 403
    
    # Delete the campaign's image if it exists
    if campaign.image_url and campaign.image_url.startswith('/static/uploads/'):
        try:
            image_path = os.path.join('static', campaign.image_url.split('/static/')[1])
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception as e:
            print(f"Error removing campaign image: {e}")
    
    # Delete related donations
    Donation.query.filter_by(campaign_id=id).delete()
    
    # Delete the campaign
    db.session.delete(campaign)
    db.session.commit()
    
    return jsonify({'message': 'Campaign deleted successfully'}), 200

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/wallet_info', methods=['POST'])
def get_wallet_info():
    try:
        data = request.get_json()
        wallet_address = data.get('wallet_address')
        
        if not wallet_address:
            return jsonify({"error": "Missing wallet address"}), 400
            
        # Validate wallet address
        if not validate_address(wallet_address):
            return jsonify({"error": "Invalid wallet address format"}), 400
            
        # For demonstration, we'll determine network from address format
        network = "Testnet" if "addr_test" in wallet_address else "Mainnet"
        
        # Get balance from Blockfrost API
        try:
            api_url = f"{NETWORK}v0/addresses/{wallet_address}"
            headers = {"project_id": BLOCKFROST_PROJECT_ID}
            response = requests.get(api_url, headers=headers)
            response.raise_for_status()
            
            address_data = response.json()
            balance_lovelace = int(address_data.get('amount', [{'quantity': '0'}])[0].get('quantity', '0'))
            balance_ada = balance_lovelace / 1000000
            
            # Get stake information if available
            stake_address = address_data.get('stake_address', 'Not staked')
            
            return jsonify({
                "address": wallet_address,
                "network": network,
                "balance_ada": balance_ada,
                "balance_lovelace": balance_lovelace,
                "stake_address": stake_address
            })
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching wallet info from Blockfrost: {e}")
            # Provide fallback response with network info but no balance
            return jsonify({
                "address": wallet_address,
                "network": network,
                "balance_ada": "Unknown",
                "balance_lovelace": 0,
                "error": "Could not fetch wallet balance"
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Add this new route for checking recent transactions
@app.route("/api/check_recent_transaction", methods=["POST"])
def check_recent_transaction():
    try:
        data = request.get_json()
        donor_address = data.get("donor_address")
        campaign_id = data.get("campaign_id")
        amount = int(data.get("amount", 0))
        
        # Get the campaign to find the recipient address
        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            return jsonify({"success": False, "message": "Campaign not found"}), 404
        
        # Validate addresses
        if not validate_address(donor_address):
            return jsonify({"success": False, "message": "Invalid donor address format"}), 400
        
        # Get recent blockchain transactions from BlockFrost
        api_url = f"{NETWORK}v0/addresses/{donor_address}/transactions?order=desc"
        headers = {"project_id": BLOCKFROST_PROJECT_ID}
        
        try:
            response = requests.get(api_url, headers=headers)
            response.raise_for_status()
            
            # Get the recent transactions (limit to checking the last 5)
            recent_txs = response.json()[:5]
            
            # Check each transaction for a match
            for tx in recent_txs:
                tx_id = tx.get("tx_hash")
                
                # Get transaction details
                tx_url = f"{NETWORK}v0/txs/{tx_id}/utxos"
                tx_response = requests.get(tx_url, headers=headers)
                tx_response.raise_for_status()
                tx_details = tx_response.json()
                
                # Check outputs to see if any match our campaign address and amount
                for output in tx_details.get("outputs", []):
                    # Check if the address matches the campaign wallet and amount matches what we expect
                    if output.get("address") == campaign.wallet_address:
                        # Check amount
                        for amount_item in output.get("amount", []):
                            if amount_item.get("unit") == "lovelace" and int(amount_item.get("quantity", 0)) == amount:
                                # Check if this transaction is already recorded
                                existing_donation = Donation.query.filter_by(transaction_id=tx_id).first()
                                if existing_donation:
                                    return jsonify({
                                        "success": True, 
                                        "message": "Transaction already recorded",
                                        "tx_hash": tx_id,
                                        "donation": existing_donation.to_dict()
                                    })
                                
                                # Record new donation
                                donation = Donation(
                                    amount=amount,
                                    donor_address=donor_address,
                                    transaction_id=tx_id,
                                    campaign_id=campaign_id
                                )
                                
                                # Update campaign amount
                                campaign.current_amount += amount
                                
                                # Save to database
                                db.session.add(donation)
                                db.session.commit()
                                
                                return jsonify({
                                    "success": True, 
                                    "message": "Transaction verified",
                                    "tx_hash": tx_id,
                                    "donation": donation.to_dict()
                                })
            
            # No matching transaction found
            return jsonify({"success": False, "message": "No matching transaction found"}), 404
                                
        except requests.exceptions.RequestException as e:
            return jsonify({
                "success": False,
                "message": f"Error checking blockchain: {str(e)}"
            }), 500
    except Exception as e:
        print(f"Error checking recent transaction: {e}")
        return jsonify({
            "success": False,
            "message": f"Error: {str(e)}"
        }), 500

if __name__ == "__main__":
    create_tables()
    app.run(debug=True)