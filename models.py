from db import db
from datetime import datetime, timezone

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    workout_plans = db.relationship('WorkoutPlan', backref='user', lazy=True)
    weight_inserts = db.relationship('WeightInsert', backref='user', lazy=True)
    goals = db.relationship('Goal', backref='user', lazy=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"
    
class Exercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    guide = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"Exercise('{self.name}')"

class WorkoutPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    goal = db.Column(db.String(200), nullable=False)
    frequency = db.Column(db.String(50), nullable=False)
    duration_min = db.Column(db.Integer, nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    daily_sessions = db.relationship('DailySession', backref='workout_plan', lazy=True)

    def __repr__(self):
        return f"WorkoutPlan('{self.title}')"

class DailySession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day_of_week = db.Column(db.String(10), nullable=False)
    workout_plan_id = db.Column(db.Integer, db.ForeignKey('workout_plan.id'), nullable=False)
    session_exercises = db.relationship('SessionExercise', backref='daily_session', lazy=True)

    def __repr__(self):
        return f"DailySession('{self.day_of_week}')"

class SessionExercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sets = db.Column(db.Integer, nullable=False)
    reps = db.Column(db.Integer, nullable=True)
    duration_min = db.Column(db.Integer, nullable=True)
    distance_km = db.Column(db.Float, nullable=True)
    daily_session_id = db.Column(db.Integer, db.ForeignKey('daily_session.id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercise.id'), nullable=False)
    exercise = db.relationship('Exercise', backref='session_exercises', lazy=True)

    def __repr__(self):
        return f"SessionExercise(Exercise ID: '{self.exercise_id}')"
    
class WeightInsert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    weight_kg = db.Column(db.Float, nullable=False)
    date_recorded = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"WeightInsert('{self.weight_kg}' at '{self.date_recorded}')"

class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    goal_type = db.Column(db.String(50), nullable=False)
    target_value = db.Column(db.Float, nullable=False)
    is_achieved = db.Column(db.Boolean, nullable=False, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Goal('{self.goal_type}' - '{self.target_value}')"