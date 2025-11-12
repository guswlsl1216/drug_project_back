from ..extensions import db
from datetime import datetime
from sqlalchemy import Enum

order_status_enum = Enum(
  'PENDING', 'PAID', 'CANCELLED', 'REFUNDED', name='order_status'
)

class Order(db.Model):
  __tablename__ = 'orders'
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
  user = db.relationship('User', backref=db.backref('orders'))
  total_price = db.Column(db.Integer, nullable = False)
  total_count = db.Column(db.Integer, nullable = False)
  status = db.Column(db.String(30), nullable=False)
  zipcode = db.Column(db.String(10), nullable=False)
  address = db.Column(db.String(255), nullable=False)
  address_detail = db.Column(db.String(255), nullable=False)
  receiver = db.Column(db.String(50), nullable=False)
  phone = db.Column(db.String(20), nullable=False)
  payments = db.relationship('Payment', back_populates='orders', cascade='all, delete-orphan')
  payment_at = db.Column(db.DateTime, nullable=True)
  update_at = db.Column(db.DateTime, nullable=True, onupdate=datetime.now)

  def to_dict(self):
    u = self.user
    return {
      'id' : self.id,
      'user' : {
        'id' : self.user_id,
        'nickname': getattr(u, 'nickname', None),
      },
      'total_price' : self.total_price,
      'total_count' : self.total_count,
      'status' : self.status,
      'zipcode' : self.zipcode,
      'address' : self.address,
      'address_detail' : self.address_detail,
      'receiver' : self.receiver,
      'phone' : self.phone,
      'payment_at' : self.payment_at,
      'update_at' : self.update_at
    }