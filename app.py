from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity

from db import db
from models import User, Exercise

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secretKey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///workout.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'JWTsecretKey'

db.init_app(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

@app.route('/')
def home():
    return '<h1>hello there</h1>'

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username:
        return jsonify({'message': 'Username is required'}), 400
    
    if not email:
        return jsonify({'message': 'Email is required'}), 400

    if not password:
        return jsonify({'message': 'Password is required'}), 400

    username_exists = User.query.filter_by(username=username).first()
    if username_exists:
        return jsonify({'message': 'Username already exists'}), 409

    email_exists = User.query.filter_by(email=email).first()
    if email_exists:
        return jsonify({'message': 'Email already exists'}), 409

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, email=email, password=hashed_password)
    
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({'message': 'Invalid username'}), 401

    if not bcrypt.check_password_hash(user.password, password):
        return jsonify({'message': 'Invalid password'}), 401
    
    access_token = create_access_token(identity=str(user.id))
    return jsonify(access_token=access_token), 200

@app.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    return jsonify(logged_in_username=user.username), 200

@app.route('/exercises', methods=['GET'])
def get_exercises():
    all_exercises = Exercise.query.all()
    exercises_list = [
        {
            'id': exercise.id,
            'name': exercise.name,
            'description': exercise.description,
            'guide': exercise.guide
        } for exercise in all_exercises
    ]
    return jsonify(exercises_list), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)