from flask import Flask,session,render_template,request,redirect
from auth.routes import auth_bp
from dashboard.routes import dashboard_bp
from extensions import db
from models.user_model import User
from models.syllabus_model import StudyPlan

app = Flask(__name__)
app.secret_key = '111222333'

app.config['SQLALCHEMY_DATABASE_URI'] = r'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.register_blueprint(auth_bp,url_prefix = '/auth')
app.register_blueprint(dashboard_bp,url_prefix = '/dashboard')

db.init_app(app)

# =================================== HOME =============================
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect('/dashboard')
    
    return render_template('index.html')


# ===================================== start the app ============================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)