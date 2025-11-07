from ..extensions import db
from datetime import datetime

class Payment(db.Model):
  __tablename__ = 'payments'
  id = db.Column(db.Integer, primary_key=True)
  orders_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
  orders = db.relationship('Order', back_populates='payments')
  user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
  user = db.relationship('User', backref=db.backref('payments'))
  amount = db.Column(db.Integer, nullable = False)
  method = db.Column(db.String(30), nullable=False)
  status = db.Column(db.String(30), nullable=False)
  pg_tid = db.Column(db.String(128), nullable=False)
  receipt_url = db.Column(db.String(512), nullable=False)
  paid_at = db.Column(db.DateTime, default = datetime.now)
  cancel_reason = db.Column(db.String(255))
  cancelled_at = db.Column(db.DateTime, default = datetime.now)
  created_at = db.Column(db.DateTime, default = datetime.now)

  def to_dict(self):
    order = self.orders 
    return {
      'id' : self.id,
      'orders' : {
        'id' : self.orders_id,
        'status': order.status if order else None,
        'total_price': order.total_price if order else None,
        'total_count': order.total_count if order else None,
        'receiver': order.receiver if order else None,
        'address': order.address if order else None,
        'address_detail': order.address_detail if order else None,
        'phone': order.phone if order else None,
        'payment_at': order.payment_at if order else None,
        'update_at': order.update_at if order else None,
      },
      'user' : {
        'id' : self.user_id,
        'nickname' : self.user.nickname
      },
      'amount' : self.amount,
      'method' : self.method,
      'status' : self.status,
      'pg_tid' : self.pg_tid,
      'receipt_url' : self.receipt_url,
      'paid_at' : self.paid_at,
      'created_at' : self.created_at,
      'cancel_reason' : self.cancel_reason,
      'cancelled_at' : self.cancelled_at
    }