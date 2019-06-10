import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    user_id = Column(Integer, primary_key=True)
    user_name = Column(String(250), nullable=False)
    user_email = Column(String(250), nullable=False)

class Category(Base):
    __tablename__ = 'category'
    category_id = Column(Integer, primary_key=True)
    category_name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user.user_id'))
    user = relationship(User)
    
    @property
    def serialize(self):
        return {
            'name': self.category_name,
        }

class Item(Base):
    __tablename__ = 'item'
    item_name = Column(String(250), nullable=False)
    item_id = Column(Integer, primary_key=True)
    item_description = Column(String(250))
    category_id = Column(Integer, ForeignKey('category.category_id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.user_id'))
    user = relationship(User)

    @property
    def serialize(self):
        return{
            'name':self.item_name,
            'description':self.item_description,
        }

engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.create_all(engine)