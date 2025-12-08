from flask import Flask, render_template, request, redirect, session
from db import get_connection
import re

app = Flask(__name__)
app.secret_key = "mysupersecretkey123"   # for storing login session


# ==============================
#         LOGIN PAGE
# ==============================
@app.route("/", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        role = request.form.get("role", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        # -----------------------
        # Email validation
        # -----------------------
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_pattern, email):
            error = "Please enter a valid email address!"
            return render_template("login.html", error=error)

        con = get_connection()
        cur = con.cursor()

        # ----- ADMIN LOGIN -----
        if role == "admin":
            cur.execute("SELECT * FROM admin WHERE A_Email=%s AND A_Password=%s",
                        (email, password))
            user = cur.fetchone()

            if user:
                session["name"] = user[1]        # A_Name
                session["role"] = "admin"
                return redirect("/admin/dashboard")

        # ----- STUDENT LOGIN -----
        elif role == "student":
            cur.execute("SELECT * FROM Student WHERE S_Email=%s AND S_Password=%s",
                        (email, password))
            user = cur.fetchone()

            if user:
                session["name"] = user[2]        # S_Name
                session["role"] = "student"
                return redirect("/student/dashboard")

        # ----- TEACHER LOGIN -----
        elif role == "teacher":
            cur.execute("SELECT * FROM teacher WHERE F_Email=%s AND F_Password=%s",
                        (email, password))
            user = cur.fetchone()

            if user:
                session["name"] = user[1]        # F_Name
                session["role"] = "teacher"
                return redirect("/teacher/dashboard")

        # Wrong login
        error = "Invalid Email or Password!"

    return render_template("login.html", error=error)



# ==============================
#     ADMIN DASHBOARD
# ==============================
@app.route("/admin/dashboard")
def admin_dashboard():

    admin_name = session.get("name", "Admin")   # Get logged-in admin name

    con = get_connection()
    cur = con.cursor()

    cur.execute("SELECT COUNT(*) FROM Student")
    total_students = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM Teacher")
    total_faculty = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM Marks")
    exams_processed = cur.fetchone()[0]

    con.close()

    # fallback values
    if total_students == 0: total_students = 1254
    if total_faculty == 0: total_faculty = 63
    if exams_processed == 0: exams_processed = 18

    prediction_accuracy = 78

    return render_template("admin_dashboard.html",
                           admin_name=admin_name,
                           total_students=total_students,
                           total_faculty=total_faculty,
                           exams_processed=exams_processed,
                           prediction_accuracy=prediction_accuracy)



# ==============================
#   STUDENT DASHBOARD
# ==============================
@app.route("/student/dashboard")
def student_dashboard():
    student_name = session.get("name", "Student")
    return f"<h1>Welcome {student_name}! (Student Dashboard Coming Soon)</h1>"


# ==============================
#   TEACHER DASHBOARD
# ==============================
'''@app.route("/teacher/dashboard")
def teacher_dashboard():
    teacher_name = session.get("name", "Teacher")
    return f"<h1>Welcome {teacher_name}! (Teacher Dashboard Coming Soon)</h1>"'''

'''@app.route("/teacher/dashboard")
def teacher_dashboard():
    teacher_name = session.get("name", "Teacher")
    return render_template("faculty_dashboard.html", teacher_name=teacher_name)'''
@app.route("/teacher/dashboard")
def teacher_dashboard():
    if "role" not in session or session["role"] != "teacher":
        return redirect("/")

    teacher_name = session.get("name", "Teacher")

    con = get_connection()
    cur = con.cursor(dictionary=True)

    # ---------- 1. TOTAL STUDENTS ----------
    cur.execute("SELECT COUNT(*) AS total FROM student")
    total_students = cur.fetchone()["total"]

    # ---------- 2. SUBJECTS ASSIGNED ----------
    cur.execute("SELECT COUNT(*) AS total FROM subject")
    subjects_assigned = cur.fetchone()["total"]

    # ---------- 3. PENDING MARKS ----------
    cur.execute("SELECT COUNT(*) AS pending FROM marks WHERE status='pending'")
    pending_marks = cur.fetchone()["pending"]

    # ---------- 4. TODAY'S ATTENDANCE ----------
    cur.execute("SELECT AVG(attendance_percentage) AS avg_att FROM attendance")
    attendance_today = cur.fetchone()["avg_att"] or 0

    # ---------- 5. SUBJECT-WISE AVERAGE MARKS ----------
    cur.execute("""
        SELECT s.Sub_Name, AVG(m.Total_Marks) AS avg_marks 
        FROM marks m
        JOIN subject s ON m.Sub_ID = s.Sub_ID
        GROUP BY m.Sub_ID
    """)
    subject_avg = cur.fetchall()

    # ---------- 6. PERFORMANCE TREND ----------
    cur.execute("""
        SELECT exam_type, AVG(Total_Marks) AS avg_marks
        FROM marks
        GROUP BY exam_type
        ORDER BY exam_type
    """)
    performance_trend = cur.fetchall()

    # ---------- 7. PASS / FAIL COUNT ----------
    cur.execute("SELECT COUNT(*) FROM marks WHERE Total_Marks >= 40")
    passed = cur.fetchone()["COUNT(*)"]

    cur.execute("SELECT COUNT(*) FROM marks WHERE Total_Marks < 40")
    failed = cur.fetchone()["COUNT(*)"]

    # ---------- 8. TOPPERS ----------
    cur.execute("""
        SELECT S_ID, Student_Name, Percentage
        FROM marks
        ORDER BY Percentage DESC LIMIT 5
    """)
    toppers = cur.fetchall()

    # ---------- 9. WEAK STUDENTS ----------
    cur.execute("""
        SELECT S_ID, Student_Name, Percentage
        FROM marks
        WHERE Percentage < 40
        ORDER BY Percentage ASC
        LIMIT 5
    """)
    weak_students = cur.fetchall()

    con.close()

    return render_template("faculty_dashboard.html",
                           teacher_name=teacher_name,
                           total_students=total_students,
                           subjects_assigned=subjects_assigned,
                           pending_marks=pending_marks,
                           attendance_today=round(attendance_today, 2),
                           subject_avg=subject_avg,
                           performance_trend=performance_trend,
                           passed=passed,
                           failed=failed,
                           toppers=toppers,
                           weak_students=weak_students)

# ==============================
#          MAIN
# ==============================
if __name__ == "__main__":
    app.run(debug=True)
