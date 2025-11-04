from ..extensions import db
from sqlalchemy import JSON

class Analyze_result_detail(db.Model):
  __tablename__ = 'analyze_result_detail'

  id = db.Column(db.Integer, primary_key=True)
  analysis_id = db.Column(db.Integer, db.ForeignKey('analyze_result.id'))
  duplicates = db.Column(JSON)
  interactions = db.Column(JSON)