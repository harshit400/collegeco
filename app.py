from flask import Flask
from flask_mysqldb import MySQL
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from datetime import timedelta
import os

app = Flask(__name__)

# =========================
# SECURITY
# =========================

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "college-connect-secret-key"
)

app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # True in production HTTPS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

app.permanent_session_lifetime = timedelta(minutes=30)

# =========================
# MYSQL
# =========================

app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', '')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB', 'college_db')

mysql = MySQL(app)

# =========================
# MAIL
# =========================

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

mail = Mail(app)

# =========================
# SECURITY TOOLS
# =========================

csrf = CSRFProtect(app)

limiter = Limiter(
    key_func=get_remote_address,
    app=app
)

# =========================
# IMPORT ROUTES
# =========================

from routes.auth import *
from routes.profile import *
from routes.payment import *
from routes.requests import *
from routes.chat import *
from routes.pages import *

# =========================
# RUN
# =========================

if __name__ == "__main__":
    app.run(debug=True)