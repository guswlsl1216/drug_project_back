from ..extensions import db

class Test(db.Model):
    __tablename__ = "test"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<Test {self.id} {self.name}>"
