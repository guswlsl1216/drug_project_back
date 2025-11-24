from ..extensions import db
from datetime import datetime
from sqlalchemy import JSON

class Analyze_result(db.Model):
  __tablename__ = 'analyze_result'

  id = db.Column(db.Integer, primary_key=True)
  status = db.Column(db.Integer, nullable=False)
  meds = db.Column(JSON)
  supps = db.Column(JSON)
  analysis_date = db.Column(db.DateTime, default=datetime.now)
  duplicates = db.Column(JSON)
  interactions = db.Column(JSON)
  user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
  user = db.relationship('User', backref=db.backref('analyze_results'))
  analysis_uid = db.Column(db.String(64), unique=True, nullable=False)

  def to_dict(self):
    return {
      'id':self.id,
      'status':self.status,
      'meds':self.meds,
      'supps':self.supps,
      'analysis_date':self.analysis_date,
      'duplicates':self.duplicates,
      'interactions':self.interactions,
      'user_id':self.user_id,
      'analysis_uid':self.analysis_uid
    }