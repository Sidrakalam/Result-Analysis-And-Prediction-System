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

# FACULTY MENU
@app.route("/admin/faculty-menu")
def faculty_menu():
    return render_template("faculty_menu.html")


# =====================================================
#                   ADD FACULTY
# =====================================================

@app.route("/admin/add-faculty", methods=["GET", "POST"])
def add_faculty():
    error = None

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        country = request.form["country_code"]
        phone = request.form["phone"]
        department = request.form["department"]

        full_phone = country + " " + phone

        # Email Validation
        if not is_valid_email(email):
            return render_template("add_faculty.html", error="Invalid Email Format!")

        # Phone Validation (country code + number)
        if not re.match(r'^\+\d{1,3}\s\d{7,12}$', full_phone):
            return render_template("add_faculty.html", error="Invalid Phone Number!")

        con = get_connection()
        cur = con.cursor()

        sql = """INSERT INTO teacher 
                 (T_Name, T_Email, T_Password, T_Phone, T_Department)
                 VALUES (%s, %s, %s, %s, %s)"""

        cur.execute(sql, (name, email, password, full_phone, department))
        con.commit()
        con.close()

        return redirect("/admin/view-faculty")

    return render_template("add_faculty.html")

# =====================================================
#                      VIEW FACULTY
# =====================================================

@app.route("/admin/view-faculty")
def view_faculty():
    con = get_connection()
    cur = con.cursor(dictionary=True)
    cur.execute("SELECT * FROM teacher")
    faculty = cur.fetchall()
    con.close()
    return render_template("view_faculty.html", faculty=faculty)


@app.route("/admin/edit-faculty")
def edit_faculty_list():
    con = get_connection()
    cur = con.cursor(dictionary=True)
    cur.execute("SELECT * FROM teacher")
    faculty = cur.fetchall()
    con.close()
    return render_template("edit_faculty.html", faculty=faculty)


    # =====================================================
    #                      UPDATE FACULTY
    # =====================================================

@app.route("/admin/update-faculty/<int:id>", methods=["GET", "POST"])
def update_faculty(id):

    con = get_connection()
    cur = con.cursor(dictionary=True)

    cur.execute("SELECT * FROM teacher WHERE T_ID=%s", (id,))
    faculty = cur.fetchone()

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        dept = request.form["department"]

        if not is_valid_email(email):
            return render_template("update_faculty.html", faculty=faculty,
                                error="Invalid Email!")

        if not is_valid_phone(phone):
            return render_template("update_faculty.html", faculty=faculty,
                                    error="Phone must be like +91 9876543210")

        sql = """UPDATE teacher SET 
                    T_Name=%s, T_Email=%s, T_Phone=%s, T_Department=%s
                    WHERE T_ID=%s"""

        cur.execute(sql, (name, email, phone, dept, id))
        con.commit()
        con.close()

        return redirect("/admin/edit-faculty")

    return render_template("update_faculty.html", faculty=faculty)

# =====================================================
#                      DELETE FACULTY
# =====================================================

@app.route("/admin/delete-faculty")
def delete_faculty_list():
    con = get_connection()
    cur = con.cursor(dictionary=True)
    cur.execute("SELECT * FROM teacher")
    faculty = cur.fetchall()
    con.close()
    return render_template("delete_faculty.html", faculty=faculty)

@app.route("/admin/delete-faculty/<int:id>")
def delete_faculty(id):
    con = get_connection()
    cur = con.cursor()
    cur.execute("DELETE FROM teacher WHERE T_ID=%s", (id,))
    con.commit()
    con.close()
    return redirect("/admin/delete-faculty")

# ---------------------- LIST FACULTY ----------------------
@app.route("/admin/assign-subject")
def assign_subject():
    con = get_connection()
    cur = con.cursor(dictionary=True)
    cur.execute("SELECT * FROM teacher")
    faculty = cur.fetchall()
    con.close()
    return render_template("assign_subject.html", faculty=faculty)



