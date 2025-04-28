import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dotenv import load_dotenv
import json
import cardano_integration as ci

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///donation.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    wallet_address = db.Column(db.String(120), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    campaigns = db.relationship('Campaign', backref='creator', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    goal_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0.0)
    wallet_address = db.Column(db.String(120))
    wallet_mnemonic = db.Column(db.Text)  # In production, this should be encrypted
    start_date = db.Column(db.DateTime, default=datetime.now)
    end_date = db.Column(db.DateTime, nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    donations = db.relationship('Donation', backref='campaign', lazy=True)
    transactions = db.relationship('Transaction', backref='campaign', lazy=True)
    
    def __repr__(self):
        return f'<Campaign {self.title}>'
    
    @property
    def progress_percentage(self):
        if self.goal_amount == 0:
            return 0
        return min(int((self.current_amount / self.goal_amount) * 100), 100)
    
    @property
    def is_active(self):
        return datetime.now() <= self.end_date

class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    donor_name = db.Column(db.String(100))
    wallet_address = db.Column(db.String(120), nullable=False)
    transaction_hash = db.Column(db.String(120))
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    verified = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Donation {self.amount} to {self.campaign_id}>'

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_hash = db.Column(db.String(120), nullable=False, unique=True)
    transaction_type = db.Column(db.String(20), nullable=False)  # 'donation' or 'withdrawal'
    amount = db.Column(db.Float, nullable=False)
    from_address = db.Column(db.String(120), nullable=False)
    to_address = db.Column(db.String(120), nullable=False)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    description = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Transaction {self.transaction_hash}>'

# Initialize database tables
with app.app_context():
    db.create_all()
    
    # Create a default user if none exists
    if not User.query.filter_by(username='admin').first():
        admin_user = User(
            username='admin',
            email='admin@example.com',
            wallet_address='addr_test1qrv07lv7rqz0lq20zu9jmw36jyhvkjnl6qnn4sffd6jc24zk572mnwl7jrrrupz78g5gyfsu8xnghr4s4h24qg58h0us9rswxy'
        )
        db.session.add(admin_user)
        db.session.commit()

# Routes
@app.route('/')
def index():
    campaigns = Campaign.query.all()
    return render_template('index.html', campaigns=campaigns)

@app.route('/campaign/<int:campaign_id>')
def campaign_detail(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    donations = Donation.query.filter_by(campaign_id=campaign_id).all()
    transactions = Transaction.query.filter_by(campaign_id=campaign_id).all()
    
    # Check campaign balance on blockchain (if wallet address is available)
    if campaign.wallet_address:
        try:
            balance_info = ci.get_wallet_balance(campaign.wallet_address)
            if balance_info['success']:
                campaign.current_amount = balance_info['balance_ada']
                db.session.commit()
        except Exception as e:
            flash(f'Error updating balance: {str(e)}', 'warning')
    
    return render_template('campaign_detail.html', campaign=campaign, donations=donations, transactions=transactions)

@app.route('/create_campaign', methods=['GET', 'POST'])
def create_campaign():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        goal_amount = float(request.form['goal_amount'])
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
        
        # Generate a new campaign wallet address
        campaign_wallet = ci.create_campaign_address()
        
        if not campaign_wallet['success']:
            flash('Error creating campaign wallet. Please try again.', 'danger')
            return redirect(url_for('create_campaign'))
        
        # Create a new campaign
        campaign = Campaign(
            title=title,
            description=description,
            goal_amount=goal_amount,
            end_date=end_date,
            creator_id=1,  # Default to user 1 for now
            wallet_address=campaign_wallet['address'],
            wallet_mnemonic=campaign_wallet['mnemonic']  # In production, this should be encrypted
        )
        
        db.session.add(campaign)
        db.session.commit()
        
        flash('Campaign created successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('create_campaign.html')

@app.route('/donate/<int:campaign_id>', methods=['GET', 'POST'])
def donate(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    
    if request.method == 'POST':
        amount = float(request.form['amount'])
        donor_name = request.form['donor_name']
        wallet_address = request.form['wallet_address']
        
        # Create donation record
        donation = Donation(
            amount=amount,
            donor_name=donor_name,
            campaign_id=campaign_id,
            wallet_address=wallet_address,
            timestamp=datetime.now()
        )
        
        db.session.add(donation)
        db.session.commit()
        
        flash('Thank you for your donation! Please send the ADA from your wallet to complete the transaction.', 'success')
        return redirect(url_for('campaign_detail', campaign_id=campaign_id))
    
    return render_template('donate.html', campaign=campaign)

@app.route('/connect_wallet')
def connect_wallet():
    return render_template('connect_wallet.html')

@app.route('/api/store_wallet', methods=['POST'])
def store_wallet():
    wallet_data = request.json
    session['wallet_address'] = wallet_data.get('address')
    return jsonify({"success": True})

@app.route('/dashboard')
def dashboard():
    # In a real app, we would check user authentication
    user_campaigns = Campaign.query.filter_by(creator_id=1).all()
    return render_template('dashboard.html', campaigns=user_campaigns)

@app.route('/transaction_history')
def transaction_history():
    # Get all transactions
    transactions = Transaction.query.all()
    return render_template('transaction_history.html', transactions=transactions)

@app.route('/api/verify_transaction', methods=['POST'])
def verify_transaction():
    data = request.json
    tx_hash = data.get('transaction_hash')
    donation_id = data.get('donation_id')
    
    if not tx_hash or not donation_id:
        return jsonify({"success": False, "error": "Missing transaction hash or donation ID"})
    
    # Verify the transaction on the blockchain
    verification = ci.verify_transaction(tx_hash)
    
    if verification['success'] and verification['verified']:
        # Update the donation record
        donation = Donation.query.get(donation_id)
        if donation:
            donation.transaction_hash = tx_hash
            donation.verified = True
            
            # Update campaign amount
            campaign = Campaign.query.get(donation.campaign_id)
            if campaign:
                campaign.current_amount += donation.amount
            
            # Create transaction record
            transaction = Transaction(
                transaction_hash=tx_hash,
                transaction_type='donation',
                amount=donation.amount,
                from_address=donation.wallet_address,
                to_address=campaign.wallet_address,
                campaign_id=donation.campaign_id,
                timestamp=datetime.now(),
                description=f"Donation from {donation.donor_name or 'Anonymous'}"
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Donation not found"})
    else:
        return jsonify({"success": False, "error": "Transaction verification failed"})

@app.route('/api/withdraw', methods=['POST'])
def withdraw_funds():
    data = request.json
    campaign_id = data.get('campaign_id')
    amount = data.get('amount')
    to_address = data.get('to_address')
    description = data.get('description')
    
    if not campaign_id or not amount or not to_address or not description:
        return jsonify({"success": False, "error": "Missing required fields"})
    
    # In a real app, this would use PyCardano to create and submit a transaction
    # For this demo, we'll just create a transaction record
    
    # Mock transaction hash (in a real app, this would come from the blockchain)
    tx_hash = f"mock_withdrawal_hash_{datetime.now().timestamp()}"
    
    campaign = Campaign.query.get(campaign_id)
    if not campaign:
        return jsonify({"success": False, "error": "Campaign not found"})
    
    if campaign.current_amount < float(amount):
        return jsonify({"success": False, "error": "Insufficient funds"})
    
    transaction = Transaction(
        transaction_hash=tx_hash,
        transaction_type='withdrawal',
        amount=float(amount),
        from_address=campaign.wallet_address,
        to_address=to_address,
        campaign_id=campaign_id,
        description=description
    )
    
    campaign.current_amount -= float(amount)
    
    db.session.add(transaction)
    db.session.commit()
    
    return jsonify({"success": True, "transaction_hash": tx_hash})

@app.route('/api/update_balances')
def update_balances():
    campaigns = Campaign.query.all()
    updated = 0
    
    for campaign in campaigns:
        if campaign.wallet_address:
            try:
                balance_info = ci.get_wallet_balance(campaign.wallet_address)
                if balance_info['success']:
                    campaign.current_amount = balance_info['balance_ada']
                    updated += 1
            except Exception as e:
                continue
    
    db.session.commit()
    return jsonify({"success": True, "updated": updated})

@app.route('/api/load_eternl_wallet')
def load_eternl_wallet():
    # Load the Eternl wallet
    wallet_file = os.getenv('ETERNL_WALLET_PATH')
    if not wallet_file:
        return jsonify({"success": False, "error": "Eternl wallet path not configured"})
    
    wallet_info = ci.load_eternl_wallet(wallet_file)
    return jsonify(wallet_info)

@app.route('/api/build_donation_tx', methods=['POST'])
def build_donation_tx():
    """Build a donation transaction for signing with Eternl wallet"""
    data = request.json
    campaign_id = data.get('campaign_id')
    amount = data.get('amount')  # in ADA
    sender_address = data.get('sender_address')
    
    if not campaign_id or not amount or not sender_address:
        return jsonify({"success": False, "error": "Missing required fields"})
    
    try:
        # Get campaign information
        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            return jsonify({"success": False, "error": "Campaign not found"})
        
        # Convert ADA to Lovelace (1 ADA = 1,000,000 Lovelace)
        amount_lovelace = int(float(amount) * 1000000)
        
        # Build the transaction using cardano_integration
        tx_result = ci.build_donation_transaction(
            sender_address=sender_address,
            receiver_address=campaign.wallet_address,
            amount_lovelace=amount_lovelace
        )
        
        if not tx_result['success']:
            return jsonify({"success": False, "error": tx_result['error']})
        
        return jsonify({
            "success": True,
            "cbor_hex": tx_result['cbor_hex'],
            "campaign_id": campaign_id,
            "campaign_title": campaign.title,
            "amount": amount,
            "receiver_address": campaign.wallet_address
        })
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/api/confirm_donation', methods=['POST'])
def confirm_donation():
    """Confirm a donation after wallet submission"""
    data = request.json
    campaign_id = data.get('campaign_id')
    amount = data.get('amount')  # in ADA
    donor_name = data.get('donor_name', 'Anonymous')
    wallet_address = data.get('wallet_address')
    transaction_hash = data.get('transaction_hash')
    
    if not campaign_id or not amount or not wallet_address or not transaction_hash:
        return jsonify({"success": False, "error": "Missing required fields"})
    
    try:
        # Verify the transaction first
        verification = ci.verify_transaction(transaction_hash)
        
        if not verification['success'] or not verification['verified']:
            return jsonify({
                "success": False, 
                "error": "Transaction could not be verified on the blockchain"
            })
        
        # Create new donation
        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            return jsonify({"success": False, "error": "Campaign not found"})
        
        # Create donation record
        donation = Donation(
            amount=float(amount),
            donor_name=donor_name,
            campaign_id=campaign_id,
            wallet_address=wallet_address,
            transaction_hash=transaction_hash,
            verified=True,
            timestamp=datetime.now()
        )
        
        # Update campaign balance
        campaign.current_amount += float(amount)
        
        # Create transaction record
        transaction = Transaction(
            transaction_hash=transaction_hash,
            transaction_type='donation',
            amount=float(amount),
            from_address=wallet_address,
            to_address=campaign.wallet_address,
            campaign_id=campaign_id,
            timestamp=datetime.now(),
            description=f"Donation from {donor_name}"
        )
        
        db.session.add(donation)
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({"success": True, "donation_id": donation.id})
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == '__main__':
    app.run(debug=True) 