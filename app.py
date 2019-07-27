from bs4 import BeautifulSoup
from collections import Counter
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, jsonify
from nltk.corpus import stopwords
from rq import Queue
from rq.job import Job
from worker import conn

import json
import nltk
import operator
import os
import re
import requests


app = Flask(__name__)
app.config.from_object(os.environ["APP_SETTINGS"])
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
db = SQLAlchemy(app)

queue = Queue(connection=conn)


class InvalidURL(Exception):
    status_code = 400

    def __init__(self, messages, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = "\n".join(messages)

        if status_code is not None:
            self.status_code = status_code

        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        return rv


from models import Result


def count_and_save_words(url):
    errors = []

    try:
        req = requests.get(url)

    except:
        errors.append("Unable to get URL: Please make sure it's valid and try again")
        return {"error": errors }

    # Text processing
    raw = BeautifulSoup(req.text, "html.parser").get_text()
    nltk.data.path.append("./nltk_data/")

    tokens = nltk.word_tokenize(raw)
    text = nltk.Text(tokens)

    english_stopwords = set(stopwords.words('english'))

    # Remove punctuation, count raw words.
    nonPunct = re.compile(".*[A-Za-z].*")
    raw_words = [word for word in text if nonPunct.match(word)]
    raw_word_count = Counter(raw_words)

    # Stop words
    no_stop_words = [word for word in raw_words
                          if word.lower() not in english_stopwords
                    ]
    no_stop_words_count = Counter(no_stop_words)

    # Save the results
    results = sorted(
                    no_stop_words_count.items(),
                    key=operator.itemgetter(1),
                    reverse=True
                    )

    try:
        result = Result(
                    url=url,
                    result_all=raw_word_count,
                    result_no_stop_words=no_stop_words_count
                )
        db.session.add(result)
        db.session.commit()

        return result.id
    except Exception as dbError:
        print(f"Error: {dbError}")
        errors.append("Unable to add item to database.")
        return {"error": errors}


@app.errorhandler(InvalidURL)
def handler_invalid_url(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@app.route('/', methods=["GET", "POST"])
def index():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def get_counts():
    errors = []
    results = {}

    data = json.loads(request.data.decode())
    url = data["url"]

    if "http" not in url[:4]:
        url = "http://" + url
    elif "https" not in url[:5]:
        url = "https://" + url

    job = queue.enqueue_call(
            func=count_and_save_words, args=(url,), result_ttl=500
            )

    return job.get_id()


@app.route("/results/<job_key>", methods=["GET"])
def get_result(job_key):
    job = Job.fetch(job_key, connection=conn)

    if job.is_finished:
        if not isinstance(job.result, int):
            raise InvalidURL(job.result["error"], status_code=404)

        result = Result.query.filter_by(id=job.result).first()
        results = sorted(
                        result.result_no_stop_words.items(),
                        key=operator.itemgetter(1),
                        reverse=True
                    )[:10]

        return jsonify(results)
    else:
        return "Nay!", 202

if __name__ == "__main__":
    app.run()

