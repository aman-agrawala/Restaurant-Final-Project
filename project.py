from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
app = Flask(__name__)

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem

#NEW IMPORTS FOR CREATING LOGIN_SESSIONS
from flask import session as login_session
import random, string

#IMPORTS FOR GCONNECT
from oauth2client.client import flow_from_clientsecrets # creates a flow object from client secret JSON
#file. This JSON formatted file stores your client ID, client secret and other OAuth 2 parameters 
from oauth2client.client import FlowExchangeError #use FlowExchangeError method if we run into an error 
#trying to exchange an authorization code for an access token
import httplib2 #comprehensive HTTP client library in Python
import json #JSON module provides an API for converting in memory Python objects to serialized 
#representation known as JSON (JavaScript Object notation)
from flask import make_response #converts the return value from a function into a real response object
#that we can send off to our client
import requests #requests is an Apache 2 license HTTP library in Python similar to urllib but with
# a few improvements

#Declare client id by referencing client_secrets file downloaded from google oauth servers. Needed for
#Gconnect
CLIENT_ID = json.loads(open('client_secrets.json','r').read())['web']['client_id']
APPLICATION_NAME = 'Restaurant Menu Application' #added in posted code but not in video

#Connect to Database and create database session
engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create a state token to prevent request forgery.
# Store it in the session for later validation.
@app.route('/login')
def showLogin():
  state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
  login_session['state'] = state
  #return "The current session state is %s" % login_session['state']
  print 'login'
  return render_template('login2.html', STATE=state)

@app.route('/gconnect', methods = ['POST'])
def gconnect():
  # check if the token created by you in login that was sent to the server is the same token that the
  # server is sending back. Helps ensure user is making our request. request.args.get examines the state
  # token passed in and compares it to the state of the login session. If they do not match then create
  # a response of an invalid state token and return the message to the client. No further authentication
  # will occur on server side if there is a mismatch between these state tokens.
  print 'gconnect'
  if request.args.get('state') != login_session['state']:
    response = make_response(json.dumps('Invalid state parameter'),401) # Here we send a response back
    # to the browser. json.dumps serializes the 'Invalid state parameter' into a JSON formatted stream. 
    # Error 401 is an access is denied due to invalid credentials.
    response.headers['Content-Type'] = 'application/json' # changing the content-type header. 
    return response # return the invalid state parameter response back to the browser

  # if the token is valid, then we get the one time code useing request.data
  code = request.data 

  # now try to use one time code and exchange it for credentials object which will contain access token for the 
  # server
  try:
    # Upgrade the authorization code into a credentials object 
    oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='') # Creates OAuth flow object
    # and adds client secret key information to it.
    oauth_flow.redirect_uri = 'postmessage' #here you specify with postmessage that this is the one time
    # code flow that the server will be sending off. This is generally set to 'postmessage' to match the
    # redirect_uri that the client specified.
    credentials = oauth_flow.step2_exchange(code) #initiate the exchange with the step2_exchange function
    # and passing in one time code as input. This step2_exchange function of the flow class exchanges
    # an authorization code for a credentials object 
  # if error happens along the way, then throw flow exchange error and send response as JSON object
  except FlowExchangeError:
    response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
    response.headers['Content-Type'] = 'application/json'
    return response

  # Now that we have the credentials object we will check and see if there is a valid access token inside
  # of it
  access_token = credentials.access_token # store the access token in credentials
  url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token) # by appending
  # token to the following google url, then the google API server can verify that this is a valid token
  # for use 

  # In the bottom two lines of code, we create a JSON get request containing the URL and access token.
  # Store the result of this request in a variable called result. 
  h = httplib2.Http()
  result = json.loads(h.request(url, "GET")[1])

  # If there was an error in the access token info, then we abort. If the following if statement isn't
  # true then we know that we have a working access token. But we still will need to make sure we have
  # the right access token 
  if result.get('error') is not None:
    response = make_response(json.dumps(result.get('error')), 500)
    response.headers['Content-Type'] = 'application/json'

  # Verify that the access token is used for the intended user.
  gplus_id = credentials.id_token['sub'] # grab the id of the token in the credentials object 
  if result['user_id'] != gplus_id: # compare the credentials object id to the id returned by the Google
  # API server. If the two IDs do not match, then I do not have the correct token and should return an 
  # error. 
    response = make_response(json.dumps("Token's user ID doesn't match given user ID."), 401)
    response.headers['Content-Type'] = 'application/json'
    return response

  # Check client IDs and if they do not match then the app is trying to use client ID that doesn't belong
  # to it and we should not allow for it. 
  if result['issued_to'] != CLIENT_ID:
    response = make_response(json.dumps("Token's client ID does not match app's"), 401)
    print "Token's client ID does not match app's."
    response.headers['Content-Type'] = 'application/json'
    return response

  #Check to see if the user is already logged in
  stored_credentials = login_session.get('credentials')
  stored_gplus_id = login_session.get('gplus_id')
  if stored_credentials is not None and gplus_id == stored_gplus_id:
    response = make_response(json.dumps('Current user is already connected'), 200) # this returns a 200 
    # which is a sueccessful authentication and doesn't reset the login session variables. 
    response.headers['Content-Type'] = 'application/json'

  # If the above if statements were true, then we have a valid access token and the user was able to 
  # successfully login to the server. Next we do the followin:

  #Store the access token in the session for later use.
  login_session['credentials'] = credentials
  login_session['gplus_id'] = gplus_id

  # Get user info through Google+ API
  userinfo_url = 'https://www.googleapis.com/oauth2/v1/userinfo' 
  params = {'access_token':credentials.access_token, 'alt': 'json'}
  answer = requests.get(userinfo_url,params=params) # send off message to Google API server with access
  # token requesting user info allowed by the token scope and then store it in an object called data. 
  data = json.loads(answer.text) 

  # Store the data that you're interested into login_session:
  login_session['username'] = data['name']
  login_session['picture'] = data['picture']
  login_session['email'] = data['email']

  # If the above worked then we should be able to create a response that knows the user's name and can
  # return their picture. You can also add a flash message to let user know that they are logged in
  output = ''
  output += '<h1>Welcome, '
  output += login_session['username']
  output += '!</h1>'
  output += '<img src ="'
  output += login_session['picture']
  output += ' "style = "width:300px; height: 300px; border-radius:150px; -webkit-border-radius: 150px; \
               -moz-border-radius: 150px;"> '
  flash('You are now logged in as %s' %login_session['username'])
  return output

