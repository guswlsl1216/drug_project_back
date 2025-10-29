from datetime import datetime

from sqlalchemy import JSON
from ..extensions import db

class Routine_log(db.Model):
  __tablename__='routine_log'

  id = db.Column(db.Integer, primary_Key=True)
  routine_id = db.Column(db.Integer, db.ForeignKey('routine.id'), nullable=False)
  date = db.Column(db.Date, nullable=False)
  count = db.Column(db.Integer, default=1)
  performed_times = db.Column(JSON, nullable=False, default=lambda: []) #먹었는지 여부

  def getCount(self):
    return self.count
  
  def getPerformedTimes(self):
    return self.performed_times