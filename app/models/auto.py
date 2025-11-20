from sqlalchemy.ext.automap import automap_base
from typing import Iterable, Optional
from ..extensions import db

Base = automap_base()

_prepared = False 

def prepare_automap(*, only: Optional[Iterable[str]] = None, schema: Optional[str] = None):
    """
    앱 컨텍스트 안에서 호출해야 함.
    only에 포함된 테이블만 반영(reflect) 후 automap 준비
    """
    global _prepared
    if _prepared:
        return Base
    
    eng = db.engine

    Base.prepare(
        autoload_with=eng,
        schema=schema,
    )
    _prepared = True
    return Base

def get_class(table_name: str):
    """
    필요한 순간에 자동으로 prepare_automap 호출하고
    Base.classes 에서 테이블 이름에 해당하는 클래스를 가져온다.
    """
    if not _prepared:
        # automap으로 쓸 테이블만 지정 (goods는 절대 넣지 말기!!)
        prepare_automap()
    return getattr(Base.classes, table_name)
