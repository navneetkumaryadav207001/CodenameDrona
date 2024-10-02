# Imports
import sqlite3,os,dotenv,json
from flask import Flask, render_template, redirect, url_for, session, request, flash,jsonify
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



# Create the model
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "application/json",
  "response_schema" : list[title]
}
generation_config2 = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "application/json",
  "response_schema" : int
}


model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
  # safety_settings = Adjust safety settings
  # See https://ai.google.dev/gemini-api/docs/safety-settings
  system_instruction="given the prompt or topic given by user return the title for the topic in the format {is_topic : True ,title:\"title\"} only if the given prompt is a topic or concept otherwise return {is_topic : false , title : NOTHING} title may contain an appropriate emoji",
)
model3 = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  # safety_settings = Adjust safety settings
  # See https://ai.google.dev/gemini-api/docs/safety-settings
  system_instruction="given the topic list return only the list of the moderately related topics to the target topic in format ['topic1','topic2','topic3'] maximum 3 return ['nothing'] if none is related close enough",
)
model4 = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  # safety_settings = Adjust safety settings
  # See https://ai.google.dev/gemini-api/docs/safety-settings
  system_instruction="given the prompt return yes if the prompt explicitly says the basics of topic are complete or skipped and user need to move to advanced level",
)
model6 = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  # safety_settings = Adjust safety settings
  # See https://ai.google.dev/gemini-api/docs/safety-settings
  system_instruction="high-priority-note -always return a int, given the prompt return blooms taxonomy level number(int) if prompt means the current level is done and we are moving to next return in format 'int' else return 0 return 7 if the last level of booms taxonomy is done",
)
model7 = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  # safety_settings = Adjust safety settings
  # See https://ai.google.dev/gemini-api/docs/safety-settings
  system_instruction="""given the name of the topic return the json with right formatting for the assignment and lab on the basis of levels of blooms taxonomy of the topic each assignments 
  and lab contains 5 questions you can take text input by giving empty options list for question that need text answers
  for lab give some text and ask for the report 
  {
    "assignments": {
        "bloom_level1": [
            {
                "question": "What is the capital of France?",
                "options": ["Paris", "London", "Berlin", "Madrid"],
                "correctAnswer": "Paris"
            },
            {
                "question": "Which planet is known as the Red Planet?",
                "options": ["Earth", "Mars", "Jupiter", "Saturn"],
                "correctAnswer": "Mars"
            }
            #add three more questions
        ],
        "bloom_level2": [
            {
                "question": "What is 2 + 2?",
                "options": ["3", "4", "5", "6"],
                "correctAnswer": "4"
            },
            {
                "question": "What is the largest mammal?",
                "options": ["Elephant", "Blue Whale", "Giraffe", "Rhino"],
                "correctAnswer": "Blue Whale"

            }
            #add three more questions
        ]
        # Add all levels till level 6
    },
    "labs": {
        "bloom_level1": [
            {
                "question": "Perform the Map Excercise and submit the report excercise details:map everything",
                "options": [],
                "correctAnswer": "no correct answer "
            },
        ],
        "bloom_level2": [
            {
                "question": "Take this code and run in your code editor and tell what do you see code:<#include>",
                "options": [],
                "correctAnswer": "no correct answer"
            },
        ]
        # Add all levels till level 6
    }
}
""",
)
model8 = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config2,
  # safety_settings = Adjust safety settings
  # See https://ai.google.dev/gemini-api/docs/safety-settings
  system_instruction="""important return only one number ,given the questions 
  and users answer to those questions return the final score of how many question
    are right do a very hard checking like mit proffesor note ignore the 
  right answer list in questions list in questions where task are to be done for example devloping something
    only saying that i have done it is not enough give marks only if they provide a solid proof
    you can only return between zero and number of questions if user dont answer anything return zero""",
)



