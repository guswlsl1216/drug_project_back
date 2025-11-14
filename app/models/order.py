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
  items_total = db.Column(db.Integer, nullable=False)    # 상품 총합
  shipping_fee = db.Column(db.Integer, nullable=False, default=0)  # 배송비
  used_points = db.Column(db.Integer, default=0)     # 사용 포인트
  final_amount = db.Column(db.Integer, nullable=False)   # 최종 결제 금액
  total_count = db.Column(db.Integer, nullable = False)
  status = db.Column(order_status_enum, nullable=False)
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
      'items_total' : self.items_total,
      'shipping_fee' : self.shipping_fee,
      'used_points' : self.used_points,
      'final_amount' : self.final_amount,
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