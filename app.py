#!/opt/imh-python/bin/python2.7
# __author__ = 'chases'
# import the Flask class from the flask module
from __future__ import print_function
from flask import Flask, render_template, redirect, \
    url_for, request, session, flash
from functools import wraps
from flask.ext.sqlalchemy import SQLAlchemy
import sqlite3
from sqlalchemy import *
import random
from MySQLdb import IntegrityError
import hashlib
import json

# create the application object
app = Flask(__name__)
app.secret_key = '<m`+HMUuLnMQ'

# config
db = create_engine('mysql://$mysqluser:$mysqlpassword@localhost/$database')
metadata = MetaData(db)
total_questions = dict(db.execute("SELECT COUNT(*) FROM Questions;").first())[u'COUNT(*)']


# import db schema
# from models import *


# login required decorator
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('You need to login first.')
            return redirect(url_for('login'))

    return wrap


@app.route('/confirm', methods=['GET', 'POST'])
@login_required
def confirm():
    try:
        prev_choice = int(request.form['choice'])
    except Exception as exc:
        prev_choice = 1
    prev_results = db.execute(
        "select CorrectAnswer from Questions WHERE QuestionNumber='{}'".format(session['lastquestion']))
    CorrectAnswer = dict(prev_results.first())['CorrectAnswer']
    more_info = db.execute("select AddInfo from Questions WHERE QuestionNumber='{}'".format(session['lastquestion']))
    more_info = dict(more_info.first())['AddInfo']
    if CorrectAnswer == chr(int(request.form['choice']) + 64):
        db.execute("UPDATE Users SET points = points + 100 WHERE email = '{}'".format(session['user']))
        flash('Correct! 100 Points Awarded')
        prev_question = 'Correct'
    else:
        flash('Incorrect. No Points Awarded')
        prev_question = 'Incorrect'
    total_score = db.execute("select Points from Users WHERE email='{}'".format(session['user']))
    Score = dict(total_score.first())['Points']
    db.execute(
        "UPDATE Users SET Status = {} WHERE email = '{}'".format(session['lastquestion'] + 1, session['user']))
    session['lastquestion'] += 1
    prev_results = db.execute("select ResultJSON from Users WHERE email='{}'".format(session['user']))
    try:
        prev_result_first = prev_results.first()
        with open('/tmp/readfile.tmp', 'w') as tmpdump:
            print(prev_result_first, file=tmpdump)
            print(dict(prev_result_first), file=tmpdump)
        if dict(prev_result_first)['ResultJSON'] != None:
            prev_results_json = json.loads(dict(prev_result_first)['ResultJSON'])
        else:
            prev_results_json = {}
            prev_results_json['Quiz1'] = {}
    except ValueError, TypeError:
        prev_results_json = {}
        prev_results_json['Quiz1'] = {}
    if 'Quiz1' in prev_results_json.keys():
        prev_results_json['Quiz1']['Q{}'.format(session['lastquestion'])] = [chr(prev_choice + 64),
                                                                             prev_question]
    else:
        with open('/tmp/readfile.tmp', 'w') as tmpdump:
            print('What do you mean doesnt has attr', file=tmpdump)
            print(prev_results_json, file=tmpdump)
            print(prev_results_json.keys(), file=tmpdump)
        prev_results_json = {}
        prev_results_json['Quiz1'] = {}
        prev_results_json['Quiz1']['Q{}'.format(session['lastquestion'])] = [chr(prev_choice + 64),
                                                                             prev_question]
    db.execute("UPDATE Users SET ResultJSON = '{}' WHERE email = '{}'".format(json.dumps(prev_results_json),
                                                                              session['user']))
    return render_template('confirmation.html', QuestionNo=(session['lastquestion'] - 1), question=session['question'],
                           choices=session['choices'], userchoice=request.form['choice'],
                           goodchoice=(ord(CorrectAnswer) - 64), score=Score, more_info=more_info,
                           TotalQuestions=total_questions)