model2 = None
model5= None

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
            relevent_topics TEXT,
            level INTEGER NOT NULL DEFAULT 1,
            assignments TEXT
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
    if 'username' in session:
        return redirect(url_for('dashboard'))
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
            cursor.execute("SELECT relevent_topics,level FROM topics WHERE id = ?", (session["id"],))
            data2 = cursor.fetchall()
        
        level = data2[0][1]
        teach_model = None
        if(level == 1):
            topic_string = ""
            for i in data2:
                topic_string = topic_string + i[0] 
            topic_list = ast.literal_eval(topic_string)
            topic_string =  ""
            topic_string += ",".join(topic_list)
            # Initialize model2 with the selected topic
            teach_model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=f"""
                use emojis while talking
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
                if you have taught everything from the {topic_string} or user ask to skip move to the next part which is blooms taxonomy levels and
                reply 'basics are complete and move to blooms taxonomy level:rememebering ask them if they are ready for level 1 of blooms taxonomy'.
                HIGHT NOTE -> after every three non topic related chats ask student to return to topic do not teach or talk anything other than {topic}
                """)
        else:
            teach_model = genai.GenerativeModel(
                                model_name="gemini-1.5-flash",
                                # safety_settings = Adjust safety settings
                                # See https://ai.google.dev/gemini-api/docs/safety-settings
                                system_instruction=f"""
                                 Complete each action one by one for all six levels of Bloom's Taxonomy.
                                 when user ask to start say okay lets start and start teaching
                                 tell the user when one level is complete and say current level is done we are moving to next level
                                 important:-changing the level,skipping the level in any manner is not allowed just say changing the level is not allowed in short user cannot control the level even can query about so
                                 HIGHT NOTE -> after every three non topic related chats ask student to return to topic
                                 do not teach or talk anything other than {topic}
                                 use emojis whilte talking
Level 1: Remembering
Teach the student on level one of Bloom's Taxonomy (Facts):
Start by introducing the basic facts related to {topic}. Use various techniques such as interactive questions, visual aids, and mnemonic devices to help them remember key information. Take your time, using 10-20 interactive bites to ensure they grasp everything relevant. Encourage them to summarize the information in their own words and share tips for remembering.

Test the students on level one:
After teaching, ask the student multiple-choice or short-answer questions to assess their knowledge of the facts. Ensure they complete these in a short time frame. Once they finish, provide the correct answers so they can check their understanding.

Level 2: Understanding
Teach the student on level two (Understanding):
Explain the concepts and principles behind {topic}. Use examples and analogies to help the student grasp the meaning and implications of the information. Encourage them to ask questions for clarity.

Test the students on level two:
Ask the student to explain the concepts in their own words. You can present case studies or scenarios related to {topic} and have them analyze the situation. Provide feedback on their explanations.

Level 3: Applying
Teach the student on level three (Applying):
Present practical applications of {topic}. Engage them in exercises where they can apply their knowledge to solve problems or real-world situations.

Test the students on level three:
ask them to do something practical apply knowledge
Give them scenarios or problems related to {topic} and ask how they would apply their knowledge to address these situations. Review their responses together.

Level 4: Analyzing
Teach the student on level four (Analyzing):
Help the student break down complex ideas related to {topic} into smaller parts. Discuss the relationships between different concepts and encourage critical thinking.

Test the students on level four:
Pose analytical questions where they must differentiate between various aspects of {topic}. Encourage them to identify patterns, causes, and effects.

Level 5: Evaluating
Teach the student on level five (Evaluating):
Discuss criteria for evaluating information related to {topic}. Provide examples of good versus poor analysis and encourage the student to express their opinions on different perspectives.

Test the students on level five:
Ask them to critique a piece of information or an argument related to {topic}. Have them provide justifications for their evaluations.

Level 6: Creating
Teach the student on level six (Creating):
Encourage the student to synthesize their knowledge of {topic} into new ideas or projects. Discuss the importance of creativity in applying what they've learned.

Test the students on level six:
Have the student design a project, presentation, or experiment related to {topic}. Review their plans and provide constructive feedback.

Level 7(last level): Socratic level(never-ending)
Ask them to ask any question and answer them with a question leading to answer.
Reminder: After five non-action-related chats, I'll prompt you to return to the actions for further learning and testing on Bloom's Taxonomy levels.

                                 """,
                                )
        
        if blobbed_chat_session:
                global chat_session
                chat_history = pickle.loads(blobbed_chat_session)
                chat_session = teach_model.start_chat(history=chat_history)
        else:
                chat_session = teach_model.start_chat(history=[])
                chat_session.send_message(f"tell me  list of topics you will teach me about the {topic}")
                session_update()
        return render_template("dashboard.html", data=data, flag=topic,level = level)
    
    else:
        return render_template("dashboard.html", data=data, flag='false',level=1)
    
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
        if(topic == "NOTHING"):
            return redirect(url_for('dashboard'))
        relevent_topics = most_relevent(topic,topic_list)
        assignments = assignment_generator(topic)
        with sqlite3.connect('users.db') as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO topics (topic, user_id,relevent_topics,level,assignments) VALUES (?, (select id from users where username = ?),?,?,?)', (topic, session["username"],relevent_topics,1,assignments))
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
def assignment_generator(topic):
    response = model7.generate_content(topic)
    return str(response.candidates[0].content.parts[0].text)

