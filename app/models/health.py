from ..extensions import db

class HealthProduct(db.Model):
  __tablename__ = "health_products"
  id = db.Column(db.BigInteger, primary_key=True)
  bssh_nm = db.Column(db.String(255))
  prdlst_nm = db.Column(db.String(255))
  pog_daycnt = db.Column(db.String(100))
  dispos = db.Column(db.String(255))
  ntk_mthd = db.Column(db.Text)
  primary_fnclty = db.Column(db.Text)
  iftkn_atnt_matr_cn = db.Column(db.Text)
  rawmtrl_nm = db.Column(db.Text)
  intake = db.Column(db.String(255))



