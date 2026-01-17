from sqlalchemy import create_engine, Column, Integer, JSON
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./data/patchweb.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class ProtocolState(Base):
    __tablename__ = "protocol_state"

    id = Column(Integer, primary_key=True, index=True)
    data = Column(JSON, nullable=False)

def init_db():
    Base.metadata.create_all(bind=engine)
