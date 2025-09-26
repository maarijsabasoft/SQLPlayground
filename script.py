import sqlite3
import random
from faker import Faker
from datetime import datetime, timedelta

fake = Faker()
db = sqlite3.connect("school_demo.db")
c = db.cursor()

# ---------- Drop old tables ----------
c.executescript("""
DROP TABLE IF EXISTS enrollments;
DROP TABLE IF EXISTS grades;
DROP TABLE IF EXISTS attendance;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS teachers;
DROP TABLE IF EXISTS students;
""")

# ---------- Create tables ----------
c.executescript("""
CREATE TABLE teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    hire_date DATE,
    department TEXT
);

CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    dob DATE,
    gender TEXT
);

CREATE TABLE courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    credits INTEGER,
    teacher_id INTEGER,
    FOREIGN KEY (teacher_id) REFERENCES teachers(id)
);

CREATE TABLE enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    course_id INTEGER,
    enroll_date DATE,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (course_id) REFERENCES courses(id)
);

CREATE TABLE grades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    enrollment_id INTEGER,
    grade TEXT,
    FOREIGN KEY (enrollment_id) REFERENCES enrollments(id)
);

CREATE TABLE attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    enrollment_id INTEGER,
    class_date DATE,
    status TEXT,
    FOREIGN KEY (enrollment_id) REFERENCES enrollments(id)
);
""")

# ---------- Seed Teachers (~50) ----------
departments = ["Math", "Science", "History", "Literature", "Computer Science",
               "Art", "Economics", "Philosophy"]
for _ in range(50):
    c.execute(
        "INSERT INTO teachers (name,email,hire_date,department) VALUES (?,?,?,?)",
        (fake.name(), fake.unique.email(),
         fake.date_between(start_date='-15y', end_date='-1y'),
         random.choice(departments))
    )

# ---------- Seed Students (~50) ----------
for _ in range(50):
    c.execute(
        "INSERT INTO students (name,email,dob,gender) VALUES (?,?,?,?)",
        (fake.name(), fake.unique.email(),
         fake.date_of_birth(minimum_age=18, maximum_age=25),
         random.choice(["M", "F"]))
    )

# ---------- Seed Courses (~50) ----------
teacher_ids = [t[0] for t in c.execute("SELECT id FROM teachers").fetchall()]
for _ in range(50):
    c.execute(
        "INSERT INTO courses (title, credits, teacher_id) VALUES (?,?,?)",
        (fake.catch_phrase(),  # random-ish course title
         random.randint(2,5),
         random.choice(teacher_ids))
    )

# ---------- Seed Enrollments (~50 per student ≈ 2500 rows) ----------
student_ids = [s[0] for s in c.execute("SELECT id FROM students").fetchall()]
course_ids  = [c_[0] for c_ in c.execute("SELECT id FROM courses").fetchall()]

for sid in student_ids:
    # each student 5–7 courses
    for course_id in random.sample(course_ids, random.randint(5,7)):
        c.execute(
            "INSERT INTO enrollments (student_id, course_id, enroll_date) VALUES (?,?,?)",
            (sid, course_id, fake.date_between(start_date='-1y', end_date='today'))
        )

# ---------- Seed Grades (~1 per enrollment) ----------
enrollment_ids = [e[0] for e in c.execute("SELECT id FROM enrollments").fetchall()]
for eid in enrollment_ids:
    c.execute(
        "INSERT INTO grades (enrollment_id, grade) VALUES (?,?)",
        (eid, random.choice(["A","B","C","D","F"]))
    )

# ---------- Seed Attendance (~10 per enrollment) ----------
start = datetime.now() - timedelta(days=120)
for eid in enrollment_ids:
    for _ in range(10):  # 10 sessions each
        c.execute(
            "INSERT INTO attendance (enrollment_id, class_date, status) VALUES (?,?,?)",
            (eid,
             (start + timedelta(days=random.randint(0,120))).date(),
             random.choice(["Present","Absent","Late"]))
        )

db.commit()
db.close()
print("school_demo.db created with ~50 rows per main table (and many child rows).")
