from flask import Flask

app = Flask(__name__)

@app.route('/teacher/dashboard')
def dashboard():
    return "Teacher Dashboard"

if __name__ == '__main__':
    app.run(debug=True)