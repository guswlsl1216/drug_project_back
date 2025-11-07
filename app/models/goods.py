from ..extensions import db
from datetime import datetime

class Goods(db.Model):
  __tablename__ = 'goods'
  id = db.Column(db.Integer, primary_key=True)
  category = db.Column(db.String(200), nullable=False)
  classify = db.Column(db.String(200), nullable=False)
  price = db.Column(db.Integer, nullable=False)
  sell_count = db.Column(db.Integer, default=0)
  goods_name = db.Column(db.String(256), nullable=False)
  image_path = db.Column(db.String(512), nullable=False)
  goods_desc = db.Column(db.Text(), nullable=False)
  create_at = db.Column(db.DateTime, default = datetime.now)
  update_at = db.Column(db.DateTime, default = datetime.now, onupdate=datetime.now)
  stock = db.Column(db.Integer, nullable=False)
  is_active = db.Column(db.Boolean, default=True)
  user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
  user = db.relationship('User', back_populates='goods')
  reviews = db.relationship('Review', back_populates='goods', cascade='all, delete-orphan')
  carts = db.relationship('Cart', back_populates='goods', cascade='all, delete-orphan')
  favorites = db.relationship('Favorite', back_populates='goods', cascade='all, delete-orphan')

  def to_dict(self):
    return {
      'id' : self.id,
      'category' : self.category,
      'classify' : self.classify,
      'price' : self.price,
      'sell_count' : self.sell_count,
      'goods_name' : self.goods_name,
      'image_path' : self.image_path,
      'goods_desc' : self.goods_desc,
      'create_at' : self.create_at,
      'update_at' : self.update_at,
      'stock' : self.stock,
      'admin' : {
        'id' : self.user_id,
        'nickname' : self.user.nickname
      },
      'is_active' : '판매중' if self.is_active else '비활성화됨'
    }
