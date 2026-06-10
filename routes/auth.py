from flask import render_template, request, redirect, session, flash
from email_validator import validate_email, EmailNotValidError
from flask_mail import Message
import bcrypt
import random
import re

from app import app, mysql, mail, limiter,csrf


# =========================
# REGISTER
# =========================

@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def register():

    if request.method == 'POST':

        full_name = request.form['full_name']
        email = request.form['email']
        phone = request.form['phone']
        college_name = request.form['college_name']
        course = request.form['course']
        admission_type = request.form['admission_type']
        password = request.form['password']

        try:
            validate_email(email)

        except EmailNotValidError:

            flash("Invalid Email")
            return redirect('/register')

        if not phone.isdigit() or len(phone) != 10:

            flash("Invalid Phone Number")
            return redirect('/register')

        if len(password) < 8:

            flash("Password must be at least 8 characters")
            return redirect('/register')

        if not re.search(r"[A-Z]", password):

            flash("Password must contain a capital letter")
            return redirect('/register')

        if not re.search(r"[0-9]", password):

            flash("Password must contain a number")
            return redirect('/register')

        if admission_type == "New Admission":

            year = "1st Year"

        else:

            year = request.form['year']

        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        cur = mysql.connection.cursor()

        cur.execute(
            "SELECT id FROM students WHERE email=%s",
            (email,)
        )

        existing = cur.fetchone()

        if existing:

            flash("Email already exists")
            cur.close()

            return redirect('/register')

        cur.execute("""

            INSERT INTO students
            (
                full_name,
                email,
                phone,
                college_name,
                course,
                year,
                admission_type,
                password
            )

            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)

        """, (
            full_name,
            email,
            phone,
            college_name,
            course,
            year,
            admission_type,
            hashed_password
        ))

        mysql.connection.commit()
        cur.close()

        flash("Registration Successful")

        return redirect('/login')

    return render_template('register.html')


# =========================
# LOGIN
# =========================

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()

        cur.execute(
            "SELECT * FROM students WHERE email=%s",
            (email,)
        )

        user = cur.fetchone()

        cur.close()

        if not user:

            flash("Invalid Email or Password")

            return redirect('/login')

        try:

            stored_password = user[8]

            if bcrypt.checkpw(
                password.encode('utf-8'),
                stored_password.encode('utf-8')
            ):

                session.permanent = True

                session['user_id'] = user[0]
                session['user_name'] = user[1]
                session['college_name'] = user[4]
                session['admission_type'] = user[7]

                if user[7] == "Old Student":
                    return redirect('/requests')

                return redirect('/profile')

        except Exception as e:

            print("LOGIN ERROR:", e)

        flash("Invalid Email or Password")

        return redirect('/login')

    return render_template('login.html')


# =========================
# LOGOUT
# =========================

@app.route('/logout')
def logout():

    session.clear()

    flash("Logged Out Successfully")

    return redirect('/login')


# =========================
# FORGOT PASSWORD
# =========================
@csrf.exempt
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():

    if request.method == 'POST':

        email = request.form['email']

        cur = mysql.connection.cursor()

        cur.execute(
            "SELECT id FROM students WHERE email=%s",
            (email,)
        )

        user = cur.fetchone()

        cur.close()

        if not user:

            flash("Email Not Found")

            return redirect('/forgot_password')

        otp = random.randint(100000, 999999)

        session['reset_otp'] = str(otp)
        session['reset_email'] = email

        try:

            msg = Message(

                'College Connect Password Reset',

                sender=app.config['MAIL_USERNAME'],

                recipients=[email]

            )

            msg.body = f"""

            Your OTP for password reset is:

            {otp}

            """

            mail.send(msg)

        except Exception as e:

            print("MAIL ERROR:", e)

            flash("Unable to send email")

            return redirect('/forgot_password')

        flash("OTP Sent Successfully")

        return redirect('/verify_otp')

    return render_template('forgot_password.html')


# =========================
# VERIFY OTP
# =========================

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():

    if 'reset_otp' not in session:

        return redirect('/forgot_password')

    if request.method == 'POST':

        otp = request.form['otp']

        if otp == session.get('reset_otp'):

            return redirect('/reset_password')

        flash("Invalid OTP")

    return render_template('verify_otp.html')


# =========================
# RESET PASSWORD
# =========================

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():

    if 'reset_email' not in session:

        return redirect('/forgot_password')

    if request.method == 'POST':

        password = request.form['password']

        if len(password) < 8:

            flash("Password must be at least 8 characters")

            return redirect('/reset_password')

        if not re.search(r"[A-Z]", password):

            flash("Password must contain a capital letter")

            return redirect('/reset_password')

        if not re.search(r"[0-9]", password):

            flash("Password must contain a number")

            return redirect('/reset_password')

        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        cur = mysql.connection.cursor()

        cur.execute("""

            UPDATE students

            SET password=%s

            WHERE email=%s

        """, (
            hashed_password,
            session['reset_email']
        ))

        mysql.connection.commit()
        cur.close()

        session.pop('reset_otp', None)
        session.pop('reset_email', None)

        flash("Password Changed Successfully")

        return redirect('/login')

    return render_template('reset_password.html')