# ------------------ ASSIGN SUBJECT TO FACULTY ------------------
@app.route("/admin/assign-subject/<int:t_id>", methods=["GET", "POST"])
def assign_subject_to_faculty(t_id):

    con = get_connection()
    cur = con.cursor(dictionary=True)

    # Get selected teacher
    cur.execute("SELECT * FROM teacher WHERE T_ID=%s", (t_id,))
    faculty = cur.fetchone()

    # Get subjects ONLY from faculty’s department
    cur.execute("SELECT * FROM subject WHERE Sub_Department=%s", (faculty["T_Department"],))
    subject = cur.fetchall()

    if request.method == "POST":
        subject_id = request.form["subject_id"]

        # Insert into teacher_subject table
        cur.execute("""
            INSERT INTO teacher_subject (T_ID, Sub_ID)
            VALUES (%s, %s)
        """, (t_id, subject_id))

        con.commit()
        con.close()
        return redirect("/admin/view-assigned")

    return render_template("assign_subject_to_faculty.html",
                           faculty=faculty, subject=subject)


# -------------------- VIEW ALL ASSIGNED SUBJECTS --------------------
@app.route("/admin/view-assigned")
def view_assigned():

    con = get_connection()
    cur = con.cursor(dictionary=True)

    cur.execute("""
        SELECT ts.TS_ID, t.T_Name, s.Sub_Name, s.Sub_Code
        FROM teacher_subject ts
        JOIN teacher t ON ts.T_ID = t.T_ID
        JOIN subject s ON ts.Sub_ID = s.Sub_ID
    """)

    assigned = cur.fetchall()
    con.close()

    return render_template("view_assigned_subjects.html", assigned=assigned)

# ---------------------- REMOVE ASSIGNMENT ----------------------
@app.route("/admin/remove-assigned/<int:ts_id>")
def remove_assigned(ts_id):
    con = get_connection()
    cur = con.cursor()
    cur.execute("DELETE FROM teacher_subject WHERE TS_ID=%s", (ts_id,))
    con.commit()
    con.close()
    return redirect("/admin/view-assigned")

# ---------------------- SUBJECT MENU ----------------------
@app.route("/admin/subject-menu")
def subject_menu():
    return render_template("subject_menu.html")

# ---------------------- ADD SUBJECT ----------------------
@app.route("/admin/add-subject", methods=["GET", "POST"])
def add_subject():
    error = None

    if request.method == "POST":
        code = request.form["code"]
        name = request.form["name"]
        semester = request.form["semester"]
        dept = request.form["department"]

        con = get_connection()
        cur = con.cursor()

        # Check duplicate code
        cur.execute("SELECT * FROM subject WHERE Sub_Code=%s", (code,))
        if cur.fetchone():
            con.close()
            return render_template("add_subject.html", error="Subject Code already exists!")

        cur.execute("""
            INSERT INTO subject (Sub_Code, Sub_Name, Sub_Semester, Sub_Department)
            VALUES (%s, %s, %s, %s)
        """, (code, name, semester, dept))

        con.commit()
        con.close()
        return redirect("/admin/view-subject")

    return render_template("add_subject.html")


# ---------------------- VIEW SUBJECTS ----------------------
@app.route("/admin/view-subject")
def view_subjects():
    con = get_connection()
    cur = con.cursor(dictionary=True)
    cur.execute("SELECT * FROM subject")
    subject = cur.fetchall()
    con.close()
    return render_template("view_subject.html", subject=subject)


# ---------------------- EDIT SUBJECT LIST ----------------------
@app.route("/admin/edit-subject")
def edit_subjects_list():
    con = get_connection()
    cur = con.cursor(dictionary=True)
    cur.execute("SELECT * FROM subject")
    subject = cur.fetchall()
    con.close()
    return render_template("edit_subject.html", subject=subject)


# ---------------------- UPDATE SUBJECT ----------------------
@app.route("/admin/update-subject/<int:id>", methods=["GET", "POST"])
def update_subject(id):

    con = get_connection()
    cur = con.cursor(dictionary=True)

    cur.execute("SELECT * FROM subject WHERE Sub_ID=%s", (id,))
    subject = cur.fetchone()

    if request.method == "POST":
        code = request.form["code"]
        name = request.form["name"]
        semester = request.form["semester"]
        dept = request.form["department"]

        cur.execute("""
            UPDATE subject SET 
                Sub_Code=%s, 
                Sub_Name=%s, 
                Sub_Semester=%s, 
                Sub_Department=%s
            WHERE Sub_ID=%s
        """, (code, name, semester, dept, id))

        con.commit()
        con.close()

        return redirect("/admin/edit-subject")

    con.close()
    return render_template("update_subject.html", subject=subject)


