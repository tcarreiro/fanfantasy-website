from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
import os
from dotenv import load_dotenv
from website.views import views
from website.auth import auth
from website.models import User, Note

load_dotenv()

db = SQLAlchemy()
DB_NAME = 'database.db'

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
db.init_app(app)
app.register_blueprint(views, url_prefix='/')
app.register_blueprint(auth, url_prefix='/')

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
