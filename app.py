import os
import requests
import logging
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_session import Session
from functools import wraps
from dotenv import load_dotenv
import jwt

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-key-change-in-prod'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

JWT_SECRET = os.getenv('JWT_SECRET')
AUTH_SERVICE_URL = 'http://auth-service:5002'
BOOK_SERVICE_URL = 'http://book-service:5001'
BORROW_SERVICE_URL = 'http://borrow-service:5003'

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = session.get('token')
        if not token:
            flash('Authentication required')
            return redirect(url_for('signin'))
        try:
            decoded = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            session['user_id'] = decoded['user_id']
            session['username'] = decoded['username']
            session['role'] = decoded['role']
        except jwt.InvalidTokenError:
            flash('Invalid token')
            return redirect(url_for('signin'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Admin access required')
            return redirect(url_for('books'))
        return f(*args, **kwargs)
    return decorated

@app.context_processor
def inject_session():
    return dict(session=session)

@app.route('/')
def index():
    if session.get('token'):
        return redirect(url_for('books'))
    return redirect(url_for('signin'))

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        response = requests.post(f'{AUTH_SERVICE_URL}/login', json={'username': username, 'password': password})
        logger.info(f"Login attempt for {username}: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            session['token'] = data['token']
            logger.info(f"User        {username} logged in successfully")
            return redirect(url_for('books'))
        else:
            flash('Invalid credentials')
            logger.warning(f"Login failed for {username}: {response.text}")
    return render_template('signin.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        response = requests.post(f'{AUTH_SERVICE_URL}/signup', json={'username': username, 'password': password, 'role': role})
        logger.info(f"Signup attempt for {username} (role: {role}): {response.status_code}")
        if response.status_code == 201:
            logger.info(f"User        {username} signed up with role {role}")
            return redirect(url_for('signin'))
        else:
            flash('Signup failed: ' + response.json().get('error', 'Unknown error'))
            logger.error(f"Signup failed for {username}: {response.text}")
    return render_template('signup.html')

@app.route('/books')
@token_required
def books():
    user_id = session['user_id']
    headers = {'Authorization': f'Bearer {session["token"]}'}
    try:
        response = requests.get(f'{BOOK_SERVICE_URL}/books', headers=headers, params={'user_id': user_id}, timeout=10)
        logger.info(f"Books request for user {user_id}: {response.status_code} - {response.text[:100]}...")
        response.raise_for_status()
        books_data = response.json().get('books', [])
    except requests.exceptions.RequestException as e:
        flash(f'Failed to load books: {str(e)}')
        books_data = []
        logger.error(f"Failed to load books: {str(e)}")
    return render_template('books.html', books=books_data)

@app.route('/book/<int:book_id>')
@token_required
def book_details(book_id):
    headers = {'Authorization': f'Bearer {session["token"]}'}
    try:
        response = requests.get(f'{BOOK_SERVICE_URL}/books/{book_id}', headers=headers, timeout=10)
        response.raise_for_status()
        book_data = response.json().get('book')
        
        if not book_data:
            flash('Book not found')
            return redirect(url_for('books'))
            
        logger.info(f"Book details loaded for book_id: {book_id}")
        return render_template('book_details.html', book=book_data)
        
    except requests.exceptions.RequestException as e:
        flash(f'Failed to load book details: {str(e)}')
        logger.error(f"Failed to load book details: {str(e)}")
        return redirect(url_for('books'))
        return redirect(url_for('books'))

@app.route('/borrow/<int:book_id>', methods=['POST'])
@token_required
def borrow_book(book_id):
    user_id = session['user_id']
    headers = {'Authorization': f'Bearer {session["token"]}'}
    try:
        response = requests.post(f'{BORROW_SERVICE_URL}/borrow', json={'user_id': user_id, 'book_id': book_id}, headers=headers, timeout=10)
        logger.info(f"Borrow request for user {user_id}, book {book_id}: {response.status_code}")
        response.raise_for_status()
        flash('Book borrowed successfully')
    except requests.exceptions.RequestException as e:
        flash('Borrow failed: ' + str(e))
        logger.error(f"Borrow failed: {str(e)}")
    return redirect(url_for('books'))

@app.route('/borrowed')
@token_required
def borrowed():
    headers = {'Authorization': f'Bearer {session["token"]}'}
    try:
        response = requests.get(f'{BORROW_SERVICE_URL}/borrowed', headers=headers, timeout=10)
        logger.info(f"Borrowed books request: {response.status_code}")
        response.raise_for_status()
        borrowed_data = response.json()
    except requests.exceptions.RequestException as e:
        flash('Failed to load borrowed books: ' + str(e))
        borrowed_data = {'borrowed_books': []}
        logger.error(f"Failed to load borrowed: {str(e)}")
    return render_template('borrow.html', borrowed=borrowed_data)

@app.route('/return/<int:borrow_id>', methods=['POST'])
@token_required
def return_book(borrow_id):
    headers = {'Authorization': f'Bearer {session["token"]}'}
    try:
        response = requests.post(f'{BORROW_SERVICE_URL}/return/{borrow_id}', headers=headers, timeout=10)
        logger.info(f"Return request for borrow {borrow_id}: {response.status_code}")
        response.raise_for_status()
        flash('Book returned successfully')
    except requests.exceptions.RequestException as e:
        flash('Return failed: ' + str(e))
        logger.error(f"Return failed: {str(e)}")
    return redirect(url_for('borrowed'))

@app.route('/admin')
@token_required
@admin_required
def admin():
    headers = {'Authorization': f'Bearer {session["token"]}'}
    books_data = []
    users_data = []
    borrows_data = []
    try:
        book_response = requests.get(f'{BOOK_SERVICE_URL}/books/all', headers=headers, timeout=10)
        book_response.raise_for_status()
        books_data = book_response.json().get('books', [])
        logger.info(f"Admin loaded {len(books_data)} all books")
    except requests.exceptions.RequestException as e:
        flash(f'Failed to load books: {str(e)}')
        logger.error(f"Admin failed to load all books: {str(e)}")

    try:
        user_response = requests.get(f'{AUTH_SERVICE_URL}/users', headers=headers, timeout=10)
        user_response.raise_for_status()
        users_data = user_response.json().get('users', [])
        logger.info(f"Admin loaded {len(users_data)} users")
    except requests.exceptions.RequestException as e:
        flash(f'Failed to load users: {str(e)}')
        logger.error(f"Admin failed to load users: {str(e)}")

    try:
        borrow_response = requests.get(f'{BORROW_SERVICE_URL}/borrows/all', headers=headers, timeout=10)
        borrow_response.raise_for_status()
        borrows_data = borrow_response.json().get('borrows', [])
        logger.info(f"Admin loaded {len(borrows_data)} borrows")
    except requests.exceptions.RequestException as e:
        flash(f'Failed to load borrows: {str(e)}')
        logger.error(f"Admin failed to load borrows: {str(e)}")

    return render_template('admin.html', books=books_data, users=users_data, borrows=borrows_data, current_user_id=session['user_id'])

@app.route('/admin/users', methods=['GET', 'POST'])
@token_required
@admin_required
def manage_users():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        headers = {'Authorization': f'Bearer {session["token"]}'}
        data = {'username': username, 'password': password, 'role': role}
        try:
            response = requests.post(f'{AUTH_SERVICE_URL}/users', json=data, headers=headers, timeout=10)
            logger.info(f"Admin create user '{username}' (role: {role}): {response.status_code}")
            response.raise_for_status()
            flash('User    created successfully')
            return redirect(url_for('admin'))
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e.response, 'json'):
                error_msg = e.response.json().get('error', error_msg)
            flash(f'Create user failed: {error_msg}')
            logger.error(f"Admin create user failed: {error_msg}")
    return render_template('admin-users.html')

@app.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@token_required
@admin_required
def delete_user_proxy(user_id):
    if session['user_id'] == user_id:
        flash('Cannot delete your own account')
        return redirect(url_for('admin'))
    headers = {'Authorization': f'Bearer {session["token"]}'}
    try:
        response = requests.delete(f'{AUTH_SERVICE_URL}/users/{user_id}', headers=headers, timeout=10)
        logger.info(f"Admin delete user {user_id}: {response.status_code}")
        response.raise_for_status()
        flash('User    deleted successfully')
    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        if hasattr(e.response, 'json'):
            error_msg = e.response.json().get('error', error_msg)
        flash(f'Delete user failed: {error_msg}')
        logger.error(f"Admin delete user failed: {error_msg}")
    return redirect(url_for('admin'))

@app.route('/admin/add-book', methods=['GET', 'POST'])
@token_required
@admin_required
def add_book_page():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        author_bio = request.form.get('author_bio', '')
        image_url = request.form.get('image_url', '')
        book_url = request.form['book_url']
        headers = {'Authorization': f'Bearer {session["token"]}'}
        data = {
            'title': title,
            'author': author,
            'author_bio': author_bio,
            'image_url': image_url,
            'book_url': book_url
        }
        try:
            response = requests.post(f'{BOOK_SERVICE_URL}/books', json=data, headers=headers, timeout=10)
            logger.info(f"Add book '{title}': {response.status_code}")
            response.raise_for_status()
            flash('Book added successfully')
            return redirect(url_for('admin'))
        except requests.exceptions.RequestException as e:
            flash('Add failed: ' + str(e))
            logger.error(f"Add book failed: {str(e)}")
        return render_template('add-book.html')
    return render_template('add-book.html')

@app.route('/admin/edit-book/<int:book_id>', methods=['GET', 'POST'])
@token_required
@admin_required
def edit_book_page(book_id):
    headers = {'Authorization': f'Bearer {session["token"]}'}
    
    if request.method == 'POST':
        # Handle form submission for updating book
        title = request.form['title']
        author = request.form['author']
        author_bio = request.form.get('author_bio', '')
        image_url = request.form.get('image_url', '')
        book_url = request.form['book_url']
        available = 'available' in request.form  # Checkbox
        
        data = {
            'title': title,
            'author': author,
            'author_bio': author_bio,
            'image_url': image_url,
            'book_url': book_url,
            'available': available
        }
        
        try:
            response = requests.put(f'{BOOK_SERVICE_URL}/books/{book_id}', json=data, headers=headers, timeout=10)
            logger.info(f"Update book {book_id}: {response.status_code}")
            response.raise_for_status()
            flash('Book updated successfully')
            return redirect(url_for('admin'))
        except requests.exceptions.RequestException as e:
            flash('Update failed: ' + str(e))
            logger.error(f"Update book failed: {str(e)}")
    
    # GET request - load existing book data
    try:
        # Get all books to find the specific one
        response = requests.get(f'{BOOK_SERVICE_URL}/books/all', headers=headers, timeout=10)
        response.raise_for_status()
        all_books = response.json().get('books', [])
        
        # Find the specific book by ID
        book = next((b for b in all_books if b['id'] == book_id), None)
        
        if not book:
            flash('Book not found')
            return redirect(url_for('admin'))
            
        return render_template('edit-book.html', book=book)
        
    except requests.exceptions.RequestException as e:
        flash(f'Failed to load book: {str(e)}')
        logger.error(f"Failed to load book for editing: {str(e)}")
        return redirect(url_for('admin'))

@app.route('/admin/delete/<int:book_id>', methods=['POST'])
@token_required
@admin_required
def delete_book(book_id):
    headers = {'Authorization': f'Bearer {session["token"]}'}
    try:
        response = requests.delete(f'{BOOK_SERVICE_URL}/books/{book_id}', headers=headers, timeout=10)
        logger.info(f"Delete book {book_id}: {response.status_code}")
        response.raise_for_status()
        flash('Book deleted successfully')
    except requests.exceptions.RequestException as e:
        flash('Delete failed: ' + str(e))
        logger.error(f"Delete failed: {str(e)}")
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out')
    return redirect(url_for('signin'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)