# ---------------------- DELETE SUBJECT ----------------------
@app.route("/admin/delete-subject/<int:id>")
def delete_subject(id):
    con = get_connection()
    cur = con.cursor()
    cur.execute("DELETE FROM subject WHERE Sub_ID=%s", (id,))
    con.commit()
    con.close()
    return redirect("/admin/delete-subject")


# ---------------------- DELETE SUBJECT LIST ----------------------
@app.route("/admin/delete-subject")
def delete_subjects_list():
    con = get_connection()
    cur = con.cursor(dictionary=True)
    cur.execute("SELECT * FROM subject")
    subject = cur.fetchall()
    con.close()
    return render_template("delete_subject.html", subject=subject)

#STUDENT DASHBOARD

@app.route("/student/dashboard")
def student_dashboard():

    if "role" not in session or session["role"] != "student":
        return redirect("/")

    student_name = session.get("name", "Student")

    return render_template("student_dashboard.html", student_name=student_name)


#STUDENT PROFILE
@app.route("/student/profile")
def student_profile():

    if "role" not in session or session["role"] != "student":
        return redirect("/")

    student_name = session["name"]

    con = get_connection()
    cur = con.cursor(dictionary=True)

    # Fetch Student Details
    cur.execute("SELECT * FROM student WHERE S_Name=%s", (student_name,))
    student = cur.fetchone()

    con.close()

    return render_template("student_profile.html", student=student)
#STUDENT RESULT

@app.route("/student/results")
def student_results():

    if "role" not in session or session["role"] != "student":
        return redirect("/")

    student_name = session["name"]

    con = get_connection()
    cur = con.cursor(dictionary=True)

    # Get student ID
    cur.execute("SELECT S_ID, S_Semester FROM student WHERE S_Name=%s", 
                (student_name,))
    stu = cur.fetchone()

    sid = stu["S_ID"]
    student_sem = stu["S_Semester"]

    # Fetch subject-wise marks JOIN subject name
    cur.execute("""
        SELECT subject.Sub_Code, subject.Sub_Name,
               marks.Internal, marks.External, marks.Total
        FROM marks
        JOIN subject ON marks.Sub_ID = subject.Sub_ID
        WHERE marks.S_ID=%s
        ORDER BY subject.Sub_Name ASC
    """, (sid,))

    results = cur.fetchall()
    con.close()

    return render_template("student_results.html",
                           results=results,
                           student_sem=student_sem,
                           student_name=student_name)

#TOTAL CLASS AND SEMESTER WISE RESULT 


@app.route("/student/class-results")
def student_class_results():

    if "role" not in session or session["role"] != "student":
        return redirect("/")

    student_name = session["name"]

    con = get_connection()
    cur = con.cursor(dictionary=True)

    # Fetch student data (to match department + semester)
    cur.execute("SELECT S_ID, S_Department, S_Semester FROM student WHERE S_Name=%s",
                (student_name,))
    stu = cur.fetchone()

    dept = stu["S_Department"]
    sem = stu["S_Semester"]

    # FETCH STUDENTS OF SAME CLASS (department + semester)
    cur.execute("""
        SELECT S_ID, S_Name, Roll_No
        FROM student
        WHERE S_Department=%s AND S_Semester=%s
    """, (dept, sem))
    classmates = cur.fetchall()

    # CALCULATE TOTAL MARKS OF EACH STUDENT
    class_results = []

    for s in classmates:
        cur.execute("""
            SELECT SUM(Total) AS total_marks
            FROM marks
            WHERE S_ID=%s
        """, (s["S_ID"],))
        result = cur.fetchone()

        total = result["total_marks"] if result["total_marks"] else 0

        class_results.append({
            "S_ID": s["S_ID"],
            "S_Name": s["S_Name"],
            "Roll_No": s["Roll_No"],
            "Total": total
        })

    # SORT STUDENTS BY TOTAL MARKS DESCENDING
    class_results = sorted(class_results, key=lambda x: x["Total"], reverse=True)

    # ASSIGN RANKS
    rank = 1
    for student in class_results:
        student["Rank"] = rank
        rank += 1

    con.close()

    return render_template("class_results.html",
                           class_results=class_results,
                           dept=dept,
                           sem=sem)

