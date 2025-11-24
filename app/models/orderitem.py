from ..extensions import db
from datetime import datetime

class OrderItem(db.Model):
  __tablename__ = 'orderitems'
  id = db.Column(db.Integer, primary_key=True)
  goods_id = db.Column(db.Integer, db.ForeignKey('goods.id'), nullable=False)
  goods = db.relationship('Goods', backref=db.backref('orderitems'))
  orders_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
  orders = db.relationship('Order', backref=db.backref('orderitems'))
  unit_price = db.Column(db.Integer , nullable = False)
  count = db.Column(db.Integer , nullable = False)
  subtotal = db.Column(db.Integer , nullable = False)
  create_at = db.Column(db.DateTime, default = datetime.now, nullable=False)
  cart_id = db.Column(db.Integer, db.ForeignKey('carts.id', ondelete='SET NULL'))
  carts = db.relationship('Cart', backref=db.backref('orderitems'))

  def __init__(self, unit_price, count, subtotal, goods_id=None, orders_id=None, cart_id=None):
    self.goods_id=goods_id
    self.orders_id=orders_id
    self.unit_price=unit_price
    self.count=count
    self.subtotal=subtotal
    self.cart_id=cart_id

  def to_dict(self):
    g = self.goods
    o = self.orders
    return {
      'id' : self.id,
      'goods' : {
        'id' : self.goods_id,
        'name': getattr(g, 'goods_name', None),
        'image': getattr(g, 'image_path', None),
        'price': self.unit_price,  # 주문 당시 가격
      },
      'orders' : {
        'id' : self.orders_id,
        'status': getattr(o, 'status', None),
        'receiver': getattr(o, 'receiver', None),
        'address': getattr(o, 'address', None),
        'address_detail': getattr(o, 'address_detail', None),
      },
      'count' : self.count,
      'subtotal' : self.subtotal,
      'create_at' : self.create_at,
      'cart_id' : self.cart_id
    }
