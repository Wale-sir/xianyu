from flask_pymongo import PyMongo
from flask_login import LoginManager

mongo = PyMongo()
login_manager = LoginManager()

def init_extensions(app):
    mongo.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login' 