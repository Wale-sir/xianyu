from flask_pymongo import PyMongo
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

mongo = PyMongo()
login_manager = LoginManager()
csrf = CSRFProtect()

def init_extensions(app):
    mongo.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    csrf.init_app(app) 