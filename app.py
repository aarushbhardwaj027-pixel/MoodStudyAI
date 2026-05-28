from flask import Flask, session, render_template, request, redirect
from auth.routes import auth_bp
from dashboard.routes import dashboard_bp
from extensions import db
import os

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')


# HOME ROUTE
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect('/dashboard')
    return render_template('index.html')


with app.app_context():
    db.create_all()


if __name__ != "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))