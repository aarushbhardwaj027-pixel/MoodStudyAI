from flask import render_template, request, redirect, Blueprint, session,flash
from models.user_model import db, User
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy.exc import IntegrityError

auth_bp = Blueprint('auth', __name__)

# __________________ LOGIN __________________

@auth_bp.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(username=username,email = email).first()

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            flash("Login successful!", "success")
            return redirect("/dashboard")

        return redirect('/auth/login')

    return render_template('login.html')


# __________________ SIGNUP __________________

@auth_bp.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == "POST":
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        current_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if current_user:
            flash("User already exists!", "error")
            return redirect('/auth/signup')

        encoded = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

        user = User(username=username, email=email, password=encoded)

        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return redirect('/auth/signup')
        
        flash("Account created successfully!", "success")
        return redirect('/auth/login')

    return render_template('signup.html')


# __________________ LOGOUT __________________

@auth_bp.route("/logout")
def logout():
    session.pop('user_id', None)
    return redirect("/")