#RESULT ANALYSIS 


import json
from flask import Flask, render_template, session, redirect
# ... your other imports and get_connection function ...

@app.route("/student/analysis")
def student_analysis():

    # auth
    if "role" not in session or session["role"] != "student":
        return redirect("/")

    student_name = session.get("name")

    con = get_connection()
    cur = con.cursor(dictionary=True)

    # get student id + semester for display
    cur.execute("SELECT S_ID, S_Semester FROM student WHERE S_Name=%s", (student_name,))
    stu = cur.fetchone()
    if not stu:
        con.close()
        return render_template("student_analysis.html",
                               error="Student record not found.",
                               student_name=student_name)

    sid = stu["S_ID"]
    student_sem = stu.get("S_Semester", "")

    # fetch subject-wise marks for this student
    cur.execute("""
        SELECT sub.Sub_Name, sub.Sub_Code, sub.Sub_Semester,
               m.Internal, m.External, m.Total
        FROM marks m
        JOIN subject sub ON m.Sub_ID = sub.Sub_ID
        WHERE m.S_ID = %s
        ORDER BY sub.Sub_Name
    """, (sid,))

    rows = cur.fetchall()
    con.close()

    # if no marks found, pass empty
    if not rows:
        return render_template("student_analysis.html",
                               student_name=student_name,
                               student_sem=student_sem,
                               subjects_json=json.dumps([]),
                               totals_json=json.dumps([]),
                               internals_json=json.dumps([]),
                               externals_json=json.dumps([]),
                               summary={},
                               insights=[]
                               )

    # prepare chart arrays and compute summary
    subjects = []
    sub_codes = []
    totals = []
    internals = []
    externals = []

    for r in rows:
        subjects.append(r["Sub_Name"])
        sub_codes.append(r["Sub_Code"])
        internals.append(r["Internal"] if r["Internal"] is not None else 0)
        externals.append(r["External"] if r["External"] is not None else 0)
        totals.append(r["Total"] if r["Total"] is not None else ( (r["Internal"] or 0) + (r["External"] or 0) ))

    # summary metrics
    highest = max(totals)
    lowest = min(totals)
    avg = round(sum(totals)/len(totals), 2)
    total_subjects = len(totals)
    highest_idx = totals.index(highest)
    lowest_idx = totals.index(lowest)
    strong_subject = subjects[highest_idx]
    weak_subject = subjects[lowest_idx]

    summary = {
        "total_subjects": total_subjects,
        "highest": highest,
        "highest_sub": strong_subject,
        "lowest": lowest,
        "lowest_sub": weak_subject,
        "average": avg
    }

    # simple insights (extendable)
    insights = []
    if avg >= 75:
        insights.append("Excellent overall performance — keep up the good work.")
    elif avg >= 60:
        insights.append("Good performance. Aim to improve low scoring subjects for higher scores.")
    elif avg >= 40:
        insights.append("Average performance. Focus on weak subjects and practice more.")
    else:
        insights.append("Your performance is below average. Consider counseling and extra practice.")

    insights.append(f"Strongest Subject: {strong_subject} ({highest})")
    insights.append(f"Weakest Subject: {weak_subject} ({lowest})")

    # internal vs external suggestions
    # if average internal is low vs external, suggest improving internals
    avg_internal = round(sum(internals)/len(internals), 2)
    avg_external = round(sum(externals)/len(externals), 2)
    if avg_internal < (0.6 * avg_external):  # heuristic
        insights.append("Your internal marks are relatively low compared to external marks. Improve class participation and internal assessments.")

    return render_template("student_analysis.html",
                           student_name=student_name,
                           student_sem=student_sem,
                           subjects_json=json.dumps(subjects),
                           subcodes_json=json.dumps(sub_codes),
                           totals_json=json.dumps(totals),
                           internals_json=json.dumps(internals),
                           externals_json=json.dumps(externals),
                           summary=summary,
                           insights=insights)


#                      MAIN
# =====================================================
if __name__ == "__main__":
    app.run(debug=True)
