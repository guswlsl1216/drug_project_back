from datetime import datetime
from ..extensions import db
from sqlalchemy import Enum as SAEnum
from enum import Enum  # Python Enum

class PointTypeEnum(str, Enum):
  EARN = "earn" # 적립
  USE = "use"  # 사용
  EXPIRE = "expire"  # 소멸
  ADJUST = "adjust" # 관리자 조정

class PointHistory(db.Model):
  __tablename__ = "point_history"
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

  amount = db.Column(db.Integer, nullable=False)   # + 적립 / - 사용
  balance_after = db.Column(db.Integer, nullable=False)  # 이 거래 이후의 최종 잔액

  type = db.Column(SAEnum(PointTypeEnum), nullable=False)

  # 주문과 연결 (주문으로 인해 적립/사용된 것)
  order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=True)

  description = db.Column(db.String(255), nullable=True)
  created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
  expire_at = db.Column(db.DateTime, nullable=True)
  routine_date = db.Column(db.Date, nullable=True)

  user = db.relationship("User", backref="point_histories")

  # Order와 양방향으로 잡고 싶다면
  order = db.relationship("Order", back_populates="point_histories")

  def to_dict(self):
    u = self.user
    o = self.order
    return {
      'id' : self.id,
      'user' : {
        'id' : self.user_id,
        'nickname': getattr(u, 'nickname', None),
      },
      "amount" : self.amount,
      "balance_after" : self.balance_after,
      "type": self.type.value if isinstance(self.type, PointTypeEnum) else self.type,
      "order" : {
        "id" : self.order_id,
        'used_points' : getattr(o, "used_points", None),
        'saved_points' : getattr(o, "saved_points", None)
      },
      "description" : self.description,
      "created_at" : self.created_at,
      "expire_at" : self.expire_at,
      "routine_date" : self.routine_date
    }