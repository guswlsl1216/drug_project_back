from datetime import datetime

from sqlalchemy import JSON
from ..extensions import db

class Routine(db.Model):
  __tablename__='routine'

  id = db.Column(db.Integer, primary_key=True)
  drug_id = db.Column(db.Integer, nullable=False) #db.ForeignKey('drug.id')
  author_id = db.Column(db.Integer, nullable=False) #db.ForeignKey('users.id')
  # author=db.relationship('User',backref=db.backref('routine'))
  start_date = db.Column(db.Date, nullable=False)
  end_date = db.Column(db.Date, nullable=False)
  count = db.Column(db.Integer, nullable=False) 
  eattime = db.Column(JSON, nullable=False, default=lambda: []) #아침 점심 저녁
  
  def to_dict(self):
    return{
      'drugName':'오메가3', #test self.drug.drugName
      'drug_category':'영양제', #test self.drug.category
      'eattime':self.eattime.strftime('%H:%M') if self.eattime else None,
      'count':self.count,
      'start_date':self.start_date.strftime('%m-%d') if self.start_date else None,
      'end_date':self.end_date.strftime('%m-%d') if self.end_date else None
    }