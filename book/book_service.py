import os
import logging
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import jwt
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}@{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}/{os.getenv("DB_NAME")}?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

JWT_SECRET = os.getenv('JWT_SECRET')

class Book(db.Model):
    __tablename__ = 'books'  # Explicitly map to plural table name (fixes 1146 error)
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    author_bio = db.Column(db.Text)  # Additional author info (bio/description)
    image_url = db.Column(db.String(500))  # URL to book cover image
    book_url = db.Column(db.String(500), nullable=False)  # URL to full book content (PDF/online)
    available = db.Column(db.Boolean, default=True)  # True if available for borrow

def get_user_from_token(token):
    try:
        decoded = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        logger.debug(f"Token decoded: user_id={decoded.get('user_id')}, role={decoded.get('role')}")
        return decoded
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        return None
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return None

@app.before_request
def log_request():
    logger.debug(f"Book request: {request.method} {request.url}")
    logger.debug(f"Headers: {dict(request.headers)}")
    logger.debug(f"Params: {request.args}")
    logger.debug(f"Body: {request.get_json(silent=True) or {}}")

@app.route('/books', methods=['GET'])
def get_books():
    token = request.headers.get('Authorization')
    if not token or not token.startswith('Bearer '):
        error_msg = 'Missing or invalid Authorization header'
        logger.warning(f"{error_msg} - Returning 422")
        return jsonify({'error': error_msg}), 422
    
    user_data = get_user_from_token(token.replace('Bearer ', ''))
    if not user_data:
        error_msg = 'Invalid or expired token'
        logger.warning(f"{error_msg} - Returning 422")
        return jsonify({'error': error_msg}), 422
    
    user_id = user_data.get('user_id')
    # Filter available books (add user-specific filter if needed later)
    query = Book.query.filter_by(available=True)
    if request.args.get('user_id'):
        # Placeholder for user-specific books
        pass
    
    books = query.all()
    books_data = [
        {
            'id': b.id,
            'title': b.title,
            'author': b.author,
            'author_bio': b.author_bio,
            'image_url': b.image_url,
            'book_url': b.book_url,
            'available': b.available
        }
        for b in books
    ]
    logger.info(f"Returning {len(books_data)} available books for user_id={user_id}")
    return jsonify({'books': books_data})  # Consistent format: {'books': [...]}

@app.route('/books/all', methods=['GET'])  # New: Admin-only, all books (no available filter)
def get_all_books():
    token = request.headers.get('Authorization')
    if not token or not token.startswith('Bearer '):
        error_msg = 'Missing or invalid Authorization header'
        logger.warning(f"{error_msg} - Returning 422")
        return jsonify({'error': error_msg}), 422
    
    user_data = get_user_from_token(token.replace('Bearer ', ''))
    if not user_data:
        error_msg = 'Invalid or expired token'
        logger.warning(f"{error_msg} - Returning 422")
        return jsonify({'error': error_msg}), 422
    
    if user_data.get('role') != 'admin':
        error_msg = 'Admin role required'
        logger.warning(f"Non-admin attempt to get all books by user_id={user_data.get('user_id')} - Returning 403")
        return jsonify({'error': error_msg}), 403
    
    books = Book.query.all()  # All books, no filter
    books_data = [
        {
            'id': b.id,
            'title': b.title,
            'author': b.author,
            'author_bio': b.author_bio,
            'image_url': b.image_url,
            'book_url': b.book_url,
            'available': b.available
        }
        for b in books
    ]
    logger.info(f"Returning {len(books_data)} all books for admin user_id={user_data.get('user_id')}")
    return jsonify({'books': books_data})

@app.route('/books', methods=['POST'])
def add_book():
    token = request.headers.get('Authorization')
    if not token or not token.startswith('Bearer '):
        error_msg = 'Missing or invalid Authorization header'
        logger.warning(f"{error_msg} - Returning 422")
        return jsonify({'error': error_msg}), 422
    
    user_data = get_user_from_token(token.replace('Bearer ', ''))
    if not user_data:
        error_msg = 'Invalid or expired token'
        logger.warning(f"{error_msg} - Returning 422")
        return jsonify({'error': error_msg}), 422
    
    if user_data.get('role') != 'admin':
        error_msg = 'Admin role required'
        logger.warning(f"Non-admin attempt to add book by user_id={user_data.get('user_id')} - Returning 403")
        return jsonify({'error': error_msg}), 403
    
    data = request.get_json()
    required_fields = ['title', 'author', 'book_url']
    if not data or not all(k in data for k in required_fields):
        missing = [k for k in required_fields if k not in data]
        error_msg = f'Missing required fields: {", ".join(missing)} (also provide author_bio, image_url)'
        logger.warning(f"{error_msg} - Body: {data} - Returning 422")
        return jsonify({'error': error_msg}), 422
    
    book = Book(
        title=data['title'],
        author=data['author'],
        author_bio=data.get('author_bio', ''),
        image_url=data.get('image_url', ''),
        book_url=data['book_url'],
        available=True
    )
    db.session.add(book)
    db.session.commit()
    logger.info(f"Book added: '{data['title']}' by {data['author']}, URL: {data['book_url']}, Bio: {data.get('author_bio', 'N/A')} for admin user_id={user_data['user_id']}")
    return jsonify({
        'message': 'Book added',
        'id': book.id,
        'title': book.title,
        'author': book.author,
        'author_bio': book.author_bio,
        'image_url': book.image_url,
        'book_url': book.book_url
    }), 201

