from extensions import db

class StudySession(db.Model):
    __tablename__ = "study_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    day_number = db.Column(db.Integer, nullable=False)
    focus_score = db.Column(db.Integer, default=0)
    max_streak = db.Column(db.Integer, default=0)
    pause_count = db.Column(db.Integer, default=0) 
    total_pause_time = db.Column(db.Integer, default=0)
    session_time = db.Column(db.Integer, default=0)
    mood = db.Column(db.String(50))

    created_at = db.Column(db.DateTime, default=db.func.now())