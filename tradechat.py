#Trade Chat is a simple web based chat room


# Using Flask and SQLite3
import os
import datetime as  dt
from sqlite3 import dbapi2 as sqlite3
from flask import Flask,request,session,g,redirect,url_for,abort, render_template ,\
    flash


#The whole app hinges on the Flask object , an instance of the main class of the framework.
#Inheriting the class with name lets the object inherit the application name (ie main) when the script is executed
#for example from a shell


#The application object from the main Flask class
app = Flask(__name__)
#time for some config , we need a database file name

app.config.update(dict(
    DATABASE=os.path.join(app.root_path,'tradechat.db'),
    #Set the sqlite3 database file ("TC database")
    DEBUG=True,
    SECRET_KEY='secret_key'
        #Im gonna place a secure key here for the actual application

))

app.config.from_envvar('TC_SETTINGS', silent=True)
    #This is so that if no config file exists it will keep quiet


# Once the path and filename of the database have been configured , we can make
# a function to connect to the database and returns the connection object

def connect_db():
    #"Connects to the TC Database"
    rv = sqlite3.connect(app.config[DATABASE])
    #sqlite3.connect requires a joint root_path and the database file
    rv.row_factory = sqlite3.Row
    return rv


#For effiiceincy with large numbers of users
#Im only instantiationg a new connection object
#If there is no connection stored in the g object already
# it would be inefficient to create a new connection object every time a db
# execution has to be made
def get_db():
    #Opens a new connection to the TC database
    if not hasattr(g, 'sqlite_db'):
        #Only open if it doesnt exists
        g.sqlite_db=connect_db()

    return g.sqlite_db


def init_db():
    # creates the TC database tables
    with app.app_context():
        #we are getting the connection object
        db = get_db()
        # here we are opening the database and abstracting it as f
        with app.open_resource('tables.sql', mode='r') as f:
            # this executes the script within the tables.sql fle and creates entries and user tables
            db.cursor().executescript(f.read)
        db.commit()


#The function close_db closes the database connection if there is one

def close_db():
    if  hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


#Once we have buit our db infrastructure we can begin to implement our core functionality of the app

@app.route('/')
def show_entries():
    #establishes a connection
    db = get_db()
    #specify db queries
    query = "select comment, user , time from comments order by id desc"
    #performs queries on the DB
    cursor = db.execute(query)
    #fetches all of the comments and stores it in a variable
    comments = cursor.fetchall()
    #puts it into a template-based rendering engine
    return render_template('show_entries.html',comments=comments )

@app.route('/register',methods=['GET','POST'])
def register():
    "Registers a new user in the TC database"
    error = None
    if request.method == "POST":
        db = get_db()
        if request.form["username"] == " or request.form['password'] == ":
            error = "Please provide both a username and a password"
            #both fields have to be non-empty

        else:
            db.execute("insert into users (name,password) values (?, ?)",
            [request.form['username'], request.form['password']])
            db.commit()
            session['logged_in'] = True
            #directly log in the new user
            flash('You were successfully registered')
            app.config.update(dict(USERNAME=request.form['username']))
            return redirect(url_for('show_entries'))
    return render_template('register.htnl', error=error)

@app.route('/login', methods=['GET','POST'])
def login():
 	error = None
 	if request.method=="POST":
 		db = get_db()
 		try:
 			query = 'select id from users where name = ? and password = ?'
 			#request.form takes a key which leads to the value in an element
 			db.execute(query,(request.form['username'],request.form['password'])).fetchone()[0]
 			#fails if record provided with username and password is not found
 			session['logged_in'] = True
 			flash('You are now logged in.')
 			app.config.update(dict(USERNAME=request.form['username']))
 			return redirect(url_for('show_entries'))
 		except:
 		    error = 'User not found or wrong password'
 		return render_template('login.html', error=error)


@app.route('/add', methods=['POST'])
def add():
	error = None
	#checks if they are logged in
	if not session.get('logged_in'):

		abort(401)
	#proceeds to perform procedure , get the db , execute a query then commit to db,
	# note changes on flash , then return the urlfor the showentries
	db = get_db()
	now = dt.datetime.now
	db.execute('insert into comments (comment, user, time) values (?, ?, ?)',
				[request.form['text'], app.config['USERNAME'], str(now)[:-7]])
	db.commit()
	flash('Comment succefulty added')
	return redirect(url_for('show_entries'))


@app.route('/logout')
def logout():
	session.pop('logged_in', None)
	flash('You were logged out')
	return redirect(url_for('show_entries'))




# if we want to make this standalone we need to add these lines to the application so that there
# is a server fired up  and that the application is served

#main routine

if __name__ == "__main__":
    init_db()
    app.run()
