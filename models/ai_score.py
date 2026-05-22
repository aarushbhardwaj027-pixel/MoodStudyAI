from extensions import db


class AITest(db.Model):
    __tablename__ = "ai_tests"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    day_number = db.Column(db.Integer, nullable=False)

    session_id = db.Column(db.Integer, db.ForeignKey("study_sessions.id"), nullable=True)

    topic = db.Column(db.String(255), nullable=False)

    score = db.Column(db.Integer, default=0)  
    total_questions = db.Column(db.Integer, default=5)

    correct_answers = db.Column(db.Integer, default=0)
    wrong_answers = db.Column(db.Integer, default=0)

    answers_json = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=db.func.now())