from typing import Dict, Any

from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.inspection import inspect


class Base(DeclarativeBase):
    def to_dict(self) -> Dict[str, Any]:
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}

