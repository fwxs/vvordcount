from flask import Flask


app = Flask(__name__)


@app.route('/')
def hello():
    return "Hello, World!"


@app.route('/<name>')
def hello_username(name):
    return f"Hello {name}!"


if __name__ == '__main__':
    app.run()

