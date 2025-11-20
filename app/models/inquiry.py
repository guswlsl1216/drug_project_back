from datetime import datetime
from app import db

class Inquiry(db.Model):
  __tablename__ = 'inquiry'

  id = db.Column(db.Integer, primary_key=True)

  user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

  name = db.Column(db.String(100), nullable=False)
  email = db.Column(db.String(120), nullable=False)
  type = db.Column(db.String(50), nullable=False) # 문의 유형
  title = db.Column(db.String(255), nullable=False)
  content = db.Column(db.Text, nullable=False)

  status = db.Column(db.String(20), default='pending') # 문의상태(답변대기, 완료 등)
  created_at = db.Column(db.DateTime, default=datetime.now)

  user = db.relationship('User', back_populates='inquiries')

  def __repr__(self):
    return f'<Inquiry {self.id}: {self.title}>'
  
  def to_dict(self):
    return {
      "source": "inquiry",
      "id": self.id,

      "user": {
        "id": self.user_id,
        "nickname": self.user.nickname if self.user else None,
      },

      "name": self.name,
      "email": self.email,

      "type": self.type,
      "title": self.title,
      "content": self.content,

      "goods_id": None,
      "goods_name": None,
      "goods_image": None,

      "status": self.status,
      "status_label": "답변대기" if self.status == "pending" else "답변완료",

      "is_private": False,
      "visibility_label": "전체공개",

      "created_at": self.created_at
    }
