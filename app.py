from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity

from db import db
from models import User, Exercise, WorkoutPlan, DailySession, SessionExercise

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

@app.route('/workout_plans', methods=['POST'])
@jwt_required()
def create_workout_plan():
    current_user_id = get_jwt_identity()
    data = request.get_json()

    try:
        new_plan = WorkoutPlan(
            title=data['title'],
            goal=data['goal'],
            frequency=data['frequency'],
            duration_min=data['duration_min'],
            user_id=current_user_id
        )
        db.session.add(new_plan)
        db.session.commit()

        for session_data in data['daily_sessions']:
            new_session = DailySession(
                day_of_week=session_data['day_of_week'],
                workout_plan_id=new_plan.id
            )
            db.session.add(new_session)
            db.session.commit()

            for exercise_data in session_data['session_exercises']:
                new_session_exercise = SessionExercise(
                    sets=exercise_data['sets'],
                    reps=exercise_data.get('reps'),
                    duration_min=exercise_data.get('duration_min'),
                    distance_km=exercise_data.get('distance_km'),
                    daily_session_id=new_session.id,
                    exercise_id=exercise_data['exercise_id']
                )
                db.session.add(new_session_exercise)

        db.session.commit()

        return jsonify({"message": "Workout plan created successfully!", "plan_id": new_plan.id}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e), "message": "Failed to create workout plan"}), 400

@app.route('/workout_plans', methods=['GET'])
@jwt_required()
def get_workout_plans():
    current_user_id = get_jwt_identity()
    plans = WorkoutPlan.query.filter_by(user_id=current_user_id).all()

    plans_list = []
    for plan in plans:
        plan_data = {
            'id': plan.id,
            'title': plan.title,
            'goal': plan.goal,
            'frequency': plan.frequency,
            'duration_min': plan.duration_min,
            'date_created': plan.date_created.isoformat(),
            'daily_sessions': []
        }

        for session in plan.daily_sessions:
            session_data = {
                'id': session.id,
                'day_of_week': session.day_of_week,
                'exercises': []
            }

            for session_ex in session.session_exercises:
                exercise_details = Exercise.query.get(session_ex.exercise_id)
                session_exercise_data = {
                    'sets': session_ex.sets,
                    'reps': session_ex.reps,
                    'duration_min': session_ex.duration_min,
                    'distance_km': session_ex.distance_km,
                    'exercise_name': exercise_details.name,
                    'exercise_description': exercise_details.description,
                    'exercise_guide': exercise_details.guide
                }
                session_data['exercises'].append(session_exercise_data)

            plan_data['daily_sessions'].append(session_data)
        plans_list.append(plan_data)

    return jsonify(plans_list), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)