from flask import Blueprint,render_template,request,redirect,session,jsonify
from models.syllabus_model import StudyPlan
from models.user_model import User
from models.StudySession import StudySession
from models.notes_model import TopicNotes
from models.ai_score import AITest
from extensions import db
from utils.pdf_reader import extract_text_from_pdf
from utils.ai_planner import generate_plan
from utils.mood_logic import get_study_mode
from utils.ai_assistant import ask_study_ai,generate_welcome_message
from utils.ai_tutor import generate_ai_tutor_content,generate_more_mcqs,generate_notes,generate_qa
from datetime import date, timedelta
import json


dashboard_bp = Blueprint('dashboard',__name__)

# ================================= DASHBOARD ============================
@dashboard_bp.route('/')
def dashboard_home():
    if 'user_id' not in session:
        return redirect('/')

    user = User.query.get(session["user_id"])

    if user.last_study_date:
        last_date = date.fromisoformat(user.last_study_date)
        if (date.today() - last_date).days > 1:
            user.streak = 0
            db.session.commit()

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
        sum(focus_values) / len(focus_values), 2
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

    plan = generate_plan(syllabus, days=days)

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

    user_id = session["user_id"]

    AITest.query.filter_by(user_id=user_id).delete()
    TopicNotes.query.filter_by(user_id=user_id).delete()
    StudySession.query.filter_by(user_id=user_id).delete()
    StudyPlan.query.filter_by(user_id=user_id).delete()

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

    session_map = {}
    for s in sessions:
        if s.day_number not in session_map:
            session_map[s.day_number] = s
        else:
            if (s.focus_score or 0) > (session_map[s.day_number].focus_score or 0):
                session_map[s.day_number] = s

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

    total_study_seconds = session_time  
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
 
    AITest.query.filter_by(
        user_id=session["user_id"],
        day_number=day,
        session_id=None
    ).update({"session_id": session_entry.id})

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

    plans = StudyPlan.query.filter_by(
        user_id=session["user_id"]
    ).order_by(StudyPlan.day_number.asc()).all()

    sessions = StudySession.query.filter_by(
        user_id=session["user_id"]
    ).order_by(StudySession.day_number.asc()).all()

    all_days = sorted(set(
        [p.day_number for p in plans] +
        [s.day_number for s in sessions]
    ))

    focus_by_day = {}

    for s in sessions:
        focus_by_day.setdefault(s.day_number, []).append(s.focus_score or 0)

    plans_data = []

    for day in all_days:
        scores = focus_by_day.get(day, [])
        avg_day_focus = round(sum(scores) / len(scores), 2) if scores else 0

        plans_data.append({
            "day": day,
            "focus_score": avg_day_focus
        })

    if not sessions:
        return render_template(
            "analytics.html",
            best_mood=None,
            best_avg=0,
            max_streak=0,
            total_pauses=0,
            total_pause_time=0,
            avg_focus=0,
            plans_data=plans_data,
            sessions=[]
        )

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

    AITest.query.filter_by(
        user_id=session["user_id"],
        session_id=session_id
    ).delete()

    TopicNotes.query.filter_by(
        user_id=session["user_id"],
        day_number=deleted_day
    ).delete()


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
    

#================================AI TUTOR===============================

@dashboard_bp.route('/get_tutor_data', methods=["POST"])
def get_tutor_data():

    if 'user_id' not in session:
        return redirect('/')
    try:

        data = request.get_json()

        mood      = data.get("mood")
        topics    = data.get("topics")    
        intensity = data.get("intensity") 
        day       = data.get("day")

        tutor_data = generate_ai_tutor_content(
            mood=mood,
            topics=topics,
            intensity=intensity
        )

        return jsonify(tutor_data)

    except Exception as e:
        print("Tutor AI Error:", e)
        return jsonify({"error": str(e)})
    
#========================SAVE TEST DATA=====================

@dashboard_bp.route('/save_ai_test', methods=["POST"])
def save_ai_test():

    if 'user_id' not in session:
        return redirect('/')

    data = request.get_json()
    print("=== SAVING TEST ===", data)

    test = AITest(
        user_id         = session["user_id"],
        day_number      = data.get("day"),
        topic           = data.get("topic"),
        score           = data.get("score"),
        total_questions = data.get("total_questions"),
        correct_answers = data.get("correct_answers"),
        wrong_answers   = data.get("wrong_answers"),
        answers_json    = data.get("answers_json")
    )

    db.session.add(test)
    db.session.commit()

    return jsonify({"status": "saved"})

#========================DISPLAY TEST DATA=====================
@dashboard_bp.route('/test_score')
def ai_scores():

    if 'user_id' not in session:
        return redirect('/')

    tests = AITest.query.filter_by(
        user_id=session["user_id"]
    ).order_by(AITest.day_number.asc()).all()

    if not tests:
        return render_template("test_score.html", days=[], avg_score=0, best_topic=None, total_tests=0, chart_data=[])

    days_dict = {}
    for t in tests:
        key = t.session_id or t.day_number
        if key not in days_dict:
            days_dict[key] = []
        days_dict[key].append(t)

    days_data = []
    for key, day_tests in days_dict.items():
        avg  = round(sum(t.score for t in day_tests) / len(day_tests), 1)
        best = max(day_tests, key=lambda t: t.score)
        days_data.append({
            "day":         day_tests[0].day_number,
            "avg_score":   avg,
            "topics":      day_tests,
            "topic_count": len(day_tests),
            "best_topic":  best.topic.split("::")[0].strip(),
            "best_score":  best.score
        })

    days_data.sort(key=lambda d: d["day"])

    total_tests = len(tests)
    avg_score   = round(sum(t.score for t in tests) / total_tests, 1)
    best        = max(tests, key=lambda t: t.score)
    chart_data  = [{"day": d["day"], "score": d["avg_score"]} for d in days_data]

    return render_template(
        "test_score.html",
        days        = days_data,
        avg_score   = avg_score,
        best_topic  = best.topic.split("::")[0].strip(),
        best_score  = best.score,
        total_tests = total_tests,
        chart_data  = chart_data
    )

