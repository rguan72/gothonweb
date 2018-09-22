from flask import render_template, flash, redirect, url_for, session, request
from app import app
from app.forms import LoginForm, RegistrationForm
import planisphere
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User
from werkzeug.urls import url_parse
from app import db


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc !='':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout', methods=['GET', 'POST'])
#@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route("/")
@app.route("/index")
def index():
    if current_user.is_anonymous:
        return redirect(url_for('login'))
    else:
        session['room_name'] = planisphere.START
        return redirect(url_for('game'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/game", methods=['GET', 'POST'])
@login_required
def game():
    room_name = session.get('room_name')

    if request.method == "GET":
        if room_name:
            room = planisphere.load_room(room_name)
            return render_template("show_room.html", room=room)
        else:
            # why is this here? do you need it?
            return render_template("show_death.html")
    else:
        action = request.form.get('action')

        if room_name and action:
            room = planisphere.load_room(room_name)
            next_room = room.go(action)

            if not next_room and room.name == "Laser Weapon Armory":
                if room.iters < 9:
                    print("room.iters is: " + str(room.iters))
                    room.iters = room.iters + 1
                    next_room = None
                else:
                    next_room = room.go('*')
            elif not next_room:
                next_room = room.go('*')


            if not next_room:
                session['room_name'] = planisphere.name_room(room)
            else:
                session['room_name'] = planisphere.name_room(next_room)

        return redirect(url_for("game")) # to create a loop