@app.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    token = request.headers.get('Authorization')
    if not token or not token.startswith('Bearer '):
        error_msg = 'Missing or invalid Authorization header'
        logger.warning(f"{error_msg} - Returning 422")
        return jsonify({'error': error_msg}), 422
    
    user_data = get_user_from_token(token.replace('Bearer ', ''))
    if not user_data:
        error_msg = 'Invalid or expired token'
        logger.warning(f"{error_msg} - Returning 422")
        return jsonify({'error': error_msg}), 422
    
    if user_data.get('role') != 'admin':
        error_msg = 'Admin role required'
        logger.warning(f"Non-admin attempt to delete book {book_id} by user_id={user_data.get('user_id')} - Returning 403")
        return jsonify({'error': error_msg}), 403
    
    book = Book.query.get_or_404(book_id)
    title = book.title  # For logging
    db.session.delete(book)
    db.session.commit()
    logger.info(f"Book deleted: ID {book_id} ('{title}') by admin user_id={user_data['user_id']}")
    return jsonify({'message': 'Book deleted'}), 200

@app.route('/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    token = request.headers.get('Authorization')
    if not token or not token.startswith('Bearer '):
        error_msg = 'Missing or invalid Authorization header'
        logger.warning(f"{error_msg} - Returning 422")
        return jsonify({'error': error_msg}), 422
    
    user_data = get_user_from_token(token.replace('Bearer ', ''))
    if not user_data:
        error_msg = 'Invalid or expired token'
        logger.warning(f"{error_msg} - Returning 422")
        return jsonify({'error': error_msg}), 422
    
    if user_data.get('role') != 'admin':
        error_msg = 'Admin role required'
        logger.warning(f"Non-admin attempt to update book {book_id} by user_id={user_data.get('user_id')} - Returning 403")
        return jsonify({'error': error_msg}), 403
    
    book = Book.query.get(book_id)
    if not book:
        logger.warning(f"Book {book_id} not found for update by user_id={user_data.get('user_id')}")
        return jsonify({'error': 'Book not found'}), 404
    
    data = request.get_json()
    if not data:
        error_msg = 'No data provided'
        logger.warning(f"{error_msg} - Returning 422")
        return jsonify({'error': error_msg}), 422
    
    # Update book fields
    if 'title' in data:
        book.title = data['title']
    if 'author' in data:
        book.author = data['author']
    if 'author_bio' in data:
        book.author_bio = data['author_bio']
    if 'image_url' in data:
        book.image_url = data['image_url']
    if 'book_url' in data:
        book.book_url = data['book_url']
    if 'available' in data:
        book.available = data['available']
    
    db.session.commit()
    
    logger.info(f"Book updated: ID {book_id} ('{book.title}') by admin user_id={user_data['user_id']}")
    return jsonify({
        'message': 'Book updated',
        'book': {
            'id': book.id,
            'title': book.title,
            'author': book.author,
            'author_bio': book.author_bio,
            'image_url': book.image_url,
            'book_url': book.book_url,
            'available': book.available
        }
    }), 200

@app.route('/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    token = request.headers.get('Authorization')
    if not token or not token.startswith('Bearer '):
        error_msg = 'Missing or invalid Authorization header'
        logger.warning(f"{error_msg} - Returning 422")
        return jsonify({'error': error_msg}), 422
    
    user_data = get_user_from_token(token.replace('Bearer ', ''))
    if not user_data:
        error_msg = 'Invalid or expired token'
        logger.warning(f"{error_msg} - Returning 422")
        return jsonify({'error': error_msg}), 422
    
    book = Book.query.get(book_id)
    if not book:
        logger.warning(f"Book {book_id} not found for user_id={user_data.get('user_id')}")
        return jsonify({'error': 'Book not found'}), 404
    
    book_data = {
        'id': book.id,
        'title': book.title,
        'author': book.author,
        'author_bio': book.author_bio,
        'image_url': book.image_url,
        'book_url': book.book_url,
        'available': book.available
    }
    
    logger.info(f"Returning book {book_id} for user_id={user_data.get('user_id')}")
    return jsonify({'book': book_data})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # For local dev; DB init script handles prod
    app.run(host='0.0.0.0', port=5001, debug=True)