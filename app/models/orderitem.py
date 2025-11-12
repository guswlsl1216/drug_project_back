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
  create_at = db.Column(db.DateTime, default = datetime.now)

  def to_dict(self):
    return {
      'id' : self.id,
      'goods' : {
        'id' : self.goods_id,
        'name': self.goods.goods_name,
        'image': self.goods.image_path,
        'price': self.unit_price,  # 주문 당시 가격
      },
      'orders' : {
        'id' : self.orders_id,
        'status': self.orders.status,
        'receiver': self.orders.receiver,
        'address': self.orders.address,
        'address_detail': self.orders.address_detail
      },
      'count' : self.count,
      'subtotal' : self.subtotal,
      'create_at' : self.create_at
    }
