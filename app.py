from flask import Flask, render_template, redirect, url_for, request, session, flash
from pymongo import MongoClient
import bcrypt
from bson.objectid import ObjectId
from functools import wraps
from datetime import datetime, timedelta



app = Flask(__name__)
app.secret_key = 'your_secret_key_12345'

# MongoDB client setup
client = MongoClient('mongodb+srv://likithsai007:likithsai007@cluster0.rrgi4.mongodb.net/Library_Management_System')
db = client['Library_database']
users = db['users']
books = db['books']
members = db['members']
borrow_records = db['borrow_records']

FINE_RATE = 1  # Fine rate per day in dollars

# Decorator for librarian-only access
def librarian_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'librarian':
            flash("Access denied: Librarians only")
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    if 'username' in session:
        return render_template('home.html')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = users.find_one({'username': username})
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            session['username'] = username
            session['role'] = user.get('role', 'user')  # Store user's role in session
            return redirect(url_for('home'))
        
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']  # Get the selected role
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Insert the user with the selected role
        users.insert_one({
            'username': username,
            'password': hashed,
            'role': role  # Store role in database
        })
        
        # Store username and role in session
        session['username'] = username
        session['role'] = role
        return redirect(url_for('home'))
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)  # Clear the role as well
    return redirect(url_for('login'))

@app.route('/add_book', methods=['GET', 'POST'])
@librarian_required
def add_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        isbn = request.form['isbn']
        genre = request.form.get('genre', 'Unknown')  # Optional genre
        books.insert_one({'title': title, 'author': author, 'isbn': isbn, 'genre': genre})
        return redirect(url_for('book_list'))
    return render_template('add_book.html')

@app.route('/add_member', methods=['GET', 'POST'])
@librarian_required
def add_member():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        membership_id = request.form['membership_id']
        members.insert_one({'name': name, 'email': email, 'membership_id': membership_id})
        return redirect(url_for('member_list'))
    return render_template('add_member.html')

@app.route('/book_list', methods=['GET', 'POST'])
def book_list():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':  # Handle search form submission
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        isbn = request.form.get('isbn', '').strip()
        
        # Build query
        query = {}
        if title:
            query['title'] = {'$regex': title, '$options': 'i'}
        if author:
            query['author'] = {'$regex': author, '$options': 'i'}
        if isbn:
            query['isbn'] = isbn
        
        books_list = books.find(query)  # Fetch filtered books
    else:
        books_list = books.find()  # Fetch all books for default GET
    
    return render_template('book_list.html', books=books_list)



@app.route('/member_list')
@librarian_required
def member_list():
    members_list = members.find()
    return render_template('member_list.html', members=members_list)

@app.route('/update_book/<id>', methods=['GET', 'POST'])
@librarian_required
def update_book(id):
    book = books.find_one({'_id': ObjectId(id)})
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        isbn = request.form.get('isbn')
        genre = request.form.get('genre')
        if isbn:
            books.update_one({'_id': ObjectId(id)}, {'$set': {'title': title, 'author': author, 'isbn': isbn, 'genre': genre}})
            return redirect(url_for('book_list'))
        else:
            flash('ISBN is required to update the book.')
            return render_template('update_book.html', book=book)
    return render_template('update_book.html', book=book)

@app.route('/delete_book/<id>', methods=['GET', 'POST'])
@librarian_required
def delete_book(id):
    books.delete_one({'_id': ObjectId(id)})
    return redirect(url_for('book_list'))

@app.route('/update_member/<id>', methods=['GET', 'POST'])
@librarian_required
def update_member(id):
    member = members.find_one({'_id': ObjectId(id)})
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        membership_id = request.form['membership_id']
        members.update_one({'_id': ObjectId(id)}, {'$set': {'name': name, 'email': email, 'membership_id': membership_id}})
        return redirect(url_for('member_list'))
    return render_template('update_member.html', member=member)

@app.route('/delete_member/<id>', methods=['GET', 'POST'])
@librarian_required
def delete_member(id):
    members.delete_one({'_id': ObjectId(id)})
    return redirect(url_for('member_list'))

# Borrow book with due date
@app.route('/borrow_book', methods=['GET', 'POST'])
def borrow_book():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        isbn = request.form['isbn']
        membership_id = request.form['membership_id']
        book = books.find_one({'isbn': isbn})
        member = members.find_one({'membership_id': membership_id})
        if book and member:
            due_date = datetime.now() + timedelta(days=14)  # Use datetime.datetime instead of datetime.date
            borrow_records.insert_one({
                'isbn': book['isbn'],
                'title': book['title'],
                'author': book['author'],
                'member_name': member['name'],
                'membership_id': member['membership_id'],
                'due_date': due_date,  # Use datetime.datetime
                'borrow_date': datetime.now()  # Already a datetime object
            })
            return redirect(url_for('borrow_list'))
        else:
            flash('Invalid ISBN or Membership ID')
    return render_template('borrow_book.html')


@app.route('/borrow_list')
def borrow_list():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Retrieve all borrow records
    borrow_list_entries = list(borrow_records.find())
    
    # Process borrow records
    for record in borrow_list_entries:
        # Ensure `due_date` is a datetime object
        due_date = record.get('due_date')
        if isinstance(due_date, str):
            due_date = datetime.strptime(due_date, "%Y-%m-%dT%H:%M:%S.%f")
        
        record['fine'] = calculate_fine(due_date.date()) if due_date else 0  # Pass `datetime.date` to fine calculation

        # Format `borrow_date`
        borrow_date = record.get('borrow_date')
        if borrow_date and isinstance(borrow_date, str):
            borrow_date = datetime.strptime(borrow_date, "%Y-%m-%dT%H:%M:%S.%f")
        if borrow_date:
            record['borrow_date'] = borrow_date.strftime("%d %B %Y, %I:%M %p")
    
    return render_template('borrow_list.html', borrow_list=borrow_list_entries)


# View fines
@app.route('/view_fines')
def view_fines():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Get current user's borrowed books and calculate fines
    member_id = session['username']  # Assuming username is used as membership ID
    borrow_list = list(borrow_records.find({'membership_id': member_id}))
    
    for record in borrow_list:
        due_date = record.get('due_date', datetime.now().date())  # Assumes due_date is stored
        record['fine'] = calculate_fine(due_date)
    
    return render_template('view_fines.html', borrow_list=borrow_list)

# Fine calculation function
def calculate_fine(due_date):
    today = datetime.now().date()  # Convert to `date` for comparison
    overdue_days = (today - due_date).days
    return max(overdue_days * FINE_RATE, 0)  # Ensure fine is non-negative


if __name__ == "__main__":
    app.run(debug=True)