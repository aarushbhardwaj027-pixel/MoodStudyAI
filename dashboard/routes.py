from flask import Blueprint,render_template,request,redirect,session,jsonify
from models.syllabus_model import StudyPlan
from models.user_model import User
from models.StudySession import StudySession
from extensions import db
from utils.pdf_reader import extract_text_from_pdf
from utils.ai_planner import generate_plan
from utils.mood_logic import get_study_mode
from utils.ai_assistant import ask_study_ai,generate_welcome_message
from datetime import date, timedelta


dashboard_bp = Blueprint('dashboard',__name__)

# ================================= DASHBOARD ============================
@dashboard_bp.route('/')
def dashboard_home():

    if 'user_id' not in session:
        return redirect('/')

    user = User.query.get(session["user_id"])

    syllabus_exists = StudyPlan.query.filter_by(
        user_id=session["user_id"]
    ).first() is not None



    sessions = StudySession.query.filter_by(
        user_id=session["user_id"]
    ).all()

    total_days = StudyPlan.query.filter_by(
        user_id=session["user_id"]
    ).count()

    completed_days = len(set(
        s.day_number
        for s in sessions
        if s.focus_score is not None and s.focus_score > 0
    ))

    focus_values = [
        s.focus_score
        for s in sessions
        if s.focus_score is not None and s.focus_score > 0
    ]

    avg_focus = round(
        sum(focus_values) / len(focus_values),
        2
    ) if focus_values else 0


    progress_percent = int(
        (completed_days / total_days) * 100
    ) if total_days else 0

    return render_template(
        "dashboard.html",
        syllabus_exists=syllabus_exists,
        avg_focus=avg_focus,
        progress_percent=progress_percent,
        completed_days=completed_days,
        total_days=total_days,
        user=user
    )
# ===============================UPLAOD SYLLABUS==============================

@dashboard_bp.route('/upload_syllabus', methods=["POST"])
def upload():

    if 'user_id' not in session:
        return redirect('/')

    pdf_file = request.files.get('pdf_file')
    text_input = request.form.get('text_input')
    days = int(request.form["days"])

    syllabus = ""

    if pdf_file:
        syllabus = extract_text_from_pdf(pdf_file)

    elif text_input:
        syllabus = text_input

    else:
        return redirect('/dashboard')

    # GENERATE AI PLAN
    plan = generate_plan(syllabus, days=days)

    # SAVE TO DATABASE
    for day in plan:

        topics_text = "|||".join(day["topics"])

        study_plan = StudyPlan(

            day_number=day["day"],

            topic=topics_text,

            user_id=session["user_id"]
        )

        db.session.add(study_plan)

    db.session.commit()

    return redirect("/dashboard")

# ===============================VIEW PLAN==============================
@dashboard_bp.route('/view_plan')
def view_plan():

    if 'user_id' not in session:
        return redirect('/')

    mode = request.args.get("mode", "view")

    plans = StudyPlan.query.filter_by(
        user_id=session["user_id"]
    ).order_by(StudyPlan.day_number).all()

    formatted_plans = []

    for p in plans:

        topic_list = p.topic.split("|||")

        formatted_plans.append({
            "id": p.id,
            "day_number": p.day_number,
            "topics": topic_list,
            "status": p.status
        })

    return render_template(
        "study.html",
        plans=formatted_plans,
        mode=mode
    )

# ===============================STUDY PLANNER==============================

@dashboard_bp.route('/start_study/<int:day>', methods=["POST"])
def start_study(day):

    if 'user_id' not in session:
        return redirect('/')

    mood = request.form.get("mood")

    plan_items = StudyPlan.query.filter_by(
        user_id=session["user_id"],
        day_number=day
    ).all()

    topics = []

    for p in plan_items:

        split_topics = p.topic.split("|||")

        topics.extend(split_topics)

    study_mode = get_study_mode(mood, topics)

    return render_template(
        "study_session.html",
        study_mode=study_mode,
        day=day,
        mood=mood
    )
