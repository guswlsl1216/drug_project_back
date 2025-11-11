from sqlalchemy.ext.automap import automap_base
from sqlalchemy import MetaData
from typing import Iterable, Optional
from ..extensions import db

metadata = MetaData()
Base = automap_base(metadata=metadata)

def prepare_automap(*, only: Optional[Iterable[str]] = None, schema: Optional[str] = None):
    """
    앱 컨텍스트 안에서 호출해야 함.
    only에 포함된 테이블만 반영(reflect) 후 automap 준비
    """
    eng = db.engine
    only_seq = tuple(only) if only is not None else None

    try:
        metadata.reflect(bind=eng, only=only_seq, schema=schema)
        Base.prepare(autoload_with=eng)
    except Exception as e:
        print(f"[WARN] automap reflect skipped (DB empty or tables missing): {e}")

    return Base

def get_class(table_name: str):
    # 존재하지 않는 클래스 요청 시 None 반환
    return getattr(Base.classes, table_name, None)
