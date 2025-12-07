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
    pattern = r'^\+\d{1,3}\s\d{10}$'
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
            error = "Please enter a valid email!"
            return render_template("login.html", error=error)

        con = get_connection()
        cur = con.cursor()

        # -------- ADMIN LOGIN --------
        if role == "admin":
            cur.execute("SELECT * FROM admin WHERE A_Email=%s AND A_Password=%s", 
                        (email, password))
            user = cur.fetchone()
            if user:
                session["name"] = user[1]
                session["role"] = "admin"
                return redirect("/admin/dashboard")

        # -------- STUDENT LOGIN --------
        elif role == "student":
            cur.execute("SELECT * FROM student WHERE S_Email=%s AND S_Password=%s", 
                        (email, password))
            user = cur.fetchone()
            if user:
                session["name"] = user[2]
                session["role"] = "student"
                return redirect("/student/dashboard")

        # -------- TEACHER LOGIN --------
        elif role == "teacher":
            cur.execute("SELECT * FROM teacher WHERE F_Email=%s AND F_Password=%s", 
                        (email, password))
            user = cur.fetchone()
            if user:
                session["name"] = user[1]
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

    if total_students == 0: total_students = 1254
    if total_faculty == 0: total_faculty = 63
    if exams_processed == 0: exams_processed = 18

    return render_template("admin_dashboard.html",
                           admin_name=admin_name,
                           total_students=total_students,
                           total_faculty=total_faculty,
                           exams_processed=exams_processed,
                           prediction_accuracy=78)


# STUDENT MENU PAGE
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


# =====================================================
#                 TEACHER DASHBOARD
# =====================================================
@app.route("/teacher/dashboard")
def teacher_dashboard():
    teacher_name = session.get("name", "Teacher")
    return render_template("faculty_dashboard.html", teacher_name=teacher_name)


# =====================================================
#                   ADD STUDENT
# =====================================================
@app.route("/admin/add-student", methods=["GET", "POST"])
def add_student():
    error = None

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
            return render_template("add_student.html", error="Phone must be like +91 9876543210")

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


# EDIT STUDENT LIST PAGE
@app.route("/admin/edit-students")
def edit_students_list():
    con = get_connection()
    cur = con.cursor(dictionary=True)
    cur.execute("SELECT * FROM student")
    students = cur.fetchall()
    con.close()
    return render_template("edit_students.html", students=students)


# =====================================================
#                   EDIT STUDENT
# =====================================================
@app.route("/admin/edit-student/<int:id>", methods=["GET", "POST"])
def edit_student(id):

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
            return render_template("edit_student.html", student=student,
                                   error="Invalid Email Format!")

        if not is_valid_phone(phone):
            return render_template("edit_student.html", student=student,
                                   error="Phone must be like +91 9876543210")

        sql = """UPDATE student SET 
                 S_Name=%s, S_Email=%s, S_Phone=%s,
                 S_Department=%s, S_Semester=%s
                 WHERE S_ID=%s"""

        cur.execute(sql, (name, email, phone, dept, sem, id))
        con.commit()
        con.close()

        return redirect("/admin/students")

    return render_template("edit_student.html", student=student)


# =====================================================
#                   DELETE STUDENT LIST PAGE
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
