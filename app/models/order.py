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
  saved_points = db.Column(db.Integer, default=0)     # 적립 예정 포인트
  final_amount = db.Column(db.Integer, nullable=False)   # 최종 결제 금액
  total_count = db.Column(db.Integer, nullable = False)
  status = db.Column(order_status_enum, nullable=False)
  zipcode = db.Column(db.String(10), nullable=False)
  address = db.Column(db.String(255), nullable=False)
  address_detail = db.Column(db.String(255), nullable=False)
  address_extra = db.Column(db.String(255), nullable=True)
  receiver = db.Column(db.String(50), nullable=False)
  phone = db.Column(db.String(20), nullable=False)
  delivery_message = db.Column(db.String(255), nullable=True)
  payments = db.relationship('Payment', back_populates='orders', cascade='all, delete-orphan')
  payment_at = db.Column(db.DateTime, default=datetime.now, nullable=True)
  update_at = db.Column(db.DateTime, nullable=True, onupdate=datetime.now)
  order_code = db.Column(db.String(50), nullable=False, unique=True) 
  # 이 주문으로 인한 포인트 변동 내역
  point_histories = db.relationship(
    "PointHistory",
    back_populates="order",
    cascade="all, delete-orphan"
  )

  def __init__(self, items_total, shipping_fee, used_points, saved_points, final_amount, total_count, status, zipcode, address, address_detail, address_extra, receiver,  phone, order_code, user_id=None, delivery_message=None):
    self.items_total=items_total
    self.shipping_fee=shipping_fee
    self.used_points=used_points
    self.saved_points=saved_points
    self.final_amount=final_amount
    self.total_count=total_count
    self.status=status
    self.zipcode=zipcode
    self.address=address
    self.address_detail=address_detail
    self.address_extra = address_extra
    self.receiver=receiver
    self.phone=phone
    self.delivery_message = delivery_message
    self.order_code=order_code
    self.user_id = user_id

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
      'saved_points' : self.saved_points,
      'final_amount' : self.final_amount,
      'total_count' : self.total_count,
      'status' : self.status,
      'zipcode' : self.zipcode,
      'address' : self.address,
      'address_detail' : self.address_detail,
      'address_extra': self.address_extra,
      'receiver' : self.receiver,
      'phone' : self.phone,
      'delivery_message': self.delivery_message,
      'payment_at' : self.payment_at,
      'update_at' : self.update_at,
      'order_code' : self.order_code,
      'items': [
        {
          'id': item.id,
          'goods_id': item.goods_id,
          'goods_name': getattr(item.goods, 'goods_name', None),
          'image': getattr(item.goods, 'image_path', None),
          'unit_price': item.unit_price,
          'count': item.count,
          'subtotal': item.subtotal,
        }
        for item in self.orderitems # type: ignore[attr-defined]
      ]
    }