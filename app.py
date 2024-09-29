# Imports
import sqlite3,os,dotenv,json
from flask import Flask, render_template, redirect, url_for, session, request, flash
from flask_bcrypt import Bcrypt
from authlib.integrations.flask_client import OAuth
import pickle
import ast

# LoadEnv
dotenv.load_dotenv()

# Gemini Setup
import google.generativeai as genai

gem_api = os.getenv('gem_api')
genai.configure(api_key=gem_api)

import typing_extensions as typing

class title(typing.TypedDict):
    is_topic : bool
    title  :str
class topics(typing.TypedDict):
    topic : str
# Create the model
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "application/json",
  "response_schema" : list[title]
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
  # safety_settings = Adjust safety settings
  # See https://ai.google.dev/gemini-api/docs/safety-settings
  system_instruction="given the prompt or topic given by user return the title for the topic in the format {is_topic : True ,title:\"title\"} only if the given prompt is a topic or concept otherwise return {is_topic : false , title : Null}",
)
model3 = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  # safety_settings = Adjust safety settings
  # See https://ai.google.dev/gemini-api/docs/safety-settings
  system_instruction="given the topic list return only the list of the moderately related topics to the target topic in format ['topic1','topic2','topic3'] maximum 3 return [nothing] if none is related close enough",
)

model2 = None

# Pre_Setup
app = Flask(__name__)
bcrypt = Bcrypt(app)
oauth = OAuth(app)

# ENV_Setup
app.config['SECRET_KEY'] = os.getenv('secret_key')  # Important for session management
app.config['GOOGLE_CLIENT_ID'] =  os.getenv('google_client_id')  # Replace with your Client ID
app.config['GOOGLE_CLIENT_SECRET'] =  os.getenv('google_client_secret')  # Replace with your Client Secret


# Google Oauth
google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    redirect_uri='http://localhost:5000/login/callback',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid profile email'},
)

