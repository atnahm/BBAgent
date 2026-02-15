"""SQLite database for structured transaction data."""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from pathlib import Path

Base = declarative_base()

class Transaction(Base):
    """Transaction records from invoices."""
    __tablename__ = 'transactions'
    
    id = Column(Integer, primary_key=True)
    vendor_name = Column(String(200), nullable=False)
    gstin = Column(String(15), index=True)
    amount = Column(Float, nullable=False)
    invoice_number = Column(String(100), unique=True)
    invoice_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=False)
    status = Column(String(50), default='pending')  # pending, paid, overdue, escalated
    payment_date = Column(DateTime, nullable=True)
    
    # Legal flags
    legal_flag = Column(Boolean, default=False)
    days_overdue = Column(Integer, default=0)
    interest_amount = Column(Float, default=0.0)
    
    # Source tracking
    source_type = Column(String(20))  # image, voice, manual
    raw_data_path = Column(String(500))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    customer_id = Column(Integer, ForeignKey('customers.id'))
    customer = relationship("Customer", back_populates="transactions")
    communications = relationship("Communication", back_populates="transaction")

class Customer(Base):
    """Customer/Vendor master data."""
    __tablename__ = 'customers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    gstin = Column(String(15), unique=True, index=True)
    phone_number = Column(String(15))
    email = Column(String(100))
    
    # Relationship scoring
    total_transactions = Column(Integer, default=0)
    total_value = Column(Float, default=0.0)
    avg_payment_delay_days = Column(Float, default=0.0)
    risk_score = Column(Float, default=0.0)  # 0-100, higher = riskier
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="customer")

class Communication(Base):
    """WhatsApp message history."""
    __tablename__ = 'communications'
    
    id = Column(Integer, primary_key=True)
    transaction_id = Column(Integer, ForeignKey('transactions.id'))
    message_type = Column(String(50))  # friendly_reminder, formal_notice, legal_notice
    message_text = Column(Text)
    sent_at = Column(DateTime, nullable=True)
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    delivery_status = Column(String(50))  # pending_approval, sent, delivered, failed
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    transaction = relationship("Transaction", back_populates="communications")

class DatabaseManager:
    """Database connection manager."""
    
    def __init__(self, db_path: str):
        """Initialize database connection."""
        # Ensure directory exists
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def get_session(self):
        """Get database session."""
        return self.SessionLocal()
    
    def close(self):
        """Close database connection."""
        self.engine.dispose()
