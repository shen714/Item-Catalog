from flask import Flask, render_template, request, redirect, url_for
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Item, Category, User

app = Flask(__name__)

# Connect database and create database session
engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

########################################
# Read
########################################

# Show the categories and the latest added items
@app.route('/')
@app.route('/categories/')
def show_categories_and_latest_items():
    categories = session.query(Category).all()
    items = session.query(Item).order_by(Item.item_id.desc())
    return render_template('categories.html', categories = categories)

# Show one category and the items in it
@app.route('/categories/<int:category_id>')
@app.route('/categories/<int:category_id>/items')
def show_one_category_and_items(category_id):
    #categories = session.query(Category).all()
    category = session.query(Category).filter_by(category_id=Category.category_id).one()
    category_name = category.name
    category_items = session.query(Item).filter_by(category_id = Item.category_id).all()
    return render_template('category.html', category_items = category_items, category_name = category_name)

# Show one item with detailed information
@app.route('/categories/<int:category_id>/items/<int:item_id>')
def show_one_item(category_id, item_id):
    category = session.query(Category).filter_by(category_id=Category.category_id).one()
    item = session.query(Item).filter_by(item_id=item_id).one()
    return render_template('item.html', category=category, item=item)

########################################
# Create
########################################

# add a new catagory
@app.route('/categories/add/', methods=['GET', 'POST'])
def add_category():
    if request.method == 'POST':
        new_category = Category(category_name=request.form['name'])
        session.add(new_category)
        session.commit()
        return redirect(url_for('show_categories_and_latest_items'))
    else:
        return render_template('new_category.html')

# add a new item in a category
@app.route('/categories/<int:category_id>/add/', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        new_item = Item(item_name=request.form['name'], 
        item_description=request.form['descripton'], 
        category_id=request.form['category'])
        session.add(new_item)
        session.commit()
        return redirect(url_for('show_categories_and_latest_items'))
    else:
        return render_template('new_item.html')

########################################
# Delete
########################################
# Delete the whole category
@app.route('/categories/<int:category_id>/delete/', methods=['GET', 'POST'])
def delete_category(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        session.delete(category)
        session.commit()
        return redirect(url_for('show_categories_and_latest_items'))
    else:
        return render_template('delete_category.html', category=category)

# Delete a item in a category
@app.route('/categories/<int:category_id>/items/<int:item_id>/delete', methods=['GET', 'POST'])
def delete_item(category_id, item_id):
    item = session.query(Item).filter_by(item_id=item_id, category_id=category_id).one()
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        return redirect(url_for('show_categories_and_latest_items'))
    else:
        return render_template('delete_item.html', item=item)

########################################
# Edit
########################################

# Edit a category
@app.route('/categories/<int:category_id>/edit/', methods=['GET', 'POST'])
def edit_category(category_id):
    category = session.query(Category).filter_by(id=category_id).one()
    if request.method == 'POST':
        if request.form['name']:
            category.name = request.form['name']
            return redirect(url_for('show_categories_and_latest_items'))
    else:
        return render_template('edit_category.html', category=category)

# Edit an item
@app.route('/categories/<int:category_id>/items/<int:item_id>/edit', methods=['GET', 'POST'])
def edit_item(category_id, item_id):
    item = session.query(Item).filter_by(item_id=item_id).one()
    if request.method == 'POST':
        if request.form['name']:
            item_name=request.form['name'] 
        if request.form['description']:
            item_description=request.form['descripton']
        if request.form['category']:
            item_category=request.form['category']
        session.add(item)
        session.commit()
        return redirect(url_for('show_categories_and_latest_items'))
    else:
        return render_template('edit_item.html', item=item)





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
