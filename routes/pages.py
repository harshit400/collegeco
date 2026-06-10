from flask import render_template, redirect
from app import app


# =========================
# HOME
# =========================

@app.route('/')
def home():
    return redirect('/login')


# =========================
# ABOUT
# =========================

@app.route('/about')
def about():
    return render_template('about.html')


# =========================
# CONTACT
# =========================

@app.route('/contact')
def contact():
    return render_template('contact.html')


# =========================
# PRIVACY POLICY
# =========================

@app.route('/privacy_policy')
def privacy_policy():
    return render_template('privacy_policy.html')


# =========================
# TERMS & CONDITIONS
# =========================

@app.route('/terms')
def terms():
    return render_template('terms.html')