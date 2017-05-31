import flask
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
from flask_session import Session
import pygal
from pygal.style import DarkSolarizedStyle
import time
import random
import gnupg
import os
import sys

login_manager = LoginManager()
session_manager = Session()
app = flask.Flask(__name__, template_folder='templates')
####################################################
# Add information of server PGP key in config file #
####################################################
KEYID='' # first line of config file
PASSPHRASE='' # second line of config file
IP = '' # third line of config file 
PORT = '' # fourth line of config file 
# index page
# login O - redirect to log upload page
# login X - redirect to login page
@app.route('/')
def index():
    login = flask.session.get('login', False)
    if login:
        return flask.redirect('/upload')
    else:
        return flask.redirect('/login')

# login page
# GET  - display login page(input ID box)
# POST - user submitted github ID
@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'POST':
        global FINGERPRINT
        global PASSPHRASE
        githubID = flask.request.form['id']
        keypath = './pub/' + githubID

        # check github ID by finding public key
        if not os.path.exists(keypath) or os.path.isdir(keypath):
            return flask.Response('No public key')
        data = file_read(keypath)
        pubkey = gpg.import_keys(data)
        if len(pubkey.fingerprints) == 0:
            return flask.Response('%s is not public key\n%s'%(keypath,data))
        challenge = str(random.getrandbits(256))
        flask.session['id'] = githubID
        flask.session['challenge'] = challenge
        challenge = gpg.encrypt(challenge, pubkey.fingerprints[0], always_trust=True, default_key=KEYID, passphrase=PASSPHRASE)
        flask.session['encChallenge'] = str(challenge)
        return flask.redirect('/auth')

    return flask.render_template('login.html')

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    githubID = flask.session.get('id', False)
    challenge = flask.session.get('challenge', False)
    encChallenge = flask.session.get('encChallenge', False)

    if githubID == False or challenge == False or encChallenge == False:
        return flask.redirect('/login')

    # verify challenge
    if flask.request.method == 'POST':
        global PASSPHRASE
        userChallenge = flask.request.form['challenge']
        decrypt_data = gpg.decrypt(userChallenge, passphrase=PASSPHRASE)
        if str(decrypt_data).strip() == challenge:
            user = User(githubID, challenge)
            login_user(user)
            flask.session['login'] = True
            return flask.redirect('/upload')
        else:
            return 'auth fail'

    return flask.render_template('auth.html', challenge=encChallenge)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if flask.request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in flask.request.files:
            flash('No file part')
            return flask.redirect(request.url)

        labels = []
        values = []
        service = None
        file = flask.request.files['file']
        for data in file.read().split('\n'):
            if data == '': continue
            items = data.split(',')
            if not service : service = items[1] + ":" + items[2]
            labels.append(time.strftime("%H:%M:%S", time.localtime(int(items[0]))))
            values.append(1 if items[3].find('up') != -1 else 0)
        status_chart = pygal.Line(width=1200, height=675, explicit_size=True, title='Service Status', style=DarkSolarizedStyle, x_label_rotation=20)
        status_chart.x_labels = labels
        status_chart.add(service, values)
        return flask.render_template('chart.html', body=status_chart.render())

    return flask.render_template('upload.html')

@app.route("/logout")
@login_required
def logout():
    # logout and delete session informations
    logout_user()
    del flask.session['id']
    del flask.session['challenge']
    del flask.session['login']
    return flask.redirect('/login')

@login_manager.user_loader
def load_user(userid):
    login = flask.session.get('login', False)
    if login:
        return User(userid, flask.session.get('challenge', False))
    else:
        return None

@app.route("/get",methods=['GET'])
def static_page():
    if 'page' in flask.request.args:
	    page = flask.request.args.get('page')
	    path = 'static/' + page
	    if os.path.exists(path) and not os.path.isdir(path):
		return file_read(path)
    else:
        return flask.render_template('404.html'), 404

class User(UserMixin):
    def __init__(self, githubID, challenge):
        self.name = githubID
        self.password = challenge

    def get_id(self):
        return self.name

    def __repr__(self):
        return "%s/%s" % (self.name, self.password)

def file_read(name):
    with open(name, "rb") as f:
        return f.read()

def init():
    global KEYID, PASSPHRASE, IP, PORT
    lines=file_read("config").split('\n')
    KEYID = lines[0].strip()
    PASSPHRASE = lines[1].strip()
    IP = lines[2].strip()
    PORT = int(lines[3].strip())
    ID = int(lines[4].strip())
    os.setgid(ID)
    os.setuid(ID)

if __name__ == '__main__':
    init()
    homegpgdir = '/home/visualizer/.gnupg'
    try:
            gpg = gnupg.GPG(gnupghome=homegpgdir)
    except TypeError:
            gpg = gnupg.GPG(homedir=homegpgdir)
    app.secret_key = ''.join(chr(random.randrange(0, 256)) for i in range(32))
    app.config['SESSION_TYPE'] = 'filesystem'
    login_manager.init_app(app)
    session_manager.init_app(app)
    app.run(host=IP, port=PORT)
