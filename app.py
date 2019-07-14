from bs4 import BeautifulSoup
from collections import Counter
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request
from nltk.corpus import stopwords
from stop_words import stops

import nltk
import operator
import os
import re
import requests


app = Flask(__name__)
app.config.from_object(os.environ["APP_SETTINGS"])
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


from models import Result


@app.route('/', methods=["GET", "POST"])
def index():
    errors = []
    results = {}

    if request.method == "POST":
        # Get URL that the user has entered.
        try:
            url = request.form["url"]
            req = requests.get(url)

        except:
            errors.append("Unable to get URL: Please make sure it's valid and try again")
            return render_template("index.html", errors=errors)

        if req:
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

            print(f"Stop words: {no_stop_words_count}")

            # Save the results
            results = sorted(
                    no_stop_words_count.items(),
                    key=operator.itemgetter(1),
                    reverse=True
                    )[:10]

            print(f"results")

            try:
                result = Result(
                        url=url,
                        result_all=raw_word_count,
                        result_no_stop_words=no_stop_words_count
                        )
                db.session.add(result)
                db.session.commit()
            except Exception as dbError:
                print(f"Error: {dbError}")
                errors.append("Unable to add item to database.")

    return render_template("index.html", errors=errors, results=results)


if __name__ == "__main__":
    app.run()

