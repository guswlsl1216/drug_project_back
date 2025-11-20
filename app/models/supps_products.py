from app import db # db 객체는 Flask 앱의 SQLAlchemy 인스턴스라고 가정

class SuppsProducts(db.Model):
    # 실제 DB 테이블 이름과 매핑
    __tablename__ = 'supps_products' 
    
    # supps_products 테이블 구조에 맞게 필드를 정의합니다.
    id = db.Column(db.Integer, primary_key=True) 
    # BSSH_NM (사업자명)
    BSSH_NM = db.Column(db.String(255)) 
    # PRDLST_NM (제품명)
    PRDLST_NM = db.Column(db.String(255))
    # RAWMTRL_NM (원료명) - 우리가 필요한 성분 정보
    RAWMTRL_NM = db.Column(db.Text)
    # 필요한 다른 컬럼들도 여기에 추가

    def __repr__(self):
        return f"<SuppsProducts {self.PRDLST_NM}>"