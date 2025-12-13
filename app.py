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
                session["S_ID"] = user[0]
                session["name"] = user[2]  # S_Name
                session["role"] = "student"
                return redirect("/student/dashboard")

        # -------- TEACHER LOGIN --------
        elif role == "teacher":
            cur.execute("SELECT * FROM teacher WHERE T_Email=%s AND T_Password=%s",
                        (email, password))
            user = cur.fetchone()
            if user:
                session["name"] = user[1]  # F_Name
                session["role"] = "teacher"
                session["T_ID"]=user[0]
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

# =====================================================
#                 TEACHER DASHBOARD
# =====================================================
@app.route("/teacher/dashboard")
def teacher_dashboard():

    # ---- SECURITY CHECK ----
    if "role" not in session or session["role"] != "teacher":
        return redirect("/")

    teacher_name = session.get("name", "Teacher")
    T_ID = session.get("T_ID")   # ⭐ FETCH T_ID FROM SESSION

    con = get_connection()
    cur = con.cursor(dictionary=True)

    # ---------- 1. TOTAL STUDENTS (teacher's dept & semester) ----------
    cur.execute("""
    SELECT COUNT(DISTINCT s.S_ID) AS total
    FROM student s
    JOIN subject sub
        ON s.S_Department = sub.Sub_Department
       AND s.S_Semester   = sub.Sub_Semester
    JOIN teacher_subject ts
        ON ts.Sub_ID = sub.Sub_ID
    WHERE ts.T_ID = %s
    """, (T_ID,))

    total_students = cur.fetchone()["total"] or 0

    # ---------- 2. SUBJECTS ASSIGNED ----------
    cur.execute("""
    SELECT COUNT(DISTINCT ts.Sub_ID) AS total
    FROM teacher_subject ts
    WHERE ts.T_ID = %s
    """, (T_ID,))

    subjects_assigned = cur.fetchone()["total"] or 0


# ---------- PENDING MARKS ----------
    cur.execute("""
    SELECT COUNT(DISTINCT s.S_ID) AS pending
    FROM student s
    JOIN subject sub
        ON s.S_Department = sub.Sub_Department
       AND s.S_Semester   = sub.Sub_Semester
    JOIN teacher_subject ts
        ON ts.Sub_ID = sub.Sub_ID
    LEFT JOIN marks m
        ON m.S_ID = s.S_ID
       AND m.Sub_ID = sub.Sub_ID
    WHERE ts.T_ID = %s
      AND m.M_ID IS NULL
""", (T_ID,))
    pending_marks = cur.fetchone()["pending"] or 0

# ---------- SUBJECT-WISE AVERAGE (BAR CHART DATA) ----------
    cur.execute("""
    SELECT sub.Sub_Name,
           ROUND(AVG(m.Total), 2) AS avg_marks
    FROM marks m
    JOIN subject sub ON m.Sub_ID = sub.Sub_ID
    JOIN teacher_subject ts ON ts.Sub_ID = sub.Sub_ID
    WHERE ts.T_ID = %s
    GROUP BY sub.Sub_ID
    """, (T_ID,))

    bar_data = cur.fetchall()


    
    '''# ---------- 5. PERFORMANCE TREND ----------
    cur.execute("""
        SELECT 'Internal' AS exam_type, AVG(Internal) AS avg_marks FROM marks WHERE T_ID=%s
        UNION
        SELECT 'External', AVG(External) FROM marks WHERE T_ID=%s
        UNION
        SELECT 'Total', AVG(Total) FROM marks WHERE T_ID=%s
    """, (T_ID, T_ID, T_ID))
    performance_trend = cur.fetchall()'''

