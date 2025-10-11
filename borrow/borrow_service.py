import os
import logging
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import jwt
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import desc  # For sorting borrows by date

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}@{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}/{os.getenv("DB_NAME")}?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

JWT_SECRET = os.getenv('JWT_SECRET')

class Borrow(db.Model):
    __tablename__ = 'borrows'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    book_id = db.Column(db.Integer, nullable=False)
    borrow_date = db.Column(db.DateTime, default=datetime.utcnow)

class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    author_bio = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    book_url = db.Column(db.String(500), nullable=False)
    available = db.Column(db.Boolean, default=True)

# Assume User model for joins (fetch from auth if needed, but for simplicity, use username via ID if separate)
class User(db.Model):  # Placeholder—join via user_id if needed; for now, return user_id
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    role = db.Column(db.String(20), default='user')

def get_user_id_from_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload['user_id'], payload['role']  # Return both for admin checks
    except jwt.InvalidTokenError:
        logger.warning("Invalid token in get_user_id_from_token")
        return None, None

@app.before_request
def log_request():
    logger.debug(f"Borrow request: {request.method} {request.url}")
    logger.debug(f"Headers: {dict(request.headers)}")
    logger.debug(f"Body: {request.get_json(silent=True) or {}}")

@app.route('/borrow', methods=['POST'])
def borrow_book():
    data = request.get_json()
    if not data or not all(k in data for k in ['user_id', 'book_id']):
        logger.warning("Borrow: Missing user_id or book_id")
        return jsonify({'error': 'Missing user_id or book_id'}), 422
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        logger.warning("Borrow: Missing token")
        return jsonify({'error': 'Invalid or missing token'}), 401
    user_id, role = get_user_id_from_token(token)
    if not user_id:
        return jsonify({'error': 'Invalid token'}), 401
    if user_id != data['user_id']:
        logger.warning(f"Borrow: Unauthorized user_id {data['user_id']} vs token {user_id}")
        return jsonify({'error': 'Unauthorized'}), 403
    book = Book.query.filter_by(id=data['book_id'], available=True).first()
    if not book:
        logger.warning(f"Borrow: Book {data['book_id']} not available")
        return jsonify({'error': 'Book not available'}), 404
    borrow = Borrow(user_id=user_id, book_id=data['book_id'])
    db.session.add(borrow)
    book.available = False
    db.session.commit()
    logger.info(f"Book '{book.title}' (ID {book.id}) borrowed by user {user_id}")
    return jsonify({'message': 'Book borrowed successfully', 'borrow_id': borrow.id}), 201

@app.route('/return/<int:borrow_id>', methods=['POST'])
def return_book(borrow_id):
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return jsonify({'error': 'Missing token'}), 401
    user_id, role = get_user_id_from_token(token)
    if not user_id:
        return jsonify({'error': 'Invalid token'}), 401
    borrow = Borrow.query.filter_by(id=borrow_id).first()
    if not borrow:
        return jsonify({'error': 'Borrow not found'}), 404
    if borrow.user_id != user_id:
        return jsonify({'error': 'Unauthorized to return this book'}), 403
    book = Book.query.filter_by(id=borrow.book_id).first()
    if book:
        book.available = True
    db.session.delete(borrow)
    db.session.commit()
    logger.info(f"Book '{book.title if book else 'Unknown'}' (Borrow ID {borrow_id}) returned by user {user_id}")
    return jsonify({'message': 'Book returned successfully'}), 200

@app.route('/borrowed', methods=['GET'])
def get_borrowed_books():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        logger.warning("Borrowed: Missing Authorization header")
        return jsonify({'error': 'Missing Authorization header'}), 422
    user_id, role = get_user_id_from_token(token)
    if not user_id:
        logger.warning("Borrowed: Invalid token")
        return jsonify({'error': 'Invalid token'}), 401
    try:
        borrowed = db.session.query(Borrow, Book).join(Book, Borrow.book_id == Book.id).filter(Borrow.user_id == user_id).all()
        if not borrowed:
            logger.info(f"No borrowed books for user_id={user_id}")
            return jsonify({'borrowed_books': []}), 200
        result = []
        for borrow, book in borrowed:
            result.append({
                'id': borrow.id,  # This is the borrow record ID
                'book_id': book.id,  # ADD THIS LINE - the actual book ID
                'title': book.title,
                'author': book.author,
                'author_bio': book.author_bio,
                'image_url': book.image_url,
                'book_url': book.book_url,
                'borrow_date': borrow.borrow_date.isoformat()
            })
        logger.info(f"Returning {len(result)} borrowed books for user_id={user_id}")
        return jsonify({'borrowed_books': result}), 200
    except Exception as e:
        logger.error(f"Error querying borrowed books for user_id={user_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/borrows/all', methods=['GET'])  # Admin-only: All borrows
def get_all_borrows():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return jsonify({'error': 'Missing token'}), 401
    _, role = get_user_id_from_token(token)
    if role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    try:
        # Join Borrow, Book, User (for username)
        all_borrows = db.session.query(Borrow, Book, User).\
            join(Book, Borrow.book_id == Book.id).\
            join(User, Borrow.user_id == User.id).\
            order_by(desc(Borrow.borrow_date)).all()  # Recent first
        result = []
        for borrow, book, user in all_borrows:
            result.append({
                'borrow_id': borrow.id,
                'user_id': borrow.user_id,
                'username': user.username,
                'title': book.title,
                'author': book.author,
                'borrow_date': borrow.borrow_date.isoformat(),
                'available': book.available  # False if borrowed
            })
        logger.info(f"Returning {len(result)} all borrows for admin")
        return jsonify({'borrows': result}), 200
    except Exception as e:
        logger.error(f"Error querying all borrows: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003, debug=True)