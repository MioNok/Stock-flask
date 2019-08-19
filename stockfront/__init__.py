from flask import Flask
import sqlalchemy
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

import pandas as pd
import uuid


app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = '>SomeKey'
app.config['SQLALCHEMY_DATABASE_URI'] = '<SomeURI>'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category ="info"

from stockfront import routes