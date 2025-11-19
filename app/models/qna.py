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