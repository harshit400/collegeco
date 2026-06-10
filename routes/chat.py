from flask import render_template, request, redirect, session, jsonify
from app import app, mysql


# =========================
# CHAT LIST
# =========================

@app.route('/chat_list')
def chat_list():

    if 'user_id' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    if session['admission_type'] == "New Admission":

        cur.execute("""
            SELECT
                s.id,
                s.full_name

            FROM student_requests sr

            JOIN students s
            ON s.id = sr.old_student_id

            WHERE
                sr.new_student_id=%s
                AND sr.connected=1
        """, (session['user_id'],))

    else:

        cur.execute("""
            SELECT
                s.id,
                s.full_name

            FROM student_requests sr

            JOIN students s
            ON s.id = sr.new_student_id

            WHERE
                sr.old_student_id=%s
                AND sr.connected=1
        """, (session['user_id'],))

    chats = cur.fetchall()

    return render_template(
        'chat_list.html',
        chats=chats
    )


# =========================
# CHAT PAGE
# =========================

@app.route('/chat/<int:user2_id>', methods=['GET', 'POST'])
def chat(user2_id):

    if 'user_id' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    # SECURITY CHECK
    cur.execute("""

        SELECT *

        FROM student_requests

        WHERE

        (
            new_student_id=%s
            AND old_student_id=%s
        )

        OR

        (
            new_student_id=%s
            AND old_student_id=%s
        )

        AND connected=1

    """, (
        session['user_id'],
        user2_id,
        user2_id,
        session['user_id']
    ))

    allowed = cur.fetchone()

    if not allowed:
        return "Unauthorized Access"

    if request.method == 'POST':

        message = request.form['message']

        cur.execute("""

            INSERT INTO chats
            (
                sender_id,
                receiver_id,
                message
            )

            VALUES (%s,%s,%s)

        """, (
            session['user_id'],
            user2_id,
            message
        ))

        mysql.connection.commit()

    return render_template(
        'chat.html',
        user1_id=session['user_id'],
        user2_id=user2_id
    )

# =========================
# GET MESSAGES API
# =========================

@app.route('/get_messages/<int:user2_id>')
def get_messages(user2_id):

    if 'user_id' not in session:
        return jsonify([])

    cur = mysql.connection.cursor()

    cur.execute("""

        SELECT
        sender_id,
        message,
        created_at

        FROM chats

        WHERE

        (sender_id=%s AND receiver_id=%s)

        OR

        (sender_id=%s AND receiver_id=%s)

        ORDER BY id ASC

    """, (
        session['user_id'],
        user2_id,
        user2_id,
        session['user_id']
    ))

    messages = cur.fetchall()

    data = []

    for m in messages:

        data.append({
            "sender_id": m[0],
            "message": m[1],
            "time": str(m[2])
        })

    return jsonify(data)
