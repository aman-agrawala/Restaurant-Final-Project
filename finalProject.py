from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem

app = Flask(__name__)

engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


#Fake Restaurants
restaurant = {'name': 'The CRUDdy Crab', 'id': '1'}

restaurants = [{'name': 'The CRUDdy Crab', 'id': '1'}, {'name':'Blue Burgers', 'id':'2'},{'name':'Taco Hut', 'id':'3'}]


#Fake Menu Items
items = [ {'name':'Cheese Pizza', 'description':'made with fresh cheese', 'price':'$5.99','course' :'Entree', 'id':'1'}, {'name':'Chocolate Cake','description':'made with Dutch Chocolate', 'price':'$3.99', 'course':'Dessert','id':'2'},{'name':'Caesar Salad', 'description':'with fresh organic vegetables','price':'$5.99', 'course':'Entree','id':'3'},{'name':'Iced Tea', 'description':'with lemon','price':'$.99', 'course':'Beverage','id':'4'},{'name':'Spinach Dip', 'description':'creamy dip with fresh spinach','price':'$1.99', 'course':'Appetizer','id':'5'} ]
item =  {'name':'Cheese Pizza','description':'made with fresh cheese','price':'$5.99','course' :'Entree'}


#JSON Requests
@app.route('/restaurants/JSON')
def showRestaurantsJSON():
    restaurants = session.query(Restaurant).all()
    return jsonify(Restaurants = [restaurant.serialize for restaurant in restaurants])

@app.route('/restaurant/<int:restaurant_id>/menu/JSON')
def showMenuJSON(restaurant_id):
    menu = session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
    return jsonify(MenuItems = [item.serialize for item in menu])

@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def itemJSON(restaurant_id,menu_id):
    item = session.query(MenuItem).filter_by(id = menu_id).one()
    return jsonify(Item = [item.serialize])

#Show all restaurants
@app.route('/restaurants')
@app.route('/')
def showRestaurants():
    #return 'This page will show all the restaurants'
    restaurants = session.query(Restaurant).all()
    return render_template('restaurants.html', restaurantList = restaurants)

@app.route('/restaurant/new', methods = ['GET', 'POST'])
def newRestaurant():
    #return "This page will be for making a new restaurant"
    if request.method == "POST":
        new = Restaurant(name = request.form['name'])
        session.add(new)
        session.commit()
        flash('New restaurant has been added')
        return redirect(url_for('showRestaurants'))
    else:
        print url_for('newRestaurant')
        return render_template('newRestaurant.html')

@app.route('/restaurant/<int:restaurant_id>/edit', methods = ['GET','POST'])
def editRestaurant(restaurant_id):
    #return "This page will be for editing the restaurant %s" %restaurant_id
    restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
    if request.method == 'POST':
        if request.form['name']:
            restaurant.name = request.form['name']
        session.add(restaurant)
        session.commit
        flash('Restaurant edited!')
        return redirect(url_for('showRestaurants'))
    else:
        return render_template('editRestaurant.html', restaurant = restaurant)

@app.route('/restaurant/<int:restaurant_id>/delete', methods = ['GET', 'POST'])
def deleteRestaurant(restaurant_id):
    #return 'This page will be for deleting restaurant %s' % restaurant_id
    restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
    if request.method == 'POST':
        session.delete(restaurant)
        session.commit()
        flash('Restaurant deleted!')
        return redirect(url_for('showRestaurants'))
    else:
        return render_template('deleteRestaurant.html', restaurant=restaurant)

@app.route('/restaurant/<int:restaurant_id>')
@app.route('/restaurant/<int:restaurant_id>/menu')
def showMenu(restaurant_id):
    menu = session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
    #print menu[5].restaurant_id
    #return 'This page is the menu for restaurant %s' %restaurant_id
    return render_template('menu.html', menu = menu)

@app.route('/restaurant/<int:restaurant_id>/new', methods = ['GET', 'POST'])
def newMenuItem(restaurant_id):
    #return 'This page is for making a new menu item for restaurant %s' % restaurant_id
    if request.method == 'POST':
        if request.form.get('name'):
            menu = MenuItem(name=request.form['name'])
            menu.restaurant_id = restaurant_id
            session.add(menu)
        else:
            flash('Menu must have a name!')
            return redirect(url_for('showMenu',restaurant_id= restaurant_id))
        print '2'
        if request.form.get('description'):
            menu.description = request.form['description']
            session.add(menu)
        if request.form.get('course'):
            menu.course = request.form['course']
            session.add(menu)
        if request.form.get('price'):
            menu.price = request.form['price']
            session.add(menu)
        session.commit()
        flash('Menu has been added!')
        return redirect(url_for('showMenu', restaurant_id = restaurant_id))
    else:
        return render_template('newMenuItem.html',restaurant_id = restaurant_id)

@app.route('/restaurant/<int:restaurant_id>/<int:menu_id>/edit', methods = ['GET','POST'])
def editMenuItem(restaurant_id, menu_id):
    #return 'This page is for editing menu item %s' % menu_id
    item = session.query(MenuItem).filter_by(id = menu_id).one()
    if request.method == 'POST':
        if request.form.get('name'):
            item.name = request.form['name']
            print request.form
            print 'name'
        if request.form.get('description'):
            item.description = request.form['description']
            print 'description'
        if request.form.get('course'):
            item.course = request.form['course']
            print 'course'
        if request.form.get('price'):
            item.price = request.form['price']
            print 'price'
        print 'logic completed'
        session.add(item)
        session.commit()
        flash('Menu item has been edited!')
        print 'test'
        print '\n'
        return redirect(url_for('showMenu', restaurant_id = restaurant_id))
    else:
        return render_template('editMenuItem.html', item = item)

@app.route('/restaurant/<int:restaurant_id>/<int:menu_id>/delete', methods = ['GET', "POST"])
def deleteMenuItem(restaurant_id,menu_id):
    #return 'This page is for deleting menu item %s' % menu_id
    item = session.query(MenuItem).filter_by(id = menu_id).one()
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        flash('Menu item deleted!')
        return redirect(url_for('showMenu', restaurant_id=restaurant_id))
    else:
        return render_template('deleteMenuItem.html',item = item)

if __name__ == '__main__':
    app.secret_key = 'key' #used to create sessions for users
    app.debug = True
    app.run(host='0.0.0.0', port=8000)