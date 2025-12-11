from flask import Flask, render_template, request, redirect, session
from db import get_connection
import re

app = Flask(__name__)
app.secret_key = "mysupersecretkey123"

# =====================================================
#           GLOBAL VALIDATION FUNCTIONS
# =====================================================

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email)

def is_valid_phone(phone):
    pattern = r'^\+\d{1,3}\s\d{10}$'      # +91 9876543210 format
    return re.match(pattern, phone)

# =====================================================
#                    LOGIN PAGE
# =====================================================
@app.route("/", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        role = request.form.get("role", "")
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not is_valid_email(email):
            return render_template("login.html", error="Please enter a valid email!")

        con = get_connection()
        cur = con.cursor()

        # -------- ADMIN LOGIN --------
        if role == "admin":
            cur.execute("SELECT * FROM admin WHERE A_Email=%s AND A_Password=%s",
                        (email, password))
            user = cur.fetchone()
            if user:
                session["name"] = user[1]  # A_Name
                session["role"] = "admin"
                return redirect("/admin/dashboard")

        # -------- STUDENT LOGIN --------
        elif role == "student":
            cur.execute("SELECT * FROM student WHERE S_Email=%s AND S_Password=%s",
                        (email, password))
            user = cur.fetchone()
            if user:
                session["name"] = user[2]  # S_Name
                session["role"] = "student"
                return redirect("/student/dashboard")

        # -------- TEACHER LOGIN --------
        elif role == "teacher":
            cur.execute("SELECT * FROM teacher WHERE F_Email=%s AND F_Password=%s",
                        (email, password))
            user = cur.fetchone()
            if user:
                session["name"] = user[1]  # F_Name
                session["role"] = "teacher"
                return redirect("/teacher/dashboard")

        error = "Invalid Email or Password!"

    return render_template("login.html", error=error)

# =====================================================
#                 ADMIN DASHBOARD
# =====================================================
@app.route("/admin/dashboard")
def admin_dashboard():

    admin_name = session.get("name", "Admin")

    con = get_connection()
    cur = con.cursor()

    cur.execute("SELECT COUNT(*) FROM student")
    total_students = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM teacher")
    total_faculty = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM marks")
    exams_processed = cur.fetchone()[0]

    con.close()

    # dummy fallback when DB empty
    if total_students == 0: total_students = 1254
    if total_faculty == 0: total_faculty = 63
    if exams_processed == 0: exams_processed = 18

    return render_template("admin_dashboard.html",
                           admin_name=admin_name,
                           total_students=total_students,
                           total_faculty=total_faculty,
                           exams_processed=exams_processed,
                           prediction_accuracy=78)

# STUDENT MENU
@app.route("/admin/student-menu")
def student_menu():
    return render_template("student_menu.html")

# =====================================================
#                 STUDENT DASHBOARD
# =====================================================
@app.route("/student/dashboard")
def student_dashboard():
    name = session.get("name", "Student")
    return f"<h1>Welcome {name}! (Student Dashboard Coming Soon)</h1>"


'''@app.route("/teacher/dashboard")
=======
# =====================================================
#                 TEACHER DASHBOARD
# =====================================================
@app.route("/teacher/dashboard")
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

# =====================================================
#                   ADD STUDENT
# =====================================================
@app.route("/admin/add-student", methods=["GET", "POST"])
def add_student():
    if request.method == "POST":

        roll = request.form["roll"]
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        phone = request.form["phone"]
        dept = request.form["department"]
        sem = request.form["semester"]

        if not is_valid_email(email):
            return render_template("add_student.html", error="Invalid Email Format!")

        if not is_valid_phone(phone):
            return render_template("add_student.html",
                                   error="Phone must be like +91 9876543210")

        con = get_connection()
        cur = con.cursor()

        sql = """INSERT INTO student 
                 (Roll_No, S_Name, S_Email, S_Password, S_Phone, S_Department, S_Semester)
                 VALUES (%s,%s,%s,%s,%s,%s,%s)"""

        cur.execute(sql, (roll, name, email, password, phone, dept, sem))
        con.commit()
        con.close()

        return redirect("/admin/students")

    return render_template("add_student.html")

# =====================================================
#                   VIEW STUDENTS
# =====================================================
@app.route("/admin/students")
def view_students():
    con = get_connection()
    cur = con.cursor(dictionary=True)
    cur.execute("SELECT * FROM student")
    students = cur.fetchall()
    con.close()
    return render_template("view_students.html", students=students)

# =====================================================
#            EDIT STUDENTS LIST PAGE
# =====================================================
@app.route("/admin/edit-students")
def edit_students_list():
    con = get_connection()
    cur = con.cursor(dictionary=True)
    cur.execute("SELECT * FROM student")
    students = cur.fetchall()
    con.close()
    return render_template("edit_students.html", students=students)

# =====================================================
#                   UPDATE STUDENT
# =====================================================
@app.route("/admin/update-student/<int:id>", methods=["GET", "POST"])
def update_student(id):

    con = get_connection()
    cur = con.cursor(dictionary=True)

    cur.execute("SELECT * FROM student WHERE S_ID=%s", (id,))
    student = cur.fetchone()

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        dept = request.form["department"]
        sem = request.form["semester"]

        if not is_valid_email(email):
            return render_template("update_student.html", student=student,
                                   error="Invalid Email Format!")

        if not is_valid_phone(phone):
            return render_template("update_student.html", student=student,
                                   error="Phone must be like +91 9876543210")

        sql = """UPDATE student SET 
                 S_Name=%s, S_Email=%s, S_Phone=%s,
                 S_Department=%s, S_Semester=%s
                 WHERE S_ID=%s"""

        cur.execute(sql, (name, email, phone, dept, sem, id))
        con.commit()
        con.close()

        return redirect("/admin/edit-students")

    return render_template("update_student.html", student=student)

# =====================================================
#            DELETE STUDENTS LIST PAGE
# =====================================================
@app.route("/admin/delete-students")
def delete_students_list():
    con = get_connection()
    cur = con.cursor(dictionary=True)
    cur.execute("SELECT * FROM student")
    students = cur.fetchall()
    con.close()
    return render_template("delete_students.html", students=students)

# =====================================================
#                   DELETE STUDENT
# =====================================================
@app.route("/admin/delete-student/<int:id>")
def delete_student(id):
    con = get_connection()
    cur = con.cursor()
    cur.execute("DELETE FROM student WHERE S_ID=%s", (id,))
    con.commit()
    con.close()
    return redirect("/admin/delete-students")

# =====================================================
#                      MAIN
# =====================================================
if __name__ == "__main__":
    app.run(debug=True)
