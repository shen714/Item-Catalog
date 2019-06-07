from flask import Flask, render_template
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Item, Category, User

app = Flask(__name__)

# Connect database and create database session
engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Show the categories and the latest added items
@app.route('/')
@app.route('/category')
def show_categories_and_latest_items():
    categories = session.query(Category).all()
    items = session.query(Item).order_by(Item.item_id.desc())
    return render_template('categories.html', categories = categories)

# Show one category and the items in it
@app.route('/category/<int:category_id>')
@app.route('/category/<int:category_id>/items')
def show_one_category_and_items(category_id):
    #categories = session.query(Category).all()
    category = session.query(Category).filter_by(category_id=Category.category_id).one()
    category_name = category.name
    category_items = session.query(Item).filter_by(category_id = Item.category_id).all()
    return render_template('category.html', category_items = category_items, category_name = category_name)

# Show one item with detailed information
@app.route('/category/<int:category_id>/items/<int:item_id>')
def show_one_item(category_id, item_id):
    category = session.query(Category).filter_by(category_id=Category.category_id).one()
    item = session.query(Item).filter_by(item_id=item_id).one()
    return render_template('item.html', category=category, item=item)

'''
# Create an item
@app.route('/create')
def create_item():
    session.add(new_item)
    session.commit()
  '''  

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
