from flask import request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import User, Exercise, WorkoutPlan, DailySession, SessionExercise, WeightInsert, Goal
from db import db
from flask_smorest import Blueprint as SmorestBlueprint
from schemas import UserSchema, AuthSchema

blp = SmorestBlueprint('blp', __name__, url_prefix="")
bcrypt = Bcrypt()

@blp.route('/register', methods=['POST'])
@blp.doc(
    summary="Register a new user",
)
# @blp.arguments(UserSchema)
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

@blp.route('/login', methods=['POST'])
@blp.doc(
    summary="Authenticate user",
)
# @blp.arguments(AuthSchema)
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

@blp.route('/profile', methods=['GET'])
@blp.doc(
    summary="Get user profile",
)
@jwt_required()
def profile():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    return jsonify(logged_in_username=user.username), 200

@blp.route('/exercises', methods=['GET'])
@blp.doc(
    summary="Get all exercises",
)
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

@blp.route('/workout_plans', methods=['POST'])
@blp.doc(
    summary="Create a new workout plan",
)
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

@blp.route('/workout_plans', methods=['GET'])
@blp.doc(
    summary="Get all user workout plans",
)
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

@blp.route('/weight', methods=['POST'])
@blp.doc(
    summary="Add a new weight entry",
)
@jwt_required()
def add_weight():
    current_user_id = get_jwt_identity()
    data = request.get_json()

    try:
        new_weight_entry = WeightInsert(
            weight_kg=data['weight_kg'],
            user_id=current_user_id
        )
        db.session.add(new_weight_entry)
        db.session.commit()
        return jsonify({"message": "Weight entry added successfully!"}), 201
    except Exception as e:
        return jsonify({"error": str(e), "message": "Failed to add weight entry"}), 400

@blp.route('/weight', methods=['GET'])
@blp.doc(
    summary="Get user's weight",
)
@jwt_required()
def get_weight_history():
    current_user_id = get_jwt_identity()
    weight_entries = WeightInsert.query.filter_by(user_id=current_user_id).order_by(WeightInsert.date_recorded.asc()).all()
    history = [
        {
            'id': entry.id,
            'weight_kg': entry.weight_kg,
            'date_recorded': entry.date_recorded.isoformat()
        } for entry in weight_entries
    ]
    return jsonify(history), 200

@blp.route('/goals', methods=['POST'])
@blp.doc(
    summary="Set a new goal",
)
@jwt_required()
def set_goal():
    current_user_id = get_jwt_identity()
    data = request.get_json()

    try:
        new_goal = Goal(
            goal_type=data['goal_type'],
            target_value=data['target_value'],
            user_id=current_user_id
        )
        db.session.add(new_goal)
        db.session.commit()
        return jsonify({"message": "Goal set successfully!"}), 201
    except Exception as e:
        return jsonify({"error": str(e), "message": "Failed to set goal"}), 400

@blp.route('/goals', methods=['GET'])
@blp.doc(
    summary="Get all user goals",
)
@jwt_required()
def get_goals():
    current_user_id = get_jwt_identity()
    goals = Goal.query.filter_by(user_id=current_user_id).all()
    goals_list = [
        {
            'id': goal.id,
            'goal_type': goal.goal_type,
            'target_value': goal.target_value,
            'is_achieved': goal.is_achieved
        } for goal in goals
    ]
    return jsonify(goals_list), 200