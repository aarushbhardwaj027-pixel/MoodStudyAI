from flask import Flask, session, render_template, request, redirect
from auth.routes import auth_bp
from dashboard.routes import dashboard_bp
from extensions import db
import os

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

db_url = os.getenv('DATABASE_URL')
if db_url and db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')


@app.route('/')
def home():
    if 'user_id' in session:
        return redirect('/dashboard')
    return render_template('index.html')


with app.app_context():
    db.create_all()