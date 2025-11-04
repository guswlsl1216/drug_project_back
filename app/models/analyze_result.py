from ..extensions import db
from datetime import datetime
from sqlalchemy import JSON

class Analyze_result(db.Model):
  __tablename__ = 'analyze_result'

  id = db.Column(db.Integer, primary_key=True)
  status = db.Column(db.Integer, nullable=False)
  meds = db.Column(JSON)
  supp_name = db.Column(db.String(255))
  supps = db.Column(JSON)
  analysis_date = db.Column(db.DateTime, default=datetime.now)
  user_id = db.Column(db.Integer, db.ForeignKey('users.id'))


# def to_dict(self):
#   return {
#     'id':self.id,
#     'status':self.status,
#     'meds':self.meds,
#     'supp_name':self.supp_name,
#     'supps':self.supps,
#     'analysis_date':self.analysis_date
#   }