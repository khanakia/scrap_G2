from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, Float
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

meta = MetaData()
Base = declarative_base()

class Item(Base):
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    slug = Column(String)
    descr = Column(String)
    logo_url = Column(String)
    reviews_count = Column(Integer)
    ratings_count = Column(Integer)
    category_id = Column(Integer)
    website_link = Column(String)
    link_id = Column(Float)

class Price(Base):
    __tablename__ = 'prices'

    id = Column(Integer, primary_key=True)
    item_id = Column(String)
    name = Column(String)
    price = Column(Float)
    currency = Column(String)
    unit_text = Column(String)
    
class Link(Base):
    __tablename__ = 'links'

    id = Column(Integer, primary_key=True)
    url = Column(String)
    category_id = Column(Integer)

class Category(Base):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    parent_id = Column(Integer)
    slug = Column(String)
    ext_id = Column(Integer)
    ext_url = Column(String)


db_string = "postgresql+psycopg2://postgres:@127.0.0.1:5432/scrap_g2db"

# engine = create_engine("sqlite:///scrap.db")
engine = create_engine(db_string)
meta.create_all(engine)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

session = Session()


def get_connection():
    """
    Establishes a connection to the database using the engine object.

    Returns:
    A connection object.
    """
    conn = engine.connect()
    return conn
