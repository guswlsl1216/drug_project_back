from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db

class User(db.Model, UserMixin):
  __tablename__ = 'users'
  id = db.Column(db.Integer, primary_key=True) # 기본키, id(숫자)
  username = db.Column(db.String(30), unique=True, index= True, nullable=False)
  nickname = db.Column(db.String(30), unique=True, index=True, nullable=False)
  password_hash = db.Column(db.String(255), nullable=False)
  email = db.Column(db.String(100), unique=True, nullable=False)
  created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
  updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
  deleted_at = db.Column(db.DateTime, nullable=True)
  age = db.Column(db.String(5), nullable=True)
  gender = db.Column(db.String(10), nullable=True)
  address = db.Column(db.String(200), nullable=True)
  detailed_address = db.Column(db.String(200), nullable=True)

  def set_password(self, password): # 암호화
    self.password_hash = generate_password_hash(password)

  def check_password(self, password): # 암호화 된 비밀번호를 암호화 안 된 비밀번호와 일치하는지 
    return check_password_hash(self.password_hash, password)
  
  # 회원 탈퇴 시 복구 기간 설정
  def soft_delete(self):
    self.deleted_at = datetime.now() # 삭제한 날짜와 시간을 뽑아냄
    db.session.commit() # db에 저장

  # 탈퇴 한 유저이지만 복구 가능 기간이면 데이터가 남아있으므로 일반 조회나 로그인 등 API 응답에서 제외하기 위함
  @staticmethod
  def active_users():
    return User.query.filter(User.deleted_at.is_(None))
  
  # 복구 기간이 지나면 완전 삭제
  def hard_delete(self):
    db.session.delete(self) # DB에서 삭제
    db.session.commit() # 저장
  
  def to_dict(self): 
    return {
      'id':self.id,
      'username':self.username,
      'nickname':self.nickname,
      'email':self.email,
      'created_at':self.created_at,
      'updated_at':self.updated_at,
      'deleted_at':self.deleted_at
    }