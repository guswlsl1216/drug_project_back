from datetime import datetime
from ..extensions import db
from sqlalchemy import Enum
import os
from ..config import Config

class User_drugs(db.Model):
  __tablename__ ='user_drugs'

  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
  # name => ai가 인식한 name과 유저가 수정한 name 따로 관리 
  predicted_name = db.Column(db.String(255), nullable=True) # 모델이 예측한 약 이름 
  confirmed_name = db.Column(db.String(255), nullable=True) # 유저가 직접 입력한 약 이름 
  item_type = db.Column(Enum('medicine', 'supplement'), nullable=False) # 약 vs 영양제 구분 필드
  taken = db.Column(db.Boolean, nullable=False, default=False)  # 복용 완료 여부 
  created_at = db.Column(db.DateTime, default=datetime.now)
  updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

  # 디버깅용 쿼리 결과 확인할 때 호출됨 
  def __repr__(self):
    return f"<User_meds id={self.id}, user_id={self.user_id}, name={self.confirmed_name or self.predicted_name}>"
  