from functools import wraps
from flask import Flask, render_template, request, redirect, jsonify, url_for, flash  # noqa
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Item, Category, User
from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog App"


# Connect database and create database session
engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in login_session:
            return redirect(url_for('showLogin'))
        return f(*args, **kwargs)
    return decorated_function


########################################
# Authentation
########################################
@app.route('/login')
def showLogin():
    state = ''.join(
        random.choice(
            string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# Connect
@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            'Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['email'] = data['email']

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    flash("you are now logged in as %s" % login_session['username'])
    print("done!")
    return output


# Disconnect
@app.route('/gdisconnect')
def gdisconnect():
        # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # If the given token was invalid notice the user.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/logout')
def logout():
    if 'username' in login_session:
        gdisconnect()
        flash("You have successfully been logged out.")
        return redirect(url_for('show_categories'))
    else:
        flash("You were not logged in")
        return redirect(url_for('show_categories'))


########################################
# User
########################################
# User Helper Functions
def createUser(login_session):
    newUser = User(
        user_name=login_session['username'], user_email=login_session['email'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(user_email=login_session['email'])
    .one()
    return user.user_id


def getUserInfo(this_user_id):
    user = session.query(User).filter_by(id=this_user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.user_id
    except:
        return None


########################################
# JSON
########################################
@app.route('/categories/JSON')
def categoriesJSON():
    categories = session.query(Category).all()
    return jsonify(categories=[category.serialize for category in categories])


@app.route('/categories/<int:chosen_category_id>/items/JSON')
def itemsJSON(chosen_category_id):
    items = session.query(Item).filter_by(category_id=chosen_category_id)
    .all()
    return jsonify(items=[item.serialize for item in items])


@app.route(
    '/categories/<int:chosen_category_id>/items/<int:chosen_item_id>/JSON')
def itemJSON(chosen_category_id, chosen_item_id):
    item = session.query(Item).filter_by(category_id=chosen_category_id,
                                         item_id=chosen_item_id).one()
    return jsonify(item=item.serialize)


########################################
# Read
########################################
# Show the categories and the latest added items
@app.route('/')
@app.route('/categories/')
def show_categories():
    all_categories = session.query(Category).all()
    latest_items = session.query(Item).order_by(Item.item_id.desc()).limit(10)
    if 'username' not in login_session:
        return render_template('public_categories.html',
                               categories=all_categories,
                               items=latest_items)
    else: 
        return render_template('categories.html', categories=all_categories,
                               items=latest_items)


# Show one category and the items in it
@app.route('/categories/<int:chosen_category_id>')
@app.route('/categories/<int:chosen_category_id>/items')
def show_category(chosen_category_id):
    all_categories = session.query(Category).all()
    chosen_category = session.query(Category).filter_by(
        category_id=chosen_category_id).one()
    chosen_category_name = chosen_category.category_name
    chosen_category_items = session.query(Item).filter_by(
        category_id=chosen_category_id).all()
    if 'username' not in login_session:
        return render_template(
            'public_category.html', categories=all_categories, 
            category=chosen_category,
            items=chosen_category_items,
            name=chosen_category_name)
    else:
        return render_template('category.html', categories=all_categories,
                               category=chosen_category,
                               items=chosen_category_items,
                               name=chosen_category_name)


# Show one item with detailed information
@app.route('/categories/<int:chosen_category_id>/items/<int:chosen_item_id>')
def show_one_item(chosen_category_id, chosen_item_id):
    category = session.query(Category).filter_by(
        category_id=chosen_category_id).one()
    item = session.query(Item).filter_by(
        item_id=chosen_item_id, category_id=chosen_category_id).one()
    if 'username' not in login_session:
        return render_template('public_item.html', item=item)
    else:
        return render_template('item.html', item=item)


########################################
# Create
########################################
# add a new catagory
@app.route('/categories/add/', methods=['GET', 'POST'])
def add_category():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        new_category = Category(
            category_name=request.form['name'],
            user_id=login_session['user_id'])
        session.add(new_category)
        session.commit()
        flash("new category created!")
        return redirect(url_for('show_categories'))
    else:
        return render_template('new_category.html')


# add a new item in a category
@app.route(
    '/categories/<int:this_category_id>/items/add/', methods=['GET', 'POST'])
def add_item(this_category_id):
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        new_item = Item(
            item_name=request.form['name'],
            item_description=request.form['description'],
            category_id=this_category_id, user_id=login_session['user_id'])
        session.add(new_item)
        session.commit()
        flash("new item created!")
        return redirect(url_for(
            'show_category', chosen_category_id=this_category_id))
    else:
        return render_template('new_item.html')


########################################
# Delete
########################################
# Delete the whole category
@app.route('/categories/<int:category_id>/delete/', methods=['GET', 'POST'])
def delete_category(category_id):
    if 'username' not in login_session:
        return redirect('/login')
    category = session.query(Category).filter_by(category_id=category_id).one()
    if category.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized"\
         "to edit this item. Please create your own item in order to edit.');"\
         "window.location = '/';}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(category)
        session.commit()
        flash("category deleted!")
        return redirect(url_for('show_categories'))
    else:
        return render_template('delete_category.html', category=category)


# Delete a item in a category
@app.route(
    '/categories/<int:category_id>/items/<int:item_id>/delete',
    methods=['GET', 'POST'])
def delete_item(category_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    item = session.query(Item).filter_by(
        item_id=item_id, category_id=category_id).one()
    if item.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized"\
         "to edit this item. Please create your own item in order to edit.');"\
         "window.location = '/';}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        flash("item deleted!")
        return redirect(url_for(
            'show_category', chosen_category_id=category_id))
    else:
        return render_template('delete_item.html', item=item)


########################################
# Edit
########################################
# Edit a category
@app.route(
    '/categories/<int:chosen_category_id>/edit/', methods=['GET', 'POST'])
def edit_category(chosen_category_id):
    if 'username' not in login_session:
        return redirect('/login')
    category_to_edit = session.query(Category).filter_by(
        category_id=chosen_category_id).one()
    if category_to_edit.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized"\
         "to edit this item. Please create your own item in order to edit.');"\
         "window.location = '/';}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            category_to_edit.category_name = request.form['name']
            flash("category edited!")
            return redirect(url_for('show_categories'))
    else:
        return render_template('edit_category.html', category=category_to_edit)


# Edit an item
@app.route(
    '/categories/<int:category_id>/items/<int:item_id>/edit',
    methods=['GET', 'POST'])
def edit_item(category_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    item = session.query(Item).filter_by(item_id=item_id).one()
    if item.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized"\
         "to edit this item. Please create your own item in order to edit.');"\
         "window.location = '/';}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            item.item_name = request.form['name']
        if request.form['description']:
            item.item_description = request.form['description']
        session.add(item)
        session.commit()
        flash("item edited!")
        return redirect(url_for(
            'show_category', chosen_category_id=category_id))
    else:
        return render_template('edit_item.html', item=item)

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
