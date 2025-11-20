from datetime import datetime
from app import db

class QnA(db.Model):
  __tablename__ = 'qna'

  id = db.Column(db.Integer, primary_key=True)

  user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
  goods_id = db.Column(db.Integer, db.ForeignKey('goods.id'), nullable=False)

# 질문 필드
  question_title = db.Column(db.String(255), nullable=False)
  question_content = db.Column(db.Text, nullable=False)
  created_at = db.Column(db.DateTime, default=datetime.now)

# 답변 필드(관리자)
  admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # 관리자 ID
  answer_content = db.Column(db.Text, nullable=True) # 답변은 없을 수도 있음
  answered_at = db.Column(db.DateTime, nullable=True)


# 상태
  is_private = db.Column(db.Boolean, default=False) # 비밀글 여부
  status = db.Column(db.String(20), default='pending') # 처리 상태(pending, answered)

# 관계 설정
  user = db.relationship('User', back_populates='qnas', foreign_keys=[user_id]) # 질문 작성자
  goods = db.relationship('Goods', back_populates='qnas') # 소속 상품
  admin = db.relationship('User', foreign_keys=[admin_id], back_populates='qna_answers')

  def __repr__(self):
    return f'<QnA {self.id}: {self.question_title}>'
  
  def to_dict(self):
    return {
      "id": self.id,
      "user": {
        "id": self.user_id,
        "nickname": self.user.nickname
      },
      "goods" : {
        "id": self.goods_id,
        "name": self.goods.goods_name,
        "image": self.goods.image_path
      },
      "question_title" : self.question_title,
      "question_content" : self.question_content,
      "created_at" : self.created_at,
      "admin_id" : self.admin_id,
      "answer_content" : self.answer_content,
      "answered_at" : self.answered_at,
      "is_private" : self.is_private,
      "visibility_label": "비밀글" if self.is_private else "전체공개",  # ← 라벨은 별도
      "status" : self.status,
      "status_label": "답변대기" if self.status == "pending" else "답변완료",
    }
  
  def admin_to_dict(self):
    return {
      "source": "qna",  # 상품문의인지 구분 가능

      "id": self.id,

      # 공통 user 형태
      "user": {
        "id": self.user_id,
        "nickname": self.user.nickname
      },

      # 관리자 테이블 공통 필드
      "name": self.user.nickname,     # Inquiry 의 name 필드와 통일
      "email": self.user.email,       # 고객센터 문의와 맞추기

      "type": "상품문의",               # Inquiry 의 type 과 동일 포지션
      "question_title": self.question_title,
      "question_content": self.question_content,

      # 상품 정보
      "goods_id": self.goods_id,
      "goods_name": self.goods.goods_name if self.goods else "",
      "goods_image": self.goods.image_path if self.goods else "",

      # 상태
      "status": self.status,
      "status_label": "답변대기" if self.status == "pending" else "답변완료",

      "is_private": self.is_private,
      "visibility_label": "비밀글" if self.is_private else "전체공개",

      "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") 
                    if self.created_at else None,

      # 답변 정보
      "answer_content": self.answer_content,
      "answered_at": self.answered_at.strftime("%Y-%m-%d %H:%M:%S")
                      if self.answered_at else None,
    }
