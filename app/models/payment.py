from ..extensions import db
from datetime import datetime
from sqlalchemy import Enum

class Payment(db.Model):
  __tablename__ = 'payments'
  id = db.Column(db.Integer, primary_key=True)
  orders_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
  orders = db.relationship('Order', back_populates='payments')
  user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
  user = db.relationship('User', backref=db.backref('payments'))
  paymentKey = db.Column(db.String(255), nullable=False)
  amount = db.Column(db.Integer, nullable = False)
  type = db.Column(db.String(50), nullable=False)
  method = db.Column(db.String(50), nullable=False)
  status = db.Column(db.String(50), nullable=False)
  pg_tid = db.Column(db.String(128), nullable=False)
  receipt_url = db.Column(db.String(512), nullable=True)
  paid_at = db.Column(db.DateTime, nullable=True)
  cancel_reason = db.Column(db.String(255), nullable=True)
  cancelled_at = db.Column(db.DateTime, nullable=True)
  created_at = db.Column(db.DateTime, default = datetime.now)

  def to_dict(self):
    order = self.orders 
    return {
      'id' : self.id,
      'orders_id': self.orders_id,
      'orders': {
        'status': getattr(order, 'status', None),
        'items_total': getattr(order, 'items_total', None),
        'shipping_fee': getattr(order, 'shipping_fee', None),
        'used_points': getattr(order, 'used_points', None),
        'final_amount': getattr(order, 'final_amount', None),
        'total_count': getattr(order, 'total_count', None),
        'receiver': getattr(order, 'receiver', None),
        'address': getattr(order, 'address', None),
        'address_detail': getattr(order, 'address_detail', None),
        'phone': getattr(order, 'phone', None),
        'payment_at': order.payment_at.isoformat() if getattr(order, 'payment_at', None) else None,
        'update_at': order.update_at.isoformat() if getattr(order, 'update_at', None) else None,
      } if order else None,
      'user_id' : self.user_id,
      'user_nickname': getattr(self.user, 'nickname', None),
      # 'paymentKey' : self.paymentKey,
      'amount' : self.amount,
      # 'type' : self.type,
      'method' : self.method,
      'status' : self.status,
      'pg_tid' : self.pg_tid,
      'receipt_url' : self.receipt_url,
      'paid_at' : self.paid_at,
      'created_at' : self.created_at,
      'cancel_reason' : self.cancel_reason,
      'cancelled_at' : self.cancelled_at
    }