# ===============================MOOD PLANNER==============================


@dashboard_bp.route('/mood/<int:day>')
def mood_page(day):

    if 'user_id' not in session:
        return redirect('/')
    
    

    return render_template("mood.html", day=day)

# ===============================DELETE PLANNER==============================

@dashboard_bp.route('/delete_plan', methods=["POST"])
def delete_plan():

    if 'user_id' not in session:
        return redirect('/')

    plans = StudyPlan.query.filter_by(
        user_id=session["user_id"]
    ).all()

    for p in plans:
        db.session.delete(p)

    db.session.commit()

    return redirect('/dashboard')

# =============================== PROGRESS ===============================

@dashboard_bp.route('/progress')
def progress():

    if 'user_id' not in session:
        return redirect('/')


    plans = StudyPlan.query.filter_by(
        user_id=session["user_id"]
    ).order_by(StudyPlan.day_number).all()

    total_days = StudyPlan.query.filter_by(
        user_id=session["user_id"]
    ).count()

    sessions = StudySession.query.filter_by(
        user_id=session["user_id"]
    ).all()


    session_map = {
        s.day_number: s for s in sessions
    }

    completed_days = len(set(
        s.day_number
        for s in sessions
        if s.focus_score and s.focus_score > 0
    ))
  
    progress_percent = int(
        (completed_days / total_days) * 100
    ) if total_days else 0

    progress_data = []

    for p in plans:

        day_session = session_map.get(p.day_number)

        progress_data.append({
            "day": p.day_number,
            "focus_score": day_session.focus_score if day_session else 0,
            "pause_count": day_session.pause_count if day_session else 0,
            "status": "done" if day_session else "pending"
        })

    return render_template(
        "progress.html",
        total_days=total_days,
        completed_days=completed_days,
        progress_percent=progress_percent,
        progress=progress_data
    )
# =====================================focus calcualtor=======================
def calculate_focus_score(pause_count, total_pause_time, studied_seconds, total_study_seconds, max_streak):

    score = 100


    if pause_count > 5:
        score -= 20
    elif pause_count > 2:
        score -= 10
    elif pause_count > 0:
        score -= 5


    if studied_seconds > 0:
        pause_ratio = total_pause_time / studied_seconds

        if pause_ratio > 0.3:
            score -= 20
        elif pause_ratio > 0.15:
            score -= 10


    if total_study_seconds and total_study_seconds > 0:

        completion = (studied_seconds / total_study_seconds) * 100

        if completion < 20:
            score -= 70
        elif completion < 50:
            score -= 50
        elif completion < 90:
            score -= 20
    else:
        completion = 0
        score -= 30 

    if max_streak > 600:
        score += 15
    elif max_streak > 300:
        score += 8
    elif max_streak > 120:
        score += 3


    return max(0, min(100, score))
# =============================== COMPLETE DAY ===============================

@dashboard_bp.route('/complete_day/<int:day>', methods=["POST"])
def complete_day(day):

    if 'user_id' not in session:
        return redirect('/')

    focus_score = int(request.form.get("focus_score", 100))
    pause_count = int(request.form.get("pause_count", 0))
    total_pause_time = int(request.form.get("total_pause_time", 0))
    max_streak = int(request.form.get("max_streak", 0))
    mood = request.form.get("mood", "normal")
    session_time = int(request.form.get("session_time", 0))

    total_study_seconds = session_time  # from JS
    studied_seconds = max(session_time - total_pause_time, 0)

    focus_score = calculate_focus_score(
        pause_count=pause_count,
        total_pause_time=total_pause_time,
        studied_seconds=studied_seconds,
        total_study_seconds=total_study_seconds,
        max_streak=max_streak
    )

    plans = StudyPlan.query.filter_by(
        user_id=session["user_id"],
        day_number=day
    ).all()

    for p in plans:
        p.status = "done"

    session_entry = StudySession(
        user_id=session["user_id"],
        day_number=day,
        focus_score=focus_score,
        pause_count=pause_count,
        total_pause_time=total_pause_time,
        max_streak=max_streak,
        mood=mood,
        session_time=session_time
    )

    db.session.add(session_entry)

    db.session.commit()

    user = User.query.get(session["user_id"])

    today = date.today()

    yesterday = today - timedelta(days=1)

    if user.last_study_date is None:

        user.streak = 1

    else:

        last_date = date.fromisoformat(
            user.last_study_date
        )

        if last_date == yesterday:

            user.streak += 1

        elif last_date == today:

            pass

        else:

            user.streak = 1

    user.last_study_date = today.isoformat()

    db.session.commit()

    return redirect('/dashboard/view_plan?mode=study')

