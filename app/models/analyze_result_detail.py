from ..extensions import db
from sqlalchemy import JSON

class Analyze_result_detail(db.Model):
  __tablename__ = 'analyze_result_detail'

  analysis_id = db.Column(
    db.Integer,
    db.ForeignKey('analyze_result.id'),
    primary_key=True
  )
  duplicates = db.Column(JSON)
  interactions = db.Column(JSON)