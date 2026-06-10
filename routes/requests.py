from flask import render_template, redirect, session, flash
from app import app, mysql
from app import client, RAZORPAY_KEY_ID

# =========================
# SEND REQUEST
# =========================

@app.route('/send_request')
def send_request():

    if 'user_id' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    # Check payment completed
    cur.execute("""
        SELECT id
        FROM payments
        WHERE
            student_id=%s
            AND payment_type='request'
            AND payment_status='Verified'
        LIMIT 1
    """, (session['user_id'],))

    payment = cur.fetchone()

    if not payment:

        flash("Please pay ₹50 first.")

        return redirect('/profile')

    # Already connected?
    cur.execute("""
        SELECT id
        FROM student_requests
        WHERE
            new_student_id=%s
            AND connected=1
        LIMIT 1
    """, (session['user_id'],))

    if cur.fetchone():

        flash("You are already connected with a senior student.")

        return redirect('/profile')

    # Student college
    cur.execute("""
        SELECT college_name
        FROM students
        WHERE id=%s
    """, (session['user_id'],))

    college = cur.fetchone()

    if not college:

        flash("Student not found")

        return redirect('/profile')

    college_name = college[0]

    # Find available seniors
    cur.execute("""
        SELECT id
        FROM students
        WHERE
            college_name=%s
            AND admission_type='Old Student'
            AND id NOT IN (
                SELECT old_student_id
                FROM student_requests
                WHERE connected=1
            )
    """, (college_name,))

    seniors = cur.fetchall()

    if not seniors:

        flash("No senior students available.")

        return redirect('/profile')

    count = 0

    for senior in seniors:

        senior_id = senior[0]

        # Avoid duplicate requests
        cur.execute("""
            SELECT id
            FROM student_requests
            WHERE
                new_student_id=%s
                AND old_student_id=%s
        """, (
            session['user_id'],
            senior_id
        ))

        if cur.fetchone():
            continue

        cur.execute("""
            INSERT INTO student_requests
            (
                new_student_id,
                old_student_id,
                status,
                connected
            )

            VALUES (%s,%s,%s,%s)
        """, (
            session['user_id'],
            senior_id,
            'Pending',
            0
        ))

        count += 1

    mysql.connection.commit()

    flash(f"{count} request(s) sent successfully.")

    return redirect('/status')


# =========================
# STATUS PAGE
# =========================

@app.route('/status')
def status():

    if 'user_id' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
            sr.id,
            sr.status,
            sr.connected,
            sr.created_at,
            s.full_name

        FROM student_requests sr

        JOIN students s
        ON s.id = sr.old_student_id

        WHERE sr.new_student_id=%s

        ORDER BY sr.id DESC
    """, (session['user_id'],))

    requests = cur.fetchall()

    return render_template(
        'status.html',
        requests=requests
    )


# =========================
# REQUESTS PAGE
# =========================

@app.route('/requests')
def requests_page():

    if 'user_id' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT
            sr.id,
            s.full_name,
            s.course,
            s.college_name,
            sr.created_at

        FROM student_requests sr

        JOIN students s
            ON s.id = sr.new_student_id

        WHERE
            sr.old_student_id=%s
            AND sr.status='Pending'

        ORDER BY sr.id DESC
    """, (session['user_id'],))

    requests = cur.fetchall()

    return render_template(
        'requests.html',
        requests=requests
    )


# =========================
# ACCEPT REQUEST
# =========================

@app.route('/accept_request/<int:request_id>', methods=['POST'])
def accept_request(request_id):
    if 'user_id' not in session:
        return redirect('/login')

    session['request_id'] = request_id
    session['payment_type'] = 'accept'

    order = client.order.create({
        "amount": 5000,
        "currency": "INR"
    })

    return render_template(
        'payment.html',
        order=order,
        razorpay_key=RAZORPAY_KEY_ID
    )


@app.route('/final_accept/<int:request_id>', methods=['POST','GET'])
def final_accept(request_id):

    if 'user_id' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    # Get the student who sent the request
    cur.execute("""
        SELECT new_student_id
        FROM student_requests
        WHERE id=%s
    """, (request_id,))

    row = cur.fetchone()

    if not row:
        flash("Request not found")
        return redirect('/requests')

    new_student_id = row[0]

    # Accept selected request
    cur.execute("""
        UPDATE student_requests
        SET
            status='Accepted',
            connected=1
        WHERE id=%s
    """, (request_id,))

    # Delete ALL OTHER pending requests
    # sent by the same student
    cur.execute("""
        DELETE FROM student_requests
        WHERE
            new_student_id=%s
            AND id != %s
            AND status='Pending'
    """, (
        new_student_id,
        request_id
    ))

    mysql.connection.commit()

    flash("Request accepted successfully")

    return redirect('/chat_list')