#DISCONNECT - Revoke a current user's token and reset their login_session.
@app.route('/gdisconnect')
def gdisconnect():
  credentials = login_session.get('credentials')
  # If credentials field is empty than we don't have a record of the user so there is no one
  # to disconnect and we will return 401 error
  if credentials is None:
      response = make_response(json.dumps('Current user not connected.'), 401)
      response.headers['Content-Type'] = 'application/json'
      return response
  # Execute HTTP GET request to revoke current toke.
  access_token = credentials.access_token # Get the access token
  # Pass to google url to revoke tokens as
  url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
  h = httplib2.Http()
  result = h.request(url,'GET')[0] # Store googles response in object like so

  if result['status'] == '200':
    # Reset the user's session.
    del login_session['credentials']
    del login_session['gplus_id']
    del login_session['username']
    del login_session['email']
    del login_session['picture']

    response = make_response(json.dumps('Successfully disconnected.'),200)
    response.headers['Content-Type'] = 'application/json'
    return response
  else:
    # For whatever reason, the given token was invalid.
    response = make_response(json.dumps('Failed to revoke token for given user.'), 400)
    response.headers['Content-Type'] = 'application/json'
    return response
 

#JSON APIs to view Restaurant Information
@app.route('/restaurant/<int:restaurant_id>/menu/JSON')
def restaurantMenuJSON(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
    items = session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
    return jsonify(MenuItems=[i.serialize for i in items])


@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def menuItemJSON(restaurant_id, menu_id):
    Menu_Item = session.query(MenuItem).filter_by(id = menu_id).one()
    return jsonify(Menu_Item = Menu_Item.serialize)

@app.route('/restaurant/JSON')
def restaurantsJSON():
    restaurants = session.query(Restaurant).all()
    return jsonify(restaurants= [r.serialize for r in restaurants])


#Show all restaurants
@app.route('/')
@app.route('/restaurant/')
def showRestaurants():
  restaurants = session.query(Restaurant).order_by(asc(Restaurant.name))
  return render_template('restaurants.html', restaurants = restaurants)

#Create a new restaurant
@app.route('/restaurant/new/', methods=['GET','POST'])
def newRestaurant():
  # First verify if user is logged in
  if 'username' not in login_session:
    return redirect('/login')
  if request.method == 'POST':
      newRestaurant = Restaurant(name = request.form['name'])
      session.add(newRestaurant)
      flash('New Restaurant %s Successfully Created' % newRestaurant.name)
      session.commit()
      return redirect(url_for('showRestaurants'))
  else:
      return render_template('newRestaurant.html')

#Edit a restaurant
@app.route('/restaurant/<int:restaurant_id>/edit/', methods = ['GET', 'POST'])
def editRestaurant(restaurant_id):
  if 'username' not in login_session:
    return redirect('/login')
  editedRestaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
  if request.method == 'POST':
      if request.form['name']:
        editedRestaurant.name = request.form['name']
        flash('Restaurant Successfully Edited %s' % editedRestaurant.name)
        return redirect(url_for('showRestaurants'))
  else:
    return render_template('editRestaurant.html', restaurant = editedRestaurant)


#Delete a restaurant
@app.route('/restaurant/<int:restaurant_id>/delete/', methods = ['GET','POST'])
def deleteRestaurant(restaurant_id):
  if 'username' not in login_session:
    return redirect('/login')
  restaurantToDelete = session.query(Restaurant).filter_by(id = restaurant_id).one()
  if request.method == 'POST':
    session.delete(restaurantToDelete)
    flash('%s Successfully Deleted' % restaurantToDelete.name)
    session.commit()
    return redirect(url_for('showRestaurants', restaurant_id = restaurant_id))
  else:
    return render_template('deleteRestaurant.html',restaurant = restaurantToDelete)

#Show a restaurant menu
@app.route('/restaurant/<int:restaurant_id>/')
@app.route('/restaurant/<int:restaurant_id>/menu/')
def showMenu(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
    items = session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
    return render_template('menu.html', items = items, restaurant = restaurant)
     

#Create a new menu item
@app.route('/restaurant/<int:restaurant_id>/menu/new/',methods=['GET','POST'])
def newMenuItem(restaurant_id):
  if 'username' not in login_session:
    return redirect('/login')
  restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
  if request.method == 'POST':
      newItem = MenuItem(name = request.form['name'], description = request.form['description'], price = request.form['price'], course = request.form['course'], restaurant_id = restaurant_id)
      session.add(newItem)
      session.commit()
      flash('New Menu %s Item Successfully Created' % (newItem.name))
      return redirect(url_for('showMenu', restaurant_id = restaurant_id))
  else:
      return render_template('newmenuitem.html', restaurant_id = restaurant_id)

#Edit a menu item
@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/edit', methods=['GET','POST'])
def editMenuItem(restaurant_id, menu_id):
    if 'username' not in login_session:
      return redirect('/login')
    editedItem = session.query(MenuItem).filter_by(id = menu_id).one()
    restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['price']:
            editedItem.price = request.form['price']
        if request.form['course']:
            editedItem.course = request.form['course']
        session.add(editedItem)
        session.commit() 
        flash('Menu Item Successfully Edited')
        return redirect(url_for('showMenu', restaurant_id = restaurant_id))
    else:
        return render_template('editmenuitem.html', restaurant_id = restaurant_id, menu_id = menu_id, item = editedItem)


#Delete a menu item
@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/delete', methods = ['GET','POST'])
def deleteMenuItem(restaurant_id,menu_id):
    if 'username' not in login_session:
      return redirect('/login')  
    restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
    itemToDelete = session.query(MenuItem).filter_by(id = menu_id).one() 
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Menu Item Successfully Deleted')
        return redirect(url_for('showMenu', restaurant_id = restaurant_id))
    else:
        return render_template('deleteMenuItem.html', item = itemToDelete)




if __name__ == '__main__':
  app.secret_key = 'super_secret_key'
  app.debug = True
  app.run(host = '0.0.0.0', port = 5000)
