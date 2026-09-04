from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import qrcode
import io
import base64
from datetime import datetime

app = Flask(__name__)

# --- 1. Database Setup (Fixed) ---
basedir = os.path.abspath(os.path.dirname(__file__))

# Ye line check karegi ki 'instance' folder hai ya nahi via code
instance_path = os.path.join(basedir, 'instance')
if not os.path.exists(instance_path):
    os.makedirs(instance_path) # Agar nahi hai to bana dega

# Ab database path set karein
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(instance_path, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- 2. Models ---
class Student(db.Model):
    id = db.Column(db.String(20), primary_key=True)  # Roll No hi ID banega
    name = db.Column(db.String(100), nullable=False)
    roll_no = db.Column(db.String(50))
    course = db.Column(db.String(100))
    year = db.Column(db.String(10))
    division = db.Column(db.String(5))
class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), db.ForeignKey('student.id'))
    # 👇 Ye Nayi Line Add Karein 👇
    subject = db.Column(db.String(50), nullable=False) 
    # 👆 Yahan tak 👆
    status = db.Column(db.String(10), default="Present")
    date = db.Column(db.String(20), default=datetime.now().strftime("%Y-%m-%d"))
    time = db.Column(db.String(20), default=datetime.now().strftime("%I:%M %p"))

# --- 3. Database Create ---
with app.app_context():
    db.create_all()

# --- 4. Routes ---

@app.route('/', methods=['GET', 'POST'])
def login():
    return render_template('login.html')

# --- Login Redirects (Jo Error de rahe the) ---
@app.route('/login_student', methods=['POST'])
def login_student():
    return redirect(url_for('student_view'))

@app.route('/login_faculty', methods=['POST'])
def login_faculty():
    return redirect(url_for('faculty_portal'))

@app.route('/login_admin', methods=['POST'])
def login_admin():
    return redirect(url_for('admin_dashboard'))

# --- Dashboards ---
@app.route('/admin')
def admin_dashboard():
    all_students = Student.query.all()
    all_attendance = Attendance.query.all()
    return render_template('dashboard.html', students=all_students, attendance=all_attendance)

@app.route('/faculty')
def faculty_portal():
    return render_template('faculty.html')

@app.route('/student_view')
def student_view():
    # Demo ke liye pehla student dikha rahe hain
    student = Student.query.first()
    if student:
        return redirect(url_for('student_profile', id=student.id))
    return "No student found! Ask Admin to add students."

@app.route('/student/<id>')
def student_profile(id):
    student = Student.query.get_or_404(id)
    
    # --- QR CODE GENERATION ---
    # Sirf ID store karein taaki scanner fast kaam kare
    qr_data = str(student.id)
    qr = qrcode.make(qr_data)
    
    buf = io.BytesIO()
    qr.save(buf, format='PNG')
    qr_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    
    return render_template('student_profile.html', student=student, qr_code=qr_base64)

# --- Attendance Logic ---
@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    try:
        # 1. Student ID aur Subject dono receive karein
        student_id = request.form.get('student_id')
        subject = request.form.get('subject') 

        # ID se student dhoondo
        student = Student.query.get(student_id)

        if student:
            # 2. Attendance lagate waqt Subject bhi save karein
            new_attendance = Attendance(
                student_id=student.id, 
                subject=subject,     # <--- Subject ab database mein jayega
                status='Present',
                date=datetime.now().strftime("%Y-%m-%d"),
                time=datetime.now().strftime("%I:%M %p")
            )
            db.session.add(new_attendance)
            db.session.commit()

            # Data wapas bhejo (Response)
            return jsonify({
                "success": True,
                "message": "Marked",
                "name": student.name,
                "roll": student.roll_no,
                "course": student.course,
                "subject": subject, # Frontend par dikhane ke liye
                "time": datetime.now().strftime("%I:%M %p")
            })
        else:
            return jsonify({"success": False, "message": "Student Not Found!"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)})

# --- Student Add Karna ---
# Is code ko app.py mein 'def add_student' ki jagah paste karein

@app.route('/add_student', methods=['POST'])
def add_student():
    name = request.form.get('name')
    roll_no = request.form.get('roll_no')
    course = request.form.get('course')
    division = request.form.get('division')
    
    # 👇 Form se Year ki value le rahe hain
    year = request.form.get('year') 

    if name and roll_no:
        student_id = roll_no
        existing = Student.query.get(student_id)
        if not existing:
            new_student = Student(
                id=student_id, 
                name=name, 
                roll_no=roll_no, 
                course=course,       
                year=year,           # <-- Ab jo select karoge (1st, 2nd, 3rd) wo save hoga
                division=division    
            )
            db.session.add(new_student)
            db.session.commit()

    return redirect(url_for('admin_dashboard'))

   # --- Is code ko app.py ke end mein paste karein ---
@app.route('/setup_demo')
def setup_demo():
    # 5 Naye Students ka Data
    students_data = [
        {"id": "101", "name": "Rahul Sharma", "roll": "CS101", "course": "BSC.IT", "div": "A"},
        {"id": "102", "name": "Priya Singh",  "roll": "IT102", "course": "BSC.IT", "div": "B"},
        {"id": "103", "name": "Amit Verma",   "roll": "ME103", "course": "Mechanical", "div": "A"},
        {"id": "104", "name": "Sneha Gupta",  "roll": "CS104", "course": "B.Tech CS", "div": "C"},
        {"id": "105", "name": "Vikram Malhotra", "roll": "CV105", "course": "Civil", "div": "A"}
    ]
    
    count = 0
    for data in students_data:
        if not Student.query.get(data["id"]):
            new_s = Student(
                id=data["id"],
                name=data["name"],
                roll_no=data["roll"],
                course=data["course"],
                year="2",
                division=data["div"]
            )
            db.session.add(new_s)
            count += 1
            
    db.session.commit()
    return f"<h1>Done! {count} New Students Added. <a href='/admin'>Dashboard Check Karo</a></h1>"

     # --- DELETE STUDENT LOGIC ---
@app.route('/delete_student/<string:id>')
def delete_student(id):
    student = Student.query.get(id)
    if student:
        # Pehle attendance delete karni padegi
        Attendance.query.filter_by(student_id=id).delete()
        db.session.delete(student)
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

# --- EDIT STUDENT LOGIC ---
# Is poore function ko replace karein
@app.route('/edit_student/<string:id>', methods=['GET', 'POST'])
def edit_student(id):
    student = Student.query.get(id)
    
    if request.method == 'POST':
        # Form se naya data lekar update karein
        student.name = request.form['name']
        student.roll_no = request.form['roll_no']
        student.course = request.form['course']
        
        # 👇 Ye Nayi Line hai (Year update karne ke liye)
        student.year = request.form['year']
        
        student.division = request.form['division']
        
        db.session.commit()
        return redirect(url_for('admin_dashboard'))

    return render_template('edit_student.html', student=student)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)

 