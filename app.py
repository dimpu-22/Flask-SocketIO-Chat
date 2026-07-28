from flask import Flask, render_template, request, redirect, session
from flask_socketio import SocketIO, emit
from database import db, User, Message

from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chat_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

socketio = SocketIO(app)
online_users = 0

@app.route('/')
def home():
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            return "Username already exists!"

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Create user
        new_user = User(
            username=username,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect('/login')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):

            session["username"] = username
            return redirect('/dashboard')

        return "Invalid Username or Password"

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/chat')
def chat():
    messages = Message.query.order_by(Message.timestamp.asc()).all()
    return render_template('chat.html', messages=messages)

from datetime import datetime

@socketio.on("send_message")
def handle_send_message(data):

    # Save message to database
    new_message = Message(
        sender=data["username"],
        receiver="General",
        room="General Chat",
        message=data["message"]
    )

    db.session.add(new_message)
    db.session.commit()

    current_time = datetime.now().strftime("%I:%M %p")

    emit(
        "receive_message",
        {
            "username": data["username"],
            "message": data["message"],
            "time": current_time
        },
        broadcast=True
    )
    
@socketio.on("connect")
def handle_connect():
    global online_users

    online_users += 1

    emit(
        "online_users",
        {"count": online_users},
        broadcast=True
    )

    emit(
        "receive_message",
        {
            "username": "System",
            "message": "A user joined the chat.",
            "time": datetime.now().strftime("%I:%M %p")
        },
        broadcast=True
    )

@socketio.on("disconnect")
def handle_disconnect():
    global online_users

    if online_users > 0:
        online_users -= 1

    emit(
        "online_users",
        {"count": online_users},
        broadcast=True
    )

    emit(
        "receive_message",
        {
            "username": "System",
            "message": "A user left the chat.",
            "time": datetime.now().strftime("%I:%M %p")
        },
        broadcast=True
    )
    
@socketio.on("typing")
def handle_typing(data):

    emit(
        "typing",
        {"username": data["username"]},
        broadcast=True,
        include_self=False
    )


@socketio.on("stop_typing")
def handle_stop_typing():

    emit(
        "stop_typing",
        broadcast=True,
        include_self=False
    )
    

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)
    
    
    