# ---------- PASS COUNT ----------
    cur.execute("""
    SELECT COUNT(*) AS passed
    FROM marks m
    JOIN teacher_subject ts ON ts.Sub_ID = m.Sub_ID
    WHERE ts.T_ID = %s AND m.Total >= 40
    """, (T_ID,))
    passed = cur.fetchone()["passed"] or 0

        # ---------- FAIL COUNT ----------
    cur.execute("""
    SELECT COUNT(*) AS failed
    FROM marks m
    JOIN teacher_subject ts ON ts.Sub_ID = m.Sub_ID
    WHERE ts.T_ID = %s AND m.Total < 40
    """, (T_ID,))
    failed = cur.fetchone()["failed"] or 0

    

    
    # ---------- TOPPERS ----------
    cur.execute("""
    SELECT s.S_ID, s.S_Name, m.Total
    FROM marks m
    JOIN student s ON m.S_ID = s.S_ID
    JOIN teacher_subject ts ON ts.Sub_ID = m.Sub_ID
    WHERE ts.T_ID = %s
    ORDER BY m.Total DESC
    LIMIT 5
""", (T_ID,))
    toppers = cur.fetchall()


    # ---------- WEAK STUDENTS ----------
    cur.execute("""
    SELECT s.S_ID, s.S_Name, m.Total
    FROM marks m
    JOIN student s ON m.S_ID = s.S_ID
    JOIN teacher_subject ts ON ts.Sub_ID = m.Sub_ID
    WHERE ts.T_ID = %s AND m.Total < 40
    ORDER BY m.Total ASC
    LIMIT 5
    """, (T_ID,))
    weak_students = cur.fetchall()

    # ---------- RECENT REMARKS ----------
    cur.execute("""
    SELECT s.S_Name, r.Remark, r.Date
    FROM student_remarks r
    JOIN student s ON r.S_ID = s.S_ID
    WHERE r.T_ID = %s
    ORDER BY r.Date DESC
    LIMIT 5
    """, (T_ID,))

    recent_remarks = cur.fetchall()

    con.close()

    return render_template(
        "faculty_dashboard.html",
        teacher_name=teacher_name,
        total_students=total_students,
        subjects_assigned=subjects_assigned,
        pending_marks=pending_marks,
        bar_data=bar_data,
        #performance_trend=performance_trend,
        passed=passed,
        failed=failed,
        toppers=toppers,
        weak_students=weak_students,
        recent_remarks=recent_remarks

    )

@app.route("/faculty_subject")
def faculty_subject():

    if "role" not in session or session["role"] != "teacher":
        return redirect("/")

    T_ID = session["T_ID"]

    con = get_connection()
    cur = con.cursor(dictionary=True)

    cur.execute("""
        SELECT sub.Sub_ID, sub.Sub_Code, sub.Sub_Name,
               sub.Sub_Department, sub.Sub_Semester
        FROM teacher_subject ts
        JOIN subject sub ON ts.Sub_ID = sub.Sub_ID
        WHERE ts.T_ID = %s
    """, (T_ID,))

    subjects = cur.fetchall()
    con.close()

    return render_template(
        "faculty_subject.html",
        subjects=subjects
    )

@app.route("/enter_marks/<int:Sub_ID>", methods=["GET", "POST"])
def enter_marks(Sub_ID):

    if "role" not in session or session["role"] != "teacher":
        return redirect("/")

    T_ID = session["T_ID"]

    con = get_connection()
    cur = con.cursor(dictionary=True)

    # ---- VERIFY TEACHER TEACHES THIS SUBJECT ----
    cur.execute("""
        SELECT sub.Sub_ID, sub.Sub_Name, sub.Sub_Department, sub.Sub_Semester
        FROM teacher_subject ts
        JOIN subject sub ON ts.Sub_ID = sub.Sub_ID
        WHERE ts.T_ID = %s AND sub.Sub_ID = %s
    """, (T_ID, Sub_ID))

    subject = cur.fetchone()
    if not subject:
        con.close()
        return "Unauthorized access", 403

    # ---- GET STUDENTS OF SAME DEPT & SEM ----
    cur.execute("""
        SELECT S_ID, Roll_No, S_Name
        FROM student
        WHERE S_Department = %s
          AND S_Semester = %s
        ORDER BY Roll_No
    """, (subject["Sub_Department"], subject["Sub_Semester"]))

    students = cur.fetchall()

    # ---- SAVE MARKS ----
    if request.method == "POST":
        for s in students:
            internal = int(request.form[f"internal_{s['S_ID']}"])
            external = int(request.form[f"external_{s['S_ID']}"])
            total = internal + external

            cur.execute("""
                INSERT INTO marks (S_ID, Sub_ID, Internal, External, Total)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    Internal=%s,
                    External=%s,
                    Total=%s
            """, (
                s["S_ID"], Sub_ID, internal, external, total,
                internal, external, total
            ))

        con.commit()

    con.close()

    return render_template(
        "enter_marks.html",
        subject=subject,
        students=students
    )




    


