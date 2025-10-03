from flask import Flask
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_smorest import Api

from db import db
from routes import blp

app = Flask(__name__)

app.config['SECRET_KEY'] = 'secretKey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///workout.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'JWTsecretKey'

app.config["API_TITLE"] = "Workout-API"
app.config["API_VERSION"] = "v1"
app.config["OPENAPI_VERSION"] = "3.1.1"
app.config["OPENAPI_URL_PREFIX"] = "/" 
app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"


db.init_app(app)
bcrypt = Bcrypt()
jwt = JWTManager()
api = Api(app)

with app.app_context():
    bcrypt.init_app(app)
    jwt.init_app(app)

api.register_blueprint(blp)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)