@app.route('/assignments')
def assignments():
    topic =""
    with sqlite3.connect('users.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT topic from topics where id = ?',(session["id"],))
            topic = str(cursor.fetchall()[0][0])
    return render_template('assignments.html',topic=topic)


@app.route('/assignments_api',methods=['POST'])
def assignments_api():
    data = request.get_json()  # Get the JSON data from the request
    test_type = data.get('test_type')  # Extract 'test_type'
    bloom_level = data.get('bloom_level') 
    assignments = ""
    with sqlite3.connect('users.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT assignments from topics where id = ?',(session["id"],))
            assignments = str(cursor.fetchall()[0][0])
    assignments = assignments.replace("```","")
    assignments = assignments.replace("json","")
    assignments= json.loads(assignments)
    questions = assignments[test_type][bloom_level]
    return jsonify({"questions": questions})


@app.route('/reply', methods=['POST'])
def reply():
    data = request.get_json()
    query = data.get('query', '')
    
    # Generate a response using the current session's model (model2)
    response = chat_session.send_message(query)
    response2 = model4.generate_content(response.candidates[0].content.parts[0].text)
    response2 = str(response2.candidates[0].content.parts[0].text)
    level = 1
    with sqlite3.connect('users.db') as conn:
            cursor = conn.cursor()
            cursor.execute('select level from topics WHERE id = ?', (session['id'],))
            level = cursor.fetchone()[0]
    if "yes" in response2 and level == 1:
        with sqlite3.connect('users.db') as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE topics SET level = ? WHERE id = ?', (2, session['id']))
            conn.commit()
        with sqlite3.connect('users.db') as conn:
            cursor = conn.cursor()
            cursor.execute('select topic from topics WHERE id = ?', (session['id'],))
            topic = cursor.fetchone()[0]
            conn.commit()
            session_update() 
            return jsonify({'redirect': url_for('dashboard'),'topic':topic,'id':session['id']})
    else:
        response3 = model6.generate_content(response.candidates[0].content.parts[0].text)
        response3 = str(response3.candidates[0].content.parts[0].text)
        try:
            if int(response3) and level>1 and int(response3) == level:
                    with sqlite3.connect('users.db') as conn:
                        cursor = conn.cursor()
                        cursor.execute('UPDATE topics SET level = ? WHERE id = ?', (int(response3)+1,session['id']))
                        conn.commit()
                    with sqlite3.connect('users.db') as conn:
                        cursor = conn.cursor()
                        cursor.execute('select topic from topics WHERE id = ?', (session['id'],))
                        topic = cursor.fetchone()[0]
                        conn.commit()
                        session_update() 
                        return jsonify({'redirect': url_for('dashboard'),'topic':topic,'id':session['id']})
        except ValueError:
            pass

    
    # Save the updated chat session history in the database
    session_update()  # Call the session_update to persist the history
    return response.text
@app.route('/check_answers',methods=['POST'])
def check_answers():
    data = request.get_json()  # Get the JSON data from the request
    questions = data.get('questions')  # Extract 'test_type'
    answers = data.get('answers')
    prompt ="questions: '"+ str(questions) + "', answers: "+ str(answers)
    response = model8.generate_content(prompt)
    correct_count = str(response.candidates[0].content.parts[0].text).strip()

    return jsonify({"correctCount": correct_count})
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
    app.run(debug=True)