@app.route("/add_remark", methods=["GET", "POST"])
def add_remark():

    if "role" not in session or session["role"] != "teacher":
        return redirect("/")

    T_ID = session["T_ID"]

    con = get_connection()
    cur = con.cursor(dictionary=True)

    # Get students taught by this teacher (dept + semester logic)
    cur.execute("""
        SELECT DISTINCT s.S_ID, s.S_Name
        FROM student s
        JOIN subject sub
            ON s.S_Department = sub.Sub_Department
           AND s.S_Semester   = sub.Sub_Semester
        JOIN teacher_subject ts
            ON ts.Sub_ID = sub.Sub_ID
        WHERE ts.T_ID = %s
        ORDER BY s.S_Name
    """, (T_ID,))

    students = cur.fetchall()

    if request.method == "POST":
        S_ID = request.form["S_ID"]
        remark = request.form["remark"]

        cur.execute("""
            INSERT INTO student_remarks (S_ID, T_ID, Remark, Date)
            VALUES (%s, %s, %s, CURDATE())
        """, (S_ID, T_ID, remark))

        con.commit()
        con.close()
        return redirect("/teacher/dashboard")

    con.close()
    return render_template("add_remark.html", students=students)

@app.route("/prediction", methods=["GET", "POST"])
def prediction():

    if "role" not in session or session["role"] != "teacher":
        return redirect("/")

    T_ID = session["T_ID"]

    con = get_connection()
    cur = con.cursor(dictionary=True)

    # Fetch subjects taught by teacher
    cur.execute("""
        SELECT sub.Sub_ID, sub.Sub_Name
        FROM teacher_subject ts
        JOIN subject sub ON ts.Sub_ID = sub.Sub_ID
        WHERE ts.T_ID = %s
    """, (T_ID,))
    subjects = cur.fetchall()

    student_data = None
    predicted_marks = None

    if request.method == "POST":
        Sub_ID = request.form["Sub_ID"]
        keyword = request.form["keyword"]

        # Fetch student marks
        cur.execute("""
            SELECT s.S_Name, s.Roll_No,
                   m.Internal, m.External, m.Total
            FROM marks m
            JOIN student s ON m.S_ID = s.S_ID
            WHERE m.Sub_ID = %s
              AND (s.S_Name LIKE %s OR s.Roll_No = %s)
        """, (Sub_ID, f"%{keyword}%", keyword))

        student_data = cur.fetchone()

        if student_data:
            internal = student_data["Internal"]
            external = student_data["External"]

            # Prediction logic
            predicted_marks = round((internal * 0.4) + (external * 0.6), 2)

    con.close()

    return render_template(
        "faculty_prediction.html",
        subjects=subjects,
        student_data=student_data,
        predicted_marks=predicted_marks
    )
@app.route("/profile")
def faculty_profile():

    if "role" not in session or session["role"] != "teacher":
        return redirect("/")

    T_ID = session["T_ID"]

    con = get_connection()
    cur = con.cursor(dictionary=True)

    cur.execute("""
        SELECT T_ID, T_Name, T_Email, T_Phone, T_Department
        FROM teacher
        WHERE T_ID = %s
    """, (T_ID,))

    teacher = cur.fetchone()
    con.close()

    return render_template(
        "faculty_profile1.html",
        teacher=teacher
    )
@app.route("/admin/prediction", methods=["GET", "POST"])
def admin_prediction():

    if "role" not in session or session["role"] != "admin":
        return redirect("/")

    con = get_connection()
    cur = con.cursor(dictionary=True)

    # Load filters
    cur.execute("SELECT DISTINCT S_Department FROM student")
    departments = cur.fetchall()

    cur.execute("SELECT DISTINCT S_Semester FROM student")
    semesters = cur.fetchall()

    cur.execute("SELECT Sub_ID, Sub_Name FROM subject")
    subjects = cur.fetchall()

    result = None
    predicted_avg = None

    if request.method == "POST":
        dept = request.form["department"]
        sem = request.form["semester"]
        sub_id = request.form.get("Sub_ID")
        keyword = request.form["keyword"]

        query = """
            SELECT s.S_Name, s.Roll_No, sub.Sub_Name,
                   m.Internal, m.External, m.Total
            FROM student s
            JOIN marks m ON s.S_ID = m.S_ID
            JOIN subject sub ON m.Sub_ID = sub.Sub_ID
            WHERE s.S_Department=%s
              AND s.S_Semester=%s
              AND (s.S_Name LIKE %s OR s.Roll_No=%s)
        """

        params = [dept, sem, f"%{keyword}%", keyword]

        if sub_id:
            query += " AND sub.Sub_ID=%s"
            params.append(sub_id)

        cur.execute(query, tuple(params))
        result = cur.fetchall()

        if result:
            predicted_avg = round(
                sum(r["Total"] for r in result) / len(result), 2
            )

    con.close()

    return render_template(
        "admin_prediction.html",
        departments=departments,
        semesters=semesters,
        subjects=subjects,
        result=result,
        predicted_avg=predicted_avg
    )

