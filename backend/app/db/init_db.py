from app.db.session import Base, engine
from app import models  # noqa: F401 - register all model metadata

def init_db() -> None:
    Base.metadata.create_all(bind=engine)