# =========================ANALYTICS==========================

@dashboard_bp.route('/analytics')
def analytics():

    if 'user_id' not in session:
        return redirect('/')

    sessions = StudySession.query.filter_by(
    user_id=session["user_id"]
    ).order_by(StudySession.day_number.asc()).all()

    if not sessions:
        return render_template(
            "analytics.html",
            best_mood=None,
            best_avg=0,
            max_streak=0,
            total_pauses=0,
            total_pause_time=0,
            avg_focus=0,
            plans_data=[]
        )


    plans_data = [
        {
            "day": s.day_number,
            "focus_score": s.focus_score or 0
        }
        for s in sessions
    ]

    avg_focus = sum(s.focus_score or 0 for s in sessions) / len(sessions)


    mood_scores = {}

    for s in sessions:
        if s.mood:
            mood_scores.setdefault(s.mood, []).append(s.focus_score or 0)

    best_mood = None
    best_avg = 0

    for mood, scores in mood_scores.items():
        avg = sum(scores) / len(scores)

        if avg > best_avg:
            best_avg = avg
            best_mood = mood


    max_streak = max((s.max_streak or 0 for s in sessions), default=0)

    total_pauses = sum(s.pause_count or 0 for s in sessions)

    total_pause_time = sum(s.total_pause_time or 0 for s in sessions)

    return render_template(
        "analytics.html",
        best_mood=best_mood,
        best_avg=round(best_avg, 2),
        max_streak=max_streak,
        total_pauses=total_pauses,
        total_pause_time=total_pause_time,
        avg_focus=round(avg_focus, 2),
        plans_data=plans_data,
        sessions=sessions 
    )

# ========================= DELETE ANALYTICS==========================
@dashboard_bp.route('/delete_session/<int:session_id>', methods=['POST'])
def delete_session(session_id):

    if 'user_id' not in session:
        return redirect('/')

    study_session = StudySession.query.get_or_404(session_id)

    if study_session.user_id != session["user_id"]:
        return redirect('/dashboard/analytics')

    deleted_day = study_session.day_number

    db.session.delete(study_session)
    db.session.commit()

    remaining_sessions = StudySession.query.filter_by(
        user_id=session["user_id"],
        day_number=deleted_day
    ).count()

    if remaining_sessions == 0:

        study_plan = StudyPlan.query.filter_by(
            user_id=session["user_id"],
            day_number=deleted_day
        ).first()

        if study_plan:
            study_plan.status = "pending"
            db.session.commit()

    return redirect('/dashboard/analytics')

# ================= AI ASSISTANT =================

@dashboard_bp.route("/ask_ai", methods=["POST"])
def ask_ai():

    if "user_id" not in session:
        return jsonify({
            "reply": "Please login first."
        })

    try:

        data = request.get_json()

        print(data)

        question = data.get("message")
        day = data.get("day")

        plans = StudyPlan.query.filter_by(
            user_id=session["user_id"],
            day_number=day
        ).all()

        topics = [p.topic for p in plans]

        print("TOPICS:", topics)

        answer = ask_study_ai(
            day,
            topics,
            question
        )

        print("ANSWER:", answer)

        return jsonify({
            "reply": answer
        })

    except Exception as e:

        print("AI ERROR:", e)

        return jsonify({
            "reply": "Backend AI error happened."
        })