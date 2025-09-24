from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegistrationForm, LoginForm, TopicForm, ReplyForm
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///forum.db'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# -------------------- MODELS --------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    replies = db.relationship('Reply', backref='topic', lazy=True)

class Reply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'))

# -------------------- LOGIN MANAGER --------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -------------------- ROUTES --------------------
@app.route('/')
def index():
    topics = Topic.query.all()
    return render_template('index.html', topics=topics)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed = generate_password_hash(form.password.data)
        user = User(username=form.username.data, password=hashed)
        db.session.add(user)
        db.session.commit()
        flash("Account created! You can now log in.", "success")
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash("Logged in successfully.", "success")
            return redirect(url_for('index'))
        flash("Login failed. Check your username/password.", "danger")
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/forum/new', methods=['GET', 'POST'])
@login_required
def new_topic():
    form = TopicForm()
    if form.validate_on_submit():
        topic = Topic(title=form.title.data, content=form.content.data, user_id=current_user.id)
        db.session.add(topic)
        db.session.commit()
        flash("New topic created!", "success")
        return redirect(url_for('index'))
    return render_template('forum.html', form=form)

@app.route('/topic/<int:topic_id>', methods=['GET', 'POST'])
def topic(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    form = ReplyForm()
    if form.validate_on_submit():
        reply = Reply(content=form.content.data, user_id=current_user.id, topic_id=topic.id)
        db.session.add(reply)
        db.session.commit()
        return redirect(url_for('topic', topic_id=topic.id))
    return render_template('topic.html', topic=topic, form=form)

@app.route('/topic/<int:topic_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_topic(topic_id):
    topic = Topic.query.get_or_404(topic_id)

    # Only allow the user who created the topic to edit it
    if topic.user_id != current_user.id:
        flash("You are not allowed to edit this topic.", "danger")
        return redirect(url_for('topic', topic_id=topic.id))

    form = TopicForm(obj=topic)  # prefill form with existing data

    if form.validate_on_submit():
        topic.title = form.title.data
        topic.content = form.content.data
        db.session.commit()
        flash("Topic updated successfully!", "success")
        return redirect(url_for('topic', topic_id=topic.id))

    return render_template('edit_topic.html', form=form, topic=topic)
# -------------------- RUN APP --------------------

if __name__ == '__main__':
    if not os.path.exists("forum.db"):
        with app.app_context():
            db.create_all()
    app.run(debug=True)
