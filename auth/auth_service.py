import os
import logging
import time
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy.exc import OperationalError

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}@{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}/{os.getenv("DB_NAME")}?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

JWT_SECRET = os.getenv('JWT_SECRET')

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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

def create_sample_admin(max_retries=10, base_delay=2):
    for attempt in range(1, max_retries + 1):
        try:
            with app.app_context():
                admin_user = User.query.filter_by(username='admin').first()
                if admin_user:
                    logger.info("Sample admin user already exists—skipping creation.")
                    return
                admin = User(username='admin', role='admin')
                admin.set_password('adminpass')
                db.session.add(admin)
                db.session.commit()
                logger.info("Sample admin user created on startup: admin / adminpass")
                return
        except OperationalError as e:
            if "Can't connect to MySQL server" in str(e) or "Connection refused" in str(e):
                logger.warning(f"Retrying DB connection for admin creation (attempt {attempt}/{max_retries})")
                time.sleep(base_delay * attempt)
                continue
            else:
                raise
        except Exception as e:
            logger.warning(f"Failed to create sample admin (may already exist or DB issue): {str(e)}")
            return
    
    logger.error(f"Failed to create sample admin after {max_retries} retries—DB may not be ready. Manual creation needed.")

create_sample_admin()

@app.before_request
def log_request():
    logger.debug(f"Auth request: {request.method} {request.url}")
    logger.debug(f"Headers: {dict(request.headers)}")
    logger.debug(f"Body: {request.get_json(silent=True) or {}}")

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    if not data or not all(k in data for k in ['username', 'password', 'role']):
        logger.warning("Signup: Missing required fields (username, password, role)")
        return jsonify({'error': 'Missing required fields'}), 422
    username = data['username']
    if User.query.filter_by(username=username).first():
        logger.warning(f"Signup: User {username} already exists")
        return jsonify({'error': 'User  already exists'}), 400
    if data['role'] not in ['user', 'admin']:
        logger.warning(f"Signup: Invalid role {data['role']}")
        return jsonify({'error': 'Role must be user or admin'}), 422
    user = User(username=username, role=data['role'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    logger.info(f"User  signed up: {username} with role {data['role']}")
    return jsonify({'message': 'User  created successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not all(k in data for k in ['username', 'password']):
        logger.warning("Login: Missing required fields (username, password)")
        return jsonify({'error': 'Missing credentials'}), 422
    username = data['username']
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(data['password']):
        token = jwt.encode({
            'user_id': user.id,
            'username': user.username,
            'role': user.role,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, JWT_SECRET, algorithm='HS256')
        logger.info(f"User  logged in: {username}")
        return jsonify({'token': token, 'user_id': user.id, 'role': user.role}), 200
    logger.warning(f"Login failed: Invalid credentials for {username}")
    return jsonify({'error': 'Invalid username or password'}), 401

@app.route('/users', methods=['GET'])
def get_all_users():
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
        logger.warning(f"Non-admin attempt to get users by user_id={user_data.get('user_id')} - Returning 403")
        return jsonify({'error': error_msg}), 403
    
    users = User.query.all()
    users_data = [
        {
            'id': u.id,
            'username': u.username,
            'role': u.role
        }
        for u in users
    ]
    logger.info(f"Returning {len(users_data)} users for admin user_id={user_data.get('user_id')}")
    return jsonify({'users': users_data})

@app.route('/users', methods=['POST'])
def create_user():
    token = request.headers.get('Authorization')
    if not token or not token.startswith('Bearer '):
        return jsonify({'error': 'Missing or invalid Authorization header'}), 422
    user_data = get_user_from_token(token.replace('Bearer ', ''))
    if not user_data:
        return jsonify({'error': 'Invalid or expired token'}), 422
    if user_data.get('role') != 'admin':
        return jsonify({'error': 'Admin role required'}), 403
    data = request.get_json()
    if not data or not all(k in data for k in ['username', 'password', 'role']):
        return jsonify({'error': 'Missing username, password, or role'}), 422
    username = data['username']
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 409
    if data['role'] not in ['user', 'admin']:
        return jsonify({'error': 'Role must be user or admin'}), 422
    if len(data['password']) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 422
    user = User(username=username, role=data['role'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    logger.info(f"Admin created user: {username} with role {data['role']}")
    return jsonify({'message': 'User  created successfully', 'user_id': user.id}), 201

@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    token = request.headers.get('Authorization')
    if not token or not token.startswith('Bearer '):
        return jsonify({'error': 'Missing or invalid Authorization header'}), 422
    user_data = get_user_from_token(token.replace('Bearer ', ''))
    if not user_data:
        return jsonify({'error': 'Invalid or expired token'}), 422
    if user_data.get('role') != 'admin':
        return jsonify({'error': 'Admin role required'}), 403
    if user_data.get('user_id') == user_id:
        return jsonify({'error': 'Cannot delete your own account'}), 403
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({'error': 'User  not found'}), 404
    username = user.username
    db.session.delete(user)
    db.session.commit()
    logger.info(f"Admin deleted user: {username} (ID {user_id})")
    return jsonify({'message': 'User  deleted successfully'}), 200

if __name__ == '__main__':
    create_sample_admin()
    app.run(host='0.0.0.0', port=5002, debug=True)