from ..extensions import db
from datetime import datetime

class Favorite(db.Model):
  __tablename__ = 'favorites'
  id = db.Column(db.Integer, primary_key=True)
  goods_id = db.Column(db.Integer, db.ForeignKey('goods.id'), nullable=False)
  goods = db.relationship('Goods', back_populates='favorites')
  user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
  user = db.relationship('User', back_populates='favorites')
  create_at = db.Column(db.DateTime, default = datetime.now)

  def to_dict(self):
    return {
      'goods' : {
        'id' : self.goods_id,
        'goods_name': self.goods.goods_name,
        'goods_image' : self.goods.image_path
      },
      'user' : {
        'id' : self.user_id,
        'nickname' : self.user.nickname
      },
      'create_at' : self.create_at,
    }

  