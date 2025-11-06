
from app import db 

class MedsProducts(db.Model):
    __tablename__ = 'meds_products' 
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    company = db.Column(db.String(255))