# use decorators to link the function to a url
@app.route('/', methods=['GET', 'POST'])
@login_required
def home():
    prev_choice = False
    question = 'Why isnt this working'
    choices = ['Who', 'fucking', 'knows']
    with open('/tmp/readfile.tmp', 'w') as tmpdump:
        print(request.form, file=tmpdump)
        print(total_questions, file=tmpdump)
    prev_question = 'Incorrect'
    questions = Table('Questions', metadata, autoload=True)
    s = questions.select()
    rs = s.execute()
    if request.method == 'POST':
        return redirect(url_for('confirm'))
        db.execute(
            "UPDATE Users SET Status = {} WHERE email = '{}'".format(session['lastquestion'] + 1, session['user']))
        while True:
            row = rs.fetchone()
            if row == None:
                break
            if row['QuestionNumber'] == session['lastquestion']:
                if prev_choice == None:
                    flash('Make your choice')
                elif (int(prev_choice) + 64) == ord(row['CorrectAnswer']):
                    db.execute("UPDATE Users SET points = points + 100 WHERE email = '{}'".format(session['user']))
                    prev_question = "Correct"
                flash('Previous Question: {}'.format(prev_question))
                flash('Chosen Answer: {}'.format(chr(prev_choice + 64)))
                flash('Correct Answer: {}'.format(row['CorrectAnswer']))
                session['lastquestion'] += 1
                break
    total_score = db.execute("select Points from Users WHERE email='{}'".format(session['user']))
    flash('Total Score: {}'.format(dict(total_score.first())['Points']))
    questions = Table('Questions', metadata, autoload=True)
    s = questions.select()
    rs = s.execute()
    for question in range(60):
        row = rs.fetchone()
        if row == None:
            break
        if int(row['QuestionNumber']) == (int(session['lastquestion'])) and row != None:
            session['question'] = row['Question'].encode("utf8", 'ignore')
            session['choices'] = [row['OptionA'], row['OptionB'], row['OptionC'],
                                  row['OptionD']]
            for choice in range(len(session['choices'])):
                if session['choices'][choice] != None:
                    session['choices'][choice] = session['choices'][choice].strip()
            return render_template('index.html', prev_question=prev_question, question=session['question'],
                                   choices=session['choices'],
                                   QuestionNo=session['lastquestion'], user=session['user'], prev_choice=prev_choice,
                                   session=session['lastquestion'], last_question_checked=row['QuestionNumber'],
                                   TotalQuestions=total_questions)
    if row == None:
        total_score = db.execute("select Points from Users WHERE email='{}'".format(session['user']))
        return render_template('finished.html')
    return render_template('index.html', prev_question=prev_question, question=question, choices=choices,
                           QuestionNo=session['lastquestion'], user=session['user'], prev_choice=prev_choice,
                           session=session['lastquestion'], last_question_checked=row['QuestionNumber'],
                           TotalQuestions=total_questions)


@app.route('/welcome')
def welcome():
    return render_template('welcome.html')  # render a template


# route for handling the login page logic
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        error = 'Invalid Credentials. Please try again.'
        users = Table('Users', metadata, autoload=True)
        s = users.select()
        rs = s.execute()
        while True:
            row = rs.fetchone()
            if row == None:
                break
            admincheck = row['email']
            passcheck = (row['UserPass'])
            if (request.form['username'] != admincheck) \
                    or hashlib.sha256(request.form['password']).hexdigest() != passcheck:
                pass
            else:
                error = None
                session['logged_in'] = True
                session['user'] = request.form['username']
                session['lastquestion'] = row['Status']
                flash('You were logged in.')
                return redirect(url_for('home'))
                break
    return render_template('login.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        if request.form['username']:
            users = Table('Users', metadata, autoload=True)
            i = users.insert()
            try:
                i.execute(firstname=request.form['firstname'], lastname=request.form['lastname'],
                          UserPass=hashlib.sha256(request.form['password']).hexdigest(), points=0,
                          email=request.form['username'])
                return redirect(url_for('login'))
            except Exception as exc:
                return render_template('register.html', error='Unable to create user')
    return render_template('register.html', error=error)


@app.route('/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    flash('You were logged out.')
    return redirect(url_for('login'))


# connect to database
def connect_db():
    return sqlite3.connect('posts.db')


# start the server with the 'run()' method
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

