from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv
from website.views import views

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

app.register_blueprint(views, url_prefix='/')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
