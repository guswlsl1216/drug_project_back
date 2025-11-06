from datetime import datetime

from sqlalchemy import JSON
from ..extensions import db

class Routine_log(db.Model):
  __tablename__='routine_log'

  id = db.Column(db.Integer, primary_key=True)
  routine_id = db.Column(db.Integer, db.ForeignKey('routine.id', ondelete='CASCADE'), nullable=False)
  date = db.Column(db.Date, nullable=False)
  count = db.Column(db.Integer, default=1)
  performed_times = db.Column(JSON, default=lambda: [False, False, False]) #먹었는지 여부
  def to_dict(self):
    return self.date.strftime('%Y-%m-%d'), self.performed_times