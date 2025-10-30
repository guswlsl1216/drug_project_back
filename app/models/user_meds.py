from datetime import datetime

from sqlalchemy import JSON
from ..extensions import db

class User_meds(db.Model):
  __tablename__ ='user_meds'

  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
  image_url = db.Column(db.String(255), nullable=False)
  name = db.Column(db.String(255), nullable=False)
  created_at = db.Column(db.DateTime, default=datetime.now)
  update_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)


