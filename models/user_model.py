from extensions import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120) , nullable = False)
    streak = db.Column(db.Integer, default=0)

    last_study_date = db.Column(db.String(50), nullable=True)
    
    study_plans = db.relationship('StudyPlan', backref='user', lazy=True)
