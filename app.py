from flask import Flask
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from db import db
from routes import bp

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secretKey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///workout.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'JWTsecretKey'

db.init_app(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

app.register_blueprint(bp)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)