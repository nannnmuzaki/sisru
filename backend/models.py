from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Consultation(db.Model):
    __tablename__ = 'consultations'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    occupation = db.Column(db.String(100), nullable=False)
    sleep_duration = db.Column(db.Float, nullable=False)
    stress_level = db.Column(db.Integer, nullable=False)
    physical_activity = db.Column(db.Integer, nullable=False)
    bmi_category = db.Column(db.String(50), nullable=False)  # Normal, Overweight, Obese
    heart_rate = db.Column(db.Integer, nullable=False)
    sleep_disorder = db.Column(db.String(50), nullable=False)  # None, Insomnia, Sleep Apnea
    blood_pressure = db.Column(db.String(50), nullable=False)  # Normal, Elevated, High
    daily_steps = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    result = db.relationship('Result', backref='consultation', uselist=False, lazy=True)

class Result(db.Model):
    __tablename__ = 'results'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    consultation_id = db.Column(db.Integer, db.ForeignKey('consultations.id'), nullable=False)
    
    cf_class = db.Column(db.String(20), nullable=False)  # BAIK, CUKUP, BURUK
    cf_value = db.Column(db.Float, nullable=False)
    
    rf_class = db.Column(db.String(20), nullable=False)  # BAIK, CUKUP, BURUK
    rf_prob_baik = db.Column(db.Float, nullable=False)
    rf_prob_cukup = db.Column(db.Float, nullable=False)
    rf_prob_buruk = db.Column(db.Float, nullable=False)
    
    final_class = db.Column(db.String(20), nullable=False)  # BAIK, CUKUP, BURUK
    fired_rules = db.Column(db.Text, nullable=False)  # Stored as JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
