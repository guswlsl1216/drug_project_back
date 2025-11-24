from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from ..extensions import db
from enum import Enum
from .qna import QnA
from .inquiry import Inquiry

class RoleEnum(str, Enum):
  ADMIN = 'admin'
  USER = 'user'

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
  age = db.Column(db.Integer, nullable=True)
  gender = db.Column(db.String(10), nullable=True)
  zipcode = db.Column(db.String(10), nullable=True)
  address = db.Column(db.String(200), nullable=True)
  detail = db.Column(db.String(200), nullable=True)
  role = db.Column(db.Enum(RoleEnum), default=RoleEnum.USER)
  tel = db.Column(db.String(30), nullable=True)
  point = db.Column(db.Integer, nullable=True, default=0)
  goods = db.relationship('Goods', back_populates='user')
  reviews = db.relationship('Review', back_populates='user', cascade='all, delete-orphan')
  carts = db.relationship('Cart', back_populates='user', cascade='all, delete-orphan')
  favorites = db.relationship('Favorite', back_populates='user', cascade='all, delete-orphan')
  inquiries = db.relationship('Inquiry', back_populates='user', foreign_keys='Inquiry.user_id', cascade='all, delete-orphan')
  qnas = db.relationship('QnA', back_populates='user', foreign_keys=[QnA.user_id], cascade='all, delete-orphan')
  qna_answers = db.relationship('QnA', back_populates='admin', foreign_keys=[QnA.admin_id])
  inquiry_answers = db.relationship(
    'Inquiry',
    back_populates='admin',
    foreign_keys=[Inquiry.admin_id]
  )

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
      'deleted_at':self.deleted_at,
      'age':self.age,
      'gender':self.gender,
      'zipcode':self.zipcode,
      'address':self.address,
      'detailed_address':self.detailed_address,
      'role':self.role,
      'point':self.point,
      'tel':self.tel,
    }