from ..extensions import db


class User_meds(db.Model):
  __tablename__ ='user_meds'

  id = db.Column(db.Integer, primary_key=True)
  med_title = db.Column(db.String(50), nullable=False) 

  def to_dict(self):
      return{
        'id': self.id,
        'med_title' : self.med_title
      }