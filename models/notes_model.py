from extensions import db


class TopicNotes(db.Model):
    __tablename__ = "topic_notes"

    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    day_number   = db.Column(db.Integer, nullable=False)
    topic        = db.Column(db.String(255), nullable=False)
    summary      = db.Column(db.Text, nullable=True)
    key_points   = db.Column(db.Text, nullable=True)   # stored as JSON string
    formulas     = db.Column(db.Text, nullable=True)   # stored as JSON string
    remember     = db.Column(db.Text, nullable=True)   # stored as JSON string
    quick_recap  = db.Column(db.Text, nullable=True)
    created_at   = db.Column(db.DateTime, default=db.func.now())