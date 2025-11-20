from ..extensions import db
from datetime import datetime
from sqlalchemy.dialects.mysql import LONGTEXT
from .auto import get_class

class Goods(db.Model):
  __tablename__ = 'goods'
  id = db.Column(db.Integer, primary_key=True)
  category = db.Column(db.String(200), nullable=False)
  classify = db.Column(db.String(200), nullable=False)
  price = db.Column(db.Integer, nullable=False)
  sell_count = db.Column(db.Integer, default=0)
  goods_name = db.Column(db.String(256), nullable=False)
  image_path = db.Column(db.String(512), nullable=False)
  goods_desc = db.Column(LONGTEXT, nullable=False)
  create_at = db.Column(db.DateTime, default = datetime.now)
  update_at = db.Column(db.DateTime, default = datetime.now, onupdate=datetime.now)
  stock = db.Column(db.Integer, nullable=False)
  is_active = db.Column(db.Boolean, default=True)
  user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
  user = db.relationship('User', back_populates='goods')
  reviews = db.relationship('Review', back_populates='goods', cascade='all, delete-orphan')
  carts = db.relationship('Cart', back_populates='goods', cascade='all, delete-orphan')
  favorites = db.relationship('Favorite', back_populates='goods', cascade='all, delete-orphan')
  supps_id = db.Column(db.Integer, nullable=True)
  qnas = db.relationship('QnA', back_populates='goods', cascade='all, delete-orphan')

  def __init__(self, category, classify, goods_name, goods_desc, price, stock,image_path=None, is_active=True, user_id=None):
    self.category = category
    self.classify = classify
    self.goods_name = goods_name
    self.goods_desc = goods_desc
    self.price = price
    self.stock = stock
    self.image_path = image_path
    self.is_active = is_active
    self.user_id = user_id

  def to_dict(self):
    from ..extensions import db as _db
    SP = get_class("supps_products")  # automap 클래스
    supp = None
    if SP is not None and self.supps_id is not None:
      supp = _db.session.get(SP, self.supps_id)
    

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
      'is_active' : self.is_active,
      'status_label': '판매중' if self.is_active else '비활성화됨',  # ← 라벨은 별도
      'supps_id':self.supps_id,
      'supps' : {
        'id' : self.supps_id,
        'PRDLST_NM': getattr(supp, "PRDLST_NM", None) if supp else None,
      }
    }
