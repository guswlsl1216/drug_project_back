from ..extensions import db

class Cart(db.Model):
  __tablename__ = 'carts'
  id = db.Column(db.Integer, primary_key=True)
  count = db.Column(db.Integer, nullable=False)
  goods_id = db.Column(db.Integer, db.ForeignKey('goods.id'), nullable=False)
  goods = db.relationship('Goods', back_populates='carts')
  user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
  user = db.relationship('User', back_populates='carts')
  orderitems = db.relationship('OrderItem', back_populates='carts')

  def to_dict(self):
    return {
      'id' : self.id,
      'count': self.count,
      'goods' : {
        'id' : self.goods_id,
        'goods_name': self.goods.goods_name,
        'goods_image' : self.goods.image_path
      },
      'user' : {
        'id' : self.user_id,
        'nickname' : self.user.nickname
      }
    }