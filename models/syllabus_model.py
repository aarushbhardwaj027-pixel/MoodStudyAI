from extensions import db

class StudyPlan(db.Model):
    __tablename__ = 'study_plan'

    id = db.Column(db.Integer, primary_key=True)

    day_number = db.Column(db.Integer, nullable=False)
    topic = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default="not done")
    focus_score = db.Column(db.Integer, default=0)
    pause_count = db.Column(db.Integer, default=0)
    total_pause_time = db.Column(db.Integer, default=0)
    max_streak = db.Column(db.Integer, default=0)
    mood = db.Column(db.String(20), default="normal")
    session_time = db.Column(db.Integer, default=0)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
