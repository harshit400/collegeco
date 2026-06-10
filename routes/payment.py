from flask import render_template, request, redirect, session, flash
import razorpay
from app import csrf
from app import app, mysql


# =========================
# RAZORPAY CONFIG
# =========================

RAZORPAY_KEY_ID="rzp_test_Su4my3C0v8FN4R"
RAZORPAY_KEY_SECRET="Q3222JzwWFVV0s8Ay1J0M7Lf"

client = razorpay.Client(
    auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
)


# =========================
# PAY REQUEST FEE
# =========================

@app.route('/pay_request')
def pay_request():

    if 'user_id' not in session:
        return redirect('/login')

    cur = mysql.connection.cursor()

    # already paid
    cur.execute("""
        SELECT id
        FROM payments
        WHERE
            student_id=%s
            AND payment_type='request'
            AND payment_status='Verified'
        LIMIT 1
    """, (session['user_id'],))

    if cur.fetchone():

        flash("Payment already completed")
        return redirect('/profile')

    order = client.order.create({
        "amount": 5000,
        "currency": "INR",
        "payment_capture": 1
    })

    session['payment_type'] = 'request'

    return render_template(
        'payment.html',
        order=order,
        razorpay_key=RAZORPAY_KEY_ID
    )


# =========================
# PAYMENT SUCCESS
# =========================
@csrf.exempt
@app.route('/payment_success', methods=['POST'])
def payment_success():

    if 'user_id' not in session:
        return redirect('/login')

    payment_id = request.form.get('razorpay_payment_id')
    order_id = request.form.get('razorpay_order_id')
    signature = request.form.get('razorpay_signature')

    if not payment_id:
        flash("Payment failed")
        return redirect('/profile')

    # Verify Razorpay signature
    try:

        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }

        client.utility.verify_payment_signature(
            params_dict
        )

    except Exception:

        flash("Payment verification failed")
        return redirect('/profile')

    payment_type = session.get('payment_type')

    cur = mysql.connection.cursor()

    # Prevent duplicate payment entries
    cur.execute("""
        SELECT id
        FROM payments
        WHERE transaction_id=%s
    """, (payment_id,))

    if cur.fetchone():

        flash("Payment already processed")
        return redirect('/profile')

    # Save payment
    cur.execute("""
        INSERT INTO payments
        (
            student_id,
            amount,
            payment_type,
            transaction_id,
            payment_status
        )
        VALUES (%s,%s,%s,%s,%s)
    """, (
        session['user_id'],
        50,
        payment_type,
        payment_id,
        'Verified'
    ))

    mysql.connection.commit()

    # Student paying to send requests
    if payment_type == "request":

        flash("Payment successful. You can now send requests.")

        return redirect('/send_request')

    # Senior paying to accept request
    if payment_type == "accept":

        request_id = session.get('request_id')

        if request_id:
            return redirect(f'/final_accept/{request_id}')

    flash("Payment successful")

    return redirect('/profile')