# =========================DELETE TEST=============================

@dashboard_bp.route('/delete_test_day/<int:day>', methods=["POST"])
def delete_test_day(day):
    if 'user_id' not in session:
        return redirect('/')

    AITest.query.filter_by(
        user_id=session["user_id"],
        day_number=day
    ).delete()

    db.session.commit()
    return redirect('/dashboard/test_score')

# =========================QA=============================

@dashboard_bp.route('/generate_qa', methods=["POST"])
def get_qa():
 
    if 'user_id' not in session:
        return redirect('/')
 
    try:
        data      = request.get_json()
        topic     = data.get("topic")
        intensity = data.get("intensity")
        result    = generate_qa(topic, intensity)
        return jsonify(result)
    except Exception as e:
        print("QA Error:", e)
        return jsonify({"error": str(e)})
 
 
# =========================MCQ=============================
 
@dashboard_bp.route('/generate_more_mcqs', methods=["POST"])
def get_more_mcqs():
 
    if 'user_id' not in session:
        return redirect('/')
 
    try:
        data      = request.get_json()
        topic     = data.get("topic")
        intensity = data.get("intensity")
        result    = generate_more_mcqs(topic, intensity)
        return jsonify(result)
    except Exception as e:
        print("More MCQ Error:", e)
        return jsonify({"error": str(e)})
 
 
# =======================NOTES=============================
 
@dashboard_bp.route('/save_notes', methods=["POST"])
def save_notes():
    if 'user_id' not in session:
        return redirect('/')

    try:
        data      = request.get_json()
        topic     = data.get("topic")
        day       = data.get("day")
        intensity = data.get("intensity")
        mood      = data.get("mood")

        if topic and "::" in topic:
            topic = topic.split("::")[0].strip()

        existing = TopicNotes.query.filter_by(
            user_id    = session["user_id"],
            day_number = day,
            topic      = topic
        ).first()

        if existing:
            return jsonify({"status": "already_exists"})

        notes = generate_notes(topic, intensity, mood)

        entry = TopicNotes(
            user_id     = session["user_id"],
            day_number  = day,
            topic       = topic,
            summary     = notes.get("summary", ""),
            key_points  = json.dumps(notes.get("key_points", [])),
            formulas    = json.dumps(notes.get("important_formulas", [])),
            remember    = json.dumps(notes.get("remember", [])),
            quick_recap = notes.get("quick_recap", "")
        )

        db.session.add(entry)
        db.session.commit()

        return jsonify({"status": "saved", "notes": notes})

    except Exception as e:
        print("Notes Error:", e)
        return jsonify({"error": str(e)})
    

# ======================VIEW NOTES==============================
 
@dashboard_bp.route('/notes')
def notes_page():
 
    if 'user_id' not in session:
        return redirect('/')
 
    all_notes = TopicNotes.query.filter_by(
        user_id=session["user_id"]
    ).order_by(TopicNotes.day_number.asc()).all()
 
    days_dict = {}
    for n in all_notes:
        if n.day_number not in days_dict:
            days_dict[n.day_number] = []
        days_dict[n.day_number].append(n)
 
    days_data = []
    for day_num, notes_list in days_dict.items():
        parsed = []
        for n in notes_list:
            parsed.append({
                "id":          n.id,
                "topic":       n.topic.split("::")[0].strip(),
                "summary":     n.summary,
                "key_points":  json.loads(n.key_points or "[]"),
                "formulas":    json.loads(n.formulas or "[]"),
                "remember":    json.loads(n.remember or "[]"),
                "quick_recap": n.quick_recap,
                "created_at":  n.created_at
            })
        days_data.append({
            "day":   day_num,
            "notes": parsed,
            "count": len(parsed)
        })
 
    return render_template("notes.html", days=days_data)

# =======================DELETE NOTES=============================

@dashboard_bp.route('/delete_notes/<int:id>',methods = ['POST'])
def delete_notes(id):
    if 'user_id' not in session:
        return redirect('/') 
    
    note = TopicNotes.query.get_or_404(id)
    
    if note.user_id != session["user_id"]:
        return redirect('/dashboard/notes')
    
    db.session.delete(note)
    db.session.commit()
    
    return redirect('/dashboard/notes')

#========================NOTES EXISTS==========================

@dashboard_bp.route('/notes_exist', methods=["POST"])
def notes_exist():
    if 'user_id' not in session:
        return jsonify({"exists": False})

    data = request.get_json()
    topic = data.get("topic", "")
    day = data.get("day")

    if topic and "::" in topic:
        topic = topic.split("::")[0].strip()

    exists = TopicNotes.query.filter_by(
        user_id=session["user_id"],
        day_number=day,
        topic=topic
    ).first() is not None

    return jsonify({"exists": exists})