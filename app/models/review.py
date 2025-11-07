from ..extensions import db
from datetime import datetime

class Review(db.Model):
  __tablename__ = "reviews"
  id = db.Column(db.Integer, primary_key=True)
  review_image = db.Column(db.String(512))
  content = db.Column(db.Text(), nullable = False)
  create_at = db.Column(db.DateTime, default = datetime.now)
  stars = db.Column(db.Integer, nullable = False)
  goods_id = db.Column(db.Integer, db.ForeignKey('goods.id'), nullable=False)
  goods = db.relationship('Goods', back_populates='reviews')
  user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
  user = db.relationship('User', back_populates='reviews')

  def to_dict(self):
    return {
      'id' : self.id,
      'review_image' : self.review_image,
      'content' : self.content,
      'create_at' : self.create_at,
      'stars' : self.stars,
      'goods' : {
        'id' : self.goods_id,
        'goods_name' : self.goods.goods_name
      },
      'user' : {
        'id' : self.user_id,
        'nickname' : self.user.nickname
      }
    }