@app.route("/student/prediction", methods=["GET", "POST"])
def student_prediction():

    if "role" not in session or session["role"] != "student":
        return redirect("/")

    S_ID = session["S_ID"]

    con = get_connection()
    cur = con.cursor(dictionary=True)

    # Get student's semester
    cur.execute("""
        SELECT S_Semester, S_Department
        FROM student
        WHERE S_ID = %s
    """, (S_ID,))
    student = cur.fetchone()

    # Get subjects of student's semester
    cur.execute("""
        SELECT Sub_ID, Sub_Name
        FROM subject
        WHERE Sub_Department=%s
          AND Sub_Semester=%s
    """, (student["S_Department"], student["S_Semester"]))
    subjects = cur.fetchall()

    marks = None
    predicted = None

    if request.method == "POST":
        Sub_ID = request.form["Sub_ID"]

        cur.execute("""
            SELECT Internal, External, Total
            FROM marks
            WHERE S_ID=%s AND Sub_ID=%s
        """, (S_ID, Sub_ID))

        marks = cur.fetchone()

        if marks:
            predicted = round(
                (marks["Internal"] * 0.4) + (marks["External"] * 0.6), 2
            )

    con.close()

    return render_template(
        "student_prediction.html",
        subjects=subjects,
        marks=marks,
        predicted=predicted
    )

@app.route("/student/report")
def student_report():

    if "role" not in session or session["role"] != "student":
        return redirect("/")

    S_ID = session.get("S_ID")
    if not S_ID:
        return redirect("/")

    con = get_connection()
    cur = con.cursor(dictionary=True)

    # Get student basic info
    cur.execute("""
        SELECT S_Name, Roll_No, S_Department, S_Semester
        FROM student
        WHERE S_ID = %s
    """, (S_ID,))
    student = cur.fetchone()

    # Get marks of all subjects in semester
    cur.execute("""
        SELECT sub.Sub_Name, m.Internal, m.External, m.Total
        FROM marks m
        JOIN subject sub ON m.Sub_ID = sub.Sub_ID
        WHERE m.S_ID = %s
    """, (S_ID,))
    results = cur.fetchall()

    # Calculations
    total_marks = sum(r["Total"] for r in results) if results else 0
    subject_count = len(results)
    percentage = round(total_marks / subject_count, 2) if subject_count else 0

    if percentage >= 60:
        grade = "A"
        status = "PASS"
    elif percentage >= 50:
        grade = "B"
        status = "PASS"
    elif percentage >= 40:
        grade = "C"
        status = "PASS"
    else:
        grade = "F"
        status = "FAIL"

    con.close()

    return render_template(
        "student_report.html",
        student=student,
        results=results,
        total_marks=total_marks,
        percentage=percentage,
        grade=grade,
        status=status
    )
@app.route("/admin/report", methods=["GET", "POST"])
def admin_report():

    if "role" not in session or session["role"] != "admin":
        return redirect("/")

    con = get_connection()
    cur = con.cursor(dictionary=True)

    # Load dropdown data
    cur.execute("SELECT DISTINCT S_Department FROM student")
    departments = cur.fetchall()

    cur.execute("SELECT DISTINCT S_Semester FROM student")
    semesters = cur.fetchall()

    report_data = None
    summary = None

    if request.method == "POST":
        department = request.form["department"]
        semester = request.form["semester"]

        # Fetch student results
        cur.execute("""
            SELECT s.S_Name, s.Roll_No, sub.Sub_Name,
                   m.Internal, m.External, m.Total
            FROM student s
            JOIN marks m ON s.S_ID = m.S_ID
            JOIN subject sub ON m.Sub_ID = sub.Sub_ID
            WHERE s.S_Department=%s AND s.S_Semester=%s
            ORDER BY s.S_Name
        """, (department, semester))

        report_data = cur.fetchall()

        if report_data:
            total_students = len(set(r["Roll_No"] for r in report_data))
            avg_score = round(
                sum(r["Total"] for r in report_data) / len(report_data), 2
            )
            passed = sum(1 for r in report_data if r["Total"] >= 40)
            failed = sum(1 for r in report_data if r["Total"] < 40)

            summary = {
                "total_students": total_students,
                "average_score": avg_score,
                "passed": passed,
                "failed": failed
            }

    con.close()

    return render_template(
        "admin_report.html",
        departments=departments,
        semesters=semesters,
        report_data=report_data,
        summary=summary
    )



#                      MAIN
# =====================================================
if __name__ == "__main__":
    app.run(debug=True)
