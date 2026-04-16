from flask import Flask, request, g, render_template, redirect, url_for
import sqlite3, os
DB = os.path.join(os.path.dirname(__file__), 'forum.db')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB)
        db.row_factory = sqlite3.Row
    return db

app = Flask(__name__)

@app.teardown_appcontext
def close_db(exception=None):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/', methods=['GET'])
def index():
    db = get_db()
    cur = db.execute('SELECT id,author,content,created FROM posts ORDER BY created DESC')
    posts = cur.fetchall()
    return render_template('index.html', posts=posts)

@app.route('/post', methods=['POST'])
def post():
    author = request.form.get('author','anon')[:50]
    content = request.form.get('content','')[:2000]
    db = get_db()
    db.execute('INSERT INTO posts (author,content) VALUES (?,?)',(author,content))
    db.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
