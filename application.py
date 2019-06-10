from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Item, Category, User
import sys

app = Flask(__name__)

# Connect database and create database session
engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

@app.route('/categories/JSON')
def categoriesJSON():
    categories = session.query(Category).all()
    return jsonify(categories=[category.serialize for category in categories])

@app.route('/categories/<int:chosen_category_id>/items/JSON')
def itemsJSON(chosen_category_id):
    items = session.query(Item).filter_by(category_id =chosen_category_id).all()
    return jsonify(items=[item.serialize for item in items])

@app.route('/categories/<int:chosen_category_id>/items/<int:chosen_item_id>/JSON')
def itemJSON(chosen_category_id, chosen_item_id):
    item = session.query(Item).filter_by(category_id=chosen_category_id, item_id = chosen_item_id).one()
    return jsonify(item=item.serialize)

########################################
# Read
########################################

# Show the categories and the latest added items
@app.route('/')
@app.route('/categories/')
def show_categories_and_latest_items():
    print("categories")
    all_categories = session.query(Category).all()
    latest_items = session.query(Item).order_by(Item.item_id.desc())
    return render_template('categories.html', categories = all_categories, items = latest_items)

# Show one category and the items in it
@app.route('/categories/<int:chosen_category_id>')
@app.route('/categories/<int:chosen_category_id>/items')
def show_one_category_and_items(chosen_category_id):
    all_categories = session.query(Category).all()
    chosen_category = session.query(Category).filter_by(category_id=chosen_category_id).one()
    chosen_category_name = chosen_category.category_name
    chosen_category_items = session.query(Item).filter_by(category_id =chosen_category_id).all()
    return render_template('category.html', categories=all_categories, category=chosen_category, items =chosen_category_items, name = chosen_category_name)

# Show one item with detailed information
@app.route('/categories/<int:chosen_category_id>/items/<int:chosen_item_id>')
def show_one_item(chosen_category_id, chosen_item_id):
    category = session.query(Category).filter_by(category_id=chosen_category_id).one()
    item = session.query(Item).filter_by(item_id=chosen_item_id, category_id=chosen_category_id).one()
    return render_template('item.html', item=item)

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
        flash("new category created!")
        return redirect(url_for('show_categories_and_latest_items'))
    else:
        return render_template('new_category.html')

# add a new item in a category
@app.route('/categories/<int:this_category_id>/items/add/', methods=['GET', 'POST'])
def add_item(this_category_id):
    if request.method == 'POST':
        new_item = Item(item_name=request.form['name'], 
        item_description=request.form['description'],
        category_id=this_category_id)
        session.add(new_item)
        session.commit()
        flash("new item created!")
        return redirect(url_for('show_one_category_and_items', chosen_category_id=this_category_id))
    else:
        return render_template('new_item.html')

########################################
# Delete
########################################
# Delete the whole category
@app.route('/categories/<int:category_id>/delete/', methods=['GET', 'POST'])
def delete_category(category_id):
    category = session.query(Category).filter_by(category_id=category_id).one()
    if request.method == 'POST':
        session.delete(category)
        session.commit()
        flash("category deleted!")
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
        flash("item deleted!")
        return redirect(url_for('show_one_category_and_items', chosen_category_id=category_id))
    else:
        return render_template('delete_item.html', item=item)

########################################
# Edit
########################################
# Edit a category
@app.route('/categories/<int:chosen_category_id>/edit/', methods=['GET', 'POST'])
def edit_category(chosen_category_id):
    category_to_edit = session.query(Category).filter_by(category_id=chosen_category_id).one()
    if request.method == 'POST':
        if request.form['name']:
            category_to_edit.category_name = request.form['name']
            flash("category edited!")
            return redirect(url_for('show_categories_and_latest_items'))
    else:
        return render_template('edit_category.html', category=category_to_edit)

# Edit an item
@app.route('/categories/<int:category_id>/items/<int:item_id>/edit', methods=['GET', 'POST'])
def edit_item(category_id, item_id):
    item = session.query(Item).filter_by(item_id=item_id).one()
    if request.method == 'POST':
        if request.form['name']:
            item.item_name=request.form['name'] 
        if request.form['description']:
            item.item_description=request.form['description']
        session.add(item)
        session.commit()
        flash("item edited!")
        return redirect(url_for('show_one_category_and_items', chosen_category_id=category_id))
    else:
        return render_template('edit_item.html', item=item)

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
