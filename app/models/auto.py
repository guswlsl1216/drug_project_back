from sqlalchemy.ext.automap import automap_base
from sqlalchemy import MetaData
from typing import Iterable, Optional
from ..extensions import db

metadata = MetaData()
Base = automap_base(metadata=metadata)

def prepare_automap(*, only: Optional[Iterable[str]] = None, schema: Optional[str] = None):
  """
  앱 컨텍스트 안에서 호출해야 함.
  only에 포함된 테이블만 반영(replect) 후 automap 준비
  """
  eng = db.engine

  only_seq = tuple(only) if only is not None else None

  metadata.reflect(bind=eng, only=only_seq, schema=schema)
  Base.prepare(autoload_with=eng)
  return Base

def get_class(table_name: str):
  return getattr(Base.classes, table_name)