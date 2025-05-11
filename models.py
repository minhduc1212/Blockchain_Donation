from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wallet_address = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    campaigns = db.relationship('Campaign', backref='creator', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'wallet_address': self.wallet_address,
            'created_at': self.created_at.isoformat()
        }

class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    goal_amount = db.Column(db.BigInteger, nullable=False)  # in lovelace (1 ADA = 1,000,000 lovelace)
    current_amount = db.Column(db.BigInteger, default=0)
    wallet_address = db.Column(db.String(120), nullable=False)
    image_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    donations = db.relationship('Donation', backref='campaign', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'goal_amount': self.goal_amount,
            'current_amount': self.current_amount,
            'wallet_address': self.wallet_address,
            'image_url': self.image_url if self.image_url else "/static/assets/images/default_campaign.gif",
            'created_at': self.created_at.isoformat(),
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'creator': self.creator.wallet_address
        }

class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.BigInteger, nullable=False)  # in lovelace
    donor_address = db.Column(db.String(120), nullable=False)
    transaction_id = db.Column(db.String(120), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'amount': self.amount,
            'donor_address': self.donor_address,
            'transaction_id': self.transaction_id,
            'created_at': self.created_at.isoformat(),
            'campaign_id': self.campaign_id
        } 