from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Menu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    harga = db.Column(db.Float, nullable=False)

class DetailPesanan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pesanan_id = db.Column(db.Integer, db.ForeignKey('pesanan.id'), nullable=False)
    menu_id = db.Column(db.Integer, db.ForeignKey('menu.id'), nullable=False)
    jumlah = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

    menu = db.relationship('Menu', backref='detail_pesanan')

class Pesanan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    waktu = db.Column(db.DateTime, default=datetime.now)
    total_harga = db.Column(db.Float, nullable=False)
    
    detail_pesanan = db.relationship('DetailPesanan', backref='pesanan', lazy='dynamic')