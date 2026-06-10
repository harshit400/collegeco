from flask import render_template, request, redirect, session, flash

from app import app, mysql

@app.route('/profile', methods=['GET', 'POST'])
def profile():

    if 'user_id' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    # Get current user
    cur.execute("""
        SELECT *
        FROM students
        WHERE id=%s
    """, (session['user_id'],))

    user = cur.fetchone()

    if not user:
        session.clear()
        return redirect('/login')

    # Update profile
    if request.method == 'POST':

        full_name = request.form['full_name']
        phone = request.form['phone']
        course = request.form['course']

        cur.execute("""
            UPDATE students
            SET
                full_name=%s,
                phone=%s,
                course=%s
            WHERE id=%s
        """, (
            full_name,
            phone,
            course,
            session['user_id']
        ))

        mysql.connection.commit()

        flash("Profile updated successfully")

        return redirect('/profile')

    # Check payment status
    cur.execute("""
        SELECT id
        FROM payments
        WHERE
            student_id=%s
            AND payment_type='request'
            AND payment_status='Verified'
        LIMIT 1
    """, (session['user_id'],))

    has_paid = cur.fetchone() is not None

    # Check if already connected
    cur.execute("""
        SELECT id
        FROM student_requests
        WHERE
            new_student_id=%s
            AND connected=1
        LIMIT 1
    """, (session['user_id'],))

    connected = cur.fetchone() is not None

    # Check if senior available
    senior_available = False

    try:

        college_name = user[4]

        cur.execute("""
            SELECT id
            FROM students
            WHERE
                college_name=%s
                AND admission_type='Old Student'
            LIMIT 1
        """, (college_name,))

        senior_available = cur.fetchone() is not None

    except:
        senior_available = False

    return render_template(
        'profile.html',
        user=user,
        has_paid=has_paid,
        connected=connected,
        senior_available=senior_available
)