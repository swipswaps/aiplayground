# -*- coding: utf-8 -*-
from flask import Flask, jsonify, render_template, request
from wtforms import Form, TextAreaField, validators
import logging
import pickle
import sqlite3
import os
import numpy as np
import psutil
import sys
from aiplayground import app

domain = 'aiplayground'
cdir = sys.path[0]
log = os.path.join(cdir, 'aiplayground.log')
db = os.path.join(cdir, 'moods.sqlite')
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
                    filename=log,
                    level=logging.INFO,
                    datefmt='%Y-%m-%d %H:%M:%S')


class ReviewForm(Form):
    mood = TextAreaField('', [validators.DataRequired(), validators.length(min=15, max=500)])


@app.route('/')
def index():
    app.logger.info(sys._getframe().f_code.co_name)
    form = ReviewForm(request.form)
    return render_template('index.html', domain=domain, form=form, system_info_text=get_system_info())


@app.route('/results', methods=['POST'])
def results():
    app.logger.info(sys._getframe().f_code.co_name)
    form = ReviewForm(request.form)
    if request.method == 'POST' and form.validate():
        review = request.form['mood']
        y, proba = classify(review)
        return render_template('results.html', domain=domain, content=review, prediction=y,
                               probability=round(proba * 100, 4), system_info_text=get_system_info())
    return render_template('index.html', domain=domain, form=form, system_info_text=get_system_info())


@app.route('/thanks', methods=['POST'])
def feedback():
    app.logger.info(sys._getframe().f_code.co_name)
    feedback = request.form['feedback_button']
    mood = request.form['mood']
    prediction = request.form['prediction']
    inv_label = {'negative': 0, 'positive': 1}
    y = inv_label[prediction]
    if feedback == 'Incorrect':
        y = int(not (y))
    train(mood, y)
    sqlite_entry(db, mood, y)
    return render_template('thanks.html', domain=domain, system_info_text=get_system_info())


@app.route('/sys_info.json')
def system_info():
    app.logger.info(sys._getframe().f_code.co_name)
    return get_system_info()


def classify(document):
    app.logger.info(sys._getframe().f_code.co_name)
    clf, vect = getPickles()
    label = {0: 'negative', 1: 'positive'}
    X = vect.transform([document])
    y = clf.predict(X)[0]
    proba = np.max(clf.predict_proba(X))
    return label[y], proba


def train(document, y):
    app.logger.info(sys._getframe().f_code.co_name)
    clf, vect = getPickles()
    X = vect.transform([document])
    clf.partial_fit(X, [y])


def sqlite_entry(path, document, y):
    app.logger.info(sys._getframe().f_code.co_name)
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.execute("INSERT INTO moods_db (mood, sentiment, date) VALUES (?, ?, DATETIME('now'))", (document, y))
    conn.commit()
    conn.close()


def getPickles():
    app.logger.info(sys._getframe().f_code.co_name)
    import vectorizer
    clf = pickle.load(open(os.path.join(cdir, 'pkl_objects', 'classifier.pkl'), 'rb'))
    vect = vectorizer.getStopwords(pickle.load(open(os.path.join(cdir, 'pkl_objects', 'stopwords.pkl'), 'rb')))
    return clf, vect


def get_system_info():
    app.logger.info(sys._getframe().f_code.co_name)
    info = 'System Information: [CPU: {0}%] [Memory: {1}%]'.format(str(psutil.cpu_percent()),
                                                                   str(psutil.virtual_memory()[2]))
    app.logger.info(info)
    return info