# Initialize database
def init_db():
    with sqlite3.connect('users.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT
            )
        ''')
        conn.commit()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                message TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.execute('''
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            chat_session BLOB,
            relevent_topics TEXT
            )
        ''')
        conn.commit()

init_db()


# ROUTES
@app.route('/')
def index():
    return render_template('welcome.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')


@app.route('/login_post', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')

    with sqlite3.connect('users.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()

    if user and bcrypt.check_password_hash(user[0], password):
        session['username'] = username
        return redirect(url_for('dashboard'))
    return redirect(url_for('index'))

@app.route('/dashboard', methods=['POST', 'GET'])
def dashboard():
    if 'username' not in session:
        return redirect(url_for('index'))
    
    # Fetch all topics for the logged-in user
    with sqlite3.connect('users.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT topic, id FROM topics WHERE user_id = (SELECT id FROM users WHERE username = ?)", (session["username"],))
        data = cursor.fetchall()

    if request.method == 'POST':
        session['id'] = request.form['flag']  # Store selected topic ID in session
        
        # Load the chat session for the selected topic
        with sqlite3.connect('users.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT chat_session, topic FROM topics WHERE id = ?", (session['id'],))
            row = cursor.fetchone()
            blobbed_chat_session, topic = row
            
            # Check if chat history exists, if not start a new session
        data2 = ""
        with sqlite3.connect('users.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT relevent_topics FROM topics WHERE id = ?", (session["id"],))
            data2 = cursor.fetchall()
        topic_string = ""
        for i in data2:
            topic_string = topic_string + i[0] 
        topic_list = ast.literal_eval(topic_string)
        topic_string =  ""
        topic_string += ",".join(topic_list)
        # Initialize model2 with the selected topic
        global model2
        model2 = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=f"""
            Assume you are a teacher teaching a student only topic {topic}. 
            provided that you taught the student about {topic_string}.
            if the student ask for the topic list
            say to student  'assuming that you have studied {topic_string} topics well and ask student to correct you if they have not
              studied the any of the topics in {topic_string}.'
            and give them topic list.
            topic list must include the connection to {topic_string}.
            follow the topic list and teach the topic in an interactive way
            if any of that is relevant deliver the it like an lecture of personl tutor in bite size may 
            three for line before moving next and then do something interactive maybe ask him if he understood 
            what you taught maybe ask him a question ask him to do some activity.if student ask question then 
            Only answer questions relevant to the topic.
            If a question is not relelated to topic, ask the user to ask a relevant question.
            if the user ask you teach other topic tell them you cant.
            """
        )
        if blobbed_chat_session:
                global chat_session
                chat_history = pickle.loads(blobbed_chat_session)
                chat_session = model2.start_chat(history=chat_history)
        else:
                chat_session = model2.start_chat(history=[])
                chat_session.send_message(f"tell me  list of topics you will teach me about the {topic}")
                session_update()
        return render_template("dashboard.html", data=data, flag=topic)
    
    else:
        return render_template("dashboard.html", data=data, flag='false')
    
@app.route('/chat_history', methods=['POST'])
def chat_history():
    history = []
    for i in chat_session.history:
        history_dictionary = {}
        history_dictionary['role'] = i.role
        if i.role == "model":
            history_dictionary["role"] = "bot"
        history_dictionary['message'] = i.parts[0].text
        history.append(history_dictionary)
    return history


    
@app.route('/session_update', methods=['POST'])
def session_update():
    topic_id = session['id']
    
    # Serialize the current chat session's history
    blobbed_chat_session = pickle.dumps(chat_session.history)
    
    # Update the chat session in the database
    with sqlite3.connect('users.db') as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE topics SET chat_session = ? WHERE id = ?', (blobbed_chat_session, topic_id))
        conn.commit()
    
    return "done", 200

    
@app.route('/chat_add',methods=["POST"])
def chat_add():
    if "flag" in request.form:
        topic_list = ""
        with sqlite3.connect('users.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT topic from topics where user_id = (select id from users where username = ?)',(session["username"],))
            topic_list = str(cursor.fetchall())
        topic = title_generator(request.form["topic"])
        relevent_topics = most_relevent(topic,topic_list)
        with sqlite3.connect('users.db') as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO topics (topic, user_id,relevent_topics) VALUES (?, (select id from users where username = ?),?)', (topic, session["username"],relevent_topics))
            conn.commit()
            return redirect(url_for('dashboard'))

def title_generator(topic):
    response = model.generate_content(topic)
    response_data = json.loads(str(response.candidates[0].content.parts[0].text))
    title = response_data[0]['title']
    return title
def most_relevent(topic,topic_list):
    prompt ="target: '"+ topic + "', topics: "+ topic_list
    response = model3.generate_content(prompt)
    return str(response.candidates[0].content.parts[0].text)


@app.route('/reply', methods=['POST'])
def reply():
    data = request.get_json()
    query = data.get('query', '')
    
    # Generate a response using the current session's model (model2)
    response = chat_session.send_message(query)
    
    
    # Save the updated chat session history in the database
    session_update()  # Call the session_update to persist the history
    
    return response.text


@app.route('/register_post', methods=['POST'])
def register_post():
    username = request.form.get('username')
    password = request.form.get('password')
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    try:
        with sqlite3.connect('users.db') as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('index'))
    except sqlite3.IntegrityError:
        flash('Username already exists', 'danger')
        return redirect(url_for('index'))

@app.route('/login/google')
def login_google():
    redirect_uri = url_for('google_authorized', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/login/callback')
def google_authorized():
    token = google.authorize_access_token()
    user_info = token['userinfo']
    email = user_info['email']

    with sqlite3.connect('users.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT username FROM users WHERE username = ?', (email,))
        user = cursor.fetchone()

        if user:
            session['username'] = email
            return redirect(url_for('dashboard'))

        # Register new user
        cursor.execute('INSERT INTO users (username) VALUES (?)', (email,))
        conn.commit()
        session['username'] = email
        return redirect(url_for('dashboard'))

    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route("/suggestions")
def suggestions():
    name = request.args.get('name')
    email = request.args.get('email')
    suggestion = request.args.get('message')
    with sqlite3.connect('users.db') as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO suggestions (name, email,message) VALUES (?, ?,?)', (name, email,suggestion))
        conn.commit()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run()