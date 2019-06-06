from flask import Flask
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Item, Category, User

app = Flask(__name__)

# Connect database and create database session
engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Read
@app.route('/')
@app.route('/hello')
def HelloWorld():
    return "Hello World"

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
