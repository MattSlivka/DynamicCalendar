import os
import requests
import psycopg2
from datetime import datetime, timedelta
import time
from apscheduler.schedulers.background import BackgroundScheduler


# Environment Variables
DATABASE_URL = os.getenv("DATABASE_URL")
NOTIFIER_URL = os.getenv("NOTIFIER_URL")
db_conn = None

scheduler = BackgroundScheduler()

def db_connection(max_retries=30, retry_delay=5):
    retries = 0
    while retries < max_retries:
        try:
            # Attempt connection
            conn = psycopg2.connect(DATABASE_URL)
            # Test the connection
            cur = conn.cursor()
            cur.execute("""SELECT 1""")
            print("Connected to database successfully.")
            return conn
        except psycopg2.OperationalError as err:
            retries += 1
            print(f"Connection failed: {err}. Retrying in {retry_delay} seconds... ({retries}/{max_retries})")
            time.sleep(retry_delay)


# Querying the Database
def check_appointments(conn):
    now = datetime.now()
    time_1 = now + timedelta(hours = 24) #24 Hour Reminder
    time_2 = now + timedelta(hours = 2) #2 Hour Threshold
    cur = conn.cursor()
    cur.execute("""
        SELECT a.appointment_id, c.email, a.start_time
        FROM Appointments a
        LEFT JOIN Contacts c ON a.contact_id = c.contact_id
        LEFT JOIN Notifications n ON a.appointment_id = n.appointment_id AND n.type = 'reminder_24h'
        WHERE start_time >= %(time_2)s AND start_time <= %(time_1)s AND notification_id IS NULL
    """, {"time_1": time_1, "time_2": time_2})

    rows = cur.fetchall()
    upcoming_appointments = []
    for row in rows:
        upcoming_appointments.append({
            "appointment_id": row[0],
            "type": "reminder_24h",
            "sent_to": row[1],
            "appt_time": row[2]
        })
    cur.close()
    return upcoming_appointments

def send_reminder(appointment, conn): 
     # Attempt to send the notification
    status = "failed"
    try:
        response = requests.post(
            f"{NOTIFIER_URL}/send", 
            json={
                "to": appointment["sent_to"],
                "subject": "Upcoming Appointment",
                "body": f"Your appointment at {appointment['appt_time'].isoformat()} is happening in 24 hours!"
            }, 
            timeout=5
        )
        status = "sent"
        response.raise_for_status()
        print(f"Successfully notified {appointment['sent_to']}")
        
    except requests.exceptions.RequestException as e:
        status = "failed"
        print(f"Failed to notify client {appointment['sent_to']}: {e}")
    
    # Write to Notifications table regardless of success/failure
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO Notifications (appointment_id, type, sent_to, sent_at, status)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            appointment["appointment_id"], 
            appointment["type"], 
            appointment["sent_to"],
            datetime.now(),
            status
        ))
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"Database error while logging notification: {e}")

def run_reminders(conn): 
    new_appointments = check_appointments(conn)
    for appointment in new_appointments: 
        send_reminder(appointment, conn)
    return

if __name__ == '__main__':
    db_conn = db_connection()
    if db_conn is None:
        exit(1)
    scheduler.add_job(run_reminders, 'interval', seconds=900, args = [db_conn])
    scheduler.start()
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
