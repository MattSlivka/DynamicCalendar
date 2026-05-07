import os
from flask import Flask, request, jsonify, session, redirect, render_template
import requests
import psycopg2
from werkzeug.security import check_password_hash
from datetime import datetime
import re

app = Flask(__name__)

# Environment Variables
DATABASE_URL = os.getenv("DATABASE_URL")
NOTIFIER_URL = os.getenv("NOTIFIER_URL")
app.secret_key = os.getenv("SECRET_KEY")
STAFF_EMAIL = os.getenv("STAFF, and STAFF_EMAIL")


conn = psycopg2.connect(DATABASE_URL)

def is_logged_in():
    return 'user_id' in session

# Verify Login
@app.route('/auth/login', methods=['POST'])
def check_login():
    # Check if staff, then get password hash. Store hash.
    # If generated hash = db hash, then is_valid set to true, return 200.
    # If anything else is not true, return 400; Invalid input.
    username = request.form.get('username')
    password = request.form.get('password')
    cur = conn.cursor()
    cur.execute("SELECT password_hash, contact_id FROM Contacts WHERE username = %s AND role = 'staff'", (username,))
    row = cur.fetchone()

    if row and check_password_hash(row[0], password):
        session['user_id'] = row[1]
        cur.close()
        return redirect('/staff')
    # return jsonify({"status": "Succesful Login!"}), 200
    else:
        cur.close()
		# return jsonify({"status": "failed"}), 401
        return redirect('/login')

@app.route('/')
def index():
    return render_template('calendar.html')

@app.route('/intake')
def intake():
    return render_template('intake.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/staff')
def staff():
    if not is_logged_in():
        return redirect('/login')
    return render_template('staff.html')

@app.route('/api/intake', methods=['POST'])
def request_form():
    full_name = request.form.get('full_name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    date_time = request.form.get('date_time')
    notes = request.form.get('notes')
    # Validation for phone, email, and date_time  CLAUDE GENERATED MOST OF THIS FOR ME.

    if not full_name or not email or not phone or not date_time:
        return jsonify({"status": "error", "message": "Invalid input, try again."}), 400
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({"status": "error", "message": "Invalid input, try again."}), 400
    if not phone.isdigit():
        return jsonify({"status": "error", "message": "Invalid input, try again."}), 400
    try:
        preferred_time = datetime.strptime(date_time, "%Y-%m-%dT%H:%M")
        if preferred_time <= datetime.now():
            return jsonify({"status": "error", "message": "Invalid input, try again."}), 400
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid input, try again."}), 400

    cur = conn.cursor()
    #Inserting into Contacts / Verifying it already exists
    cur.execute("""
        INSERT INTO Contacts (full_name, email, phone, role)
        VALUES (%s, %s, %s, 'client')
        ON CONFLICT (email) DO UPDATE SET full_name = EXCLUDED.full_name
        RETURNING contact_id
    """, (full_name, email, phone))
    contact_id = cur.fetchone()[0]
    # Add command to get into Requests Container
    cur.execute("""
        INSERT INTO Requests (contact_id, preferred_time, notes)
        VALUES (%s, %s, %s)
    """, (contact_id, preferred_time, notes))
    conn.commit()
    cur.close()

    #Notify Staff  Claude also generated this for me. 
    try:
        requests.post(f"{NOTIFIER_URL}/send", json={
            "to": STAFF_EMAIL,
            "subject": "New Appointment Request",
            "body": f"New request from {full_name} for {preferred_time}"
        })
    except requests.exceptions.RequestException as e:
        print(f"Failed to notify staff: {e}")
    return jsonify({"status": "success", "message": "Appointment request submitted successfully."}), 200

@app.route('/api/appointments', methods=['GET'])
def get_appointments():
    if not is_logged_in():
        return jsonify({"status": "unauthorized"}), 401
    cur = conn.cursor()
    cur.execute(""" 
        SELECT appointment_id, start_time, end_time FROM Appointments
    """)
    rows = cur.fetchall()
    appointments = []
    for row in rows: 
        appointments.append({
            "title": f"Appointment {row[0]}",
            "start": row[1].isoformat(),
            "end": row[2].isoformat()
        })
    cur.close()
    return jsonify(appointments), 200

@app.route('/api/public/appointments', methods=['GET'])
def get_public_appointments():
    cur = conn.cursor()
    cur.execute("""
        SELECT a.appointment_id, a.start_time, a.end_time, c.full_name
        FROM Appointments a
        JOIN Contacts c ON a.contact_id = c.contact_id
        WHERE a.status = 'confirmed'
    """)
    rows = cur.fetchall()
    appointments = []
    for row in rows:
        appointments.append({
            "title": f"Appointment with {row[3]}",
            "start": row[1].isoformat(),
            "end": row[2].isoformat()
        })
    cur.close()
    return jsonify(appointments), 200
    # I had to directly copy/paste this from Claude in order to solve the issue of HTML validation. 

@app.route('/api/requests', methods=['GET'])
def get_requests():    
    if not is_logged_in():
        return jsonify({"status": "unauthorized"}), 401
    cur = conn.cursor()
    cur.execute("""
        SELECT request_id, contact_id, preferred_time, notes, status FROM Requests 
        WHERE status = 'pending'
    """)
    rows = cur.fetchall()
    requests_list = []
    for row in rows:
        requests_list.append({
            "request_id": row[0],
            "contact_id": row[1],
            "preferred_time": row[2].isoformat(),
            "notes": row[3], 
            "status": row[4]
        })
    cur.close()
    return jsonify(requests_list), 200

@app.route('/api/requests/<int:id>/approve', methods=['POST'])
def approve_request(id):
    if not is_logged_in():
        return jsonify({"status": "unauthorized"}), 401
    cur = conn.cursor()
    cur.execute("""
        UPDATE Requests SET status = 'approved'
        WHERE request_id = %s
    """, (id,))
    cur.execute("""
        SELECT r.contact_id, r.preferred_time, r.request_id, c.email
        FROM Requests r
        JOIN Contacts c ON r.contact_id = c.contact_id
        WHERE r.request_id = %s
    """, (id,))
    row = cur.fetchone()
    contact_id = row[0]
    preferred_time = row[1]
    request_id = row[2]
    client_email = row[3]
    cur.execute("""
        INSERT INTO Appointments (contact_id, start_time, end_time, request_id, status)
        VALUES (%s, %s, %s, %s, 'confirmed')
    """, (contact_id, preferred_time, preferred_time, request_id))
    try:
        requests.post(f"{NOTIFIER_URL}/send", json={
            "to": client_email,
            "subject": "Appointment Approved",
            "body": f"Your appointment for {preferred_time} is now scheduled!"
        }, timeout=5)
    except requests.exceptions.RequestException as e:
        print(f"Failed to notify client: {e}")
    conn.commit()
    cur.close()
    return jsonify({"status": "submitted"}), 200

@app.route('/api/requests/<int:id>/reject', methods=['POST'])
def reject_request(id):
    if not is_logged_in():
        return jsonify({"status": "unauthorized"}), 401
    cur = conn.cursor()
    cur.execute("""
        UPDATE Requests SET status = 'rejected'
        WHERE request_id = %s
    """, (id,))
    conn.commit()
    cur.close()
    return jsonify({"status": "complete"}), 200


@app.route('/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect('/')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
