from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_cors import CORS
from datetime import timedelta
import os
from dotenv import load_dotenv

load_dotenv()

# ── App setup ──────────────────────────────────────────────
app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# ── MySQL Configuration ────────────────────────────────────
DB_USER     = os.getenv('DB_USER',     'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_HOST     = os.getenv('DB_HOST',     'localhost')
DB_NAME     = os.getenv('DB_NAME',     'examsynced')

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY']           = os.getenv('JWT_SECRET_KEY', 'change-this-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=7)

# ── Extensions ─────────────────────────────────────────────
db     = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt    = JWTManager(app)


# ══════════════════════════════════════════════════════════
#  DATABASE MODELS  (mirror every table in database_setup.sql)
# ══════════════════════════════════════════════════════════

class User(db.Model):
    __tablename__ = 'users'

    id             = db.Column(db.Integer,     primary_key=True)
    first_name     = db.Column(db.String(80),  nullable=False)
    last_name      = db.Column(db.String(80),  nullable=False)
    email          = db.Column(db.String(120), unique=True, nullable=False)
    institution    = db.Column(db.String(120), nullable=False)
    department     = db.Column(db.String(120), nullable=True)
    role           = db.Column(
                        db.Enum('registry', 'admin', 'tutor', 'viewer'),
                        nullable=False, default='viewer'
                    )
    password_hash  = db.Column(db.String(256), nullable=False)
    terms_accepted = db.Column(db.Boolean,     default=False)
    created_at     = db.Column(db.DateTime,    server_default=db.func.now())

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id':          self.id,
            'first_name':  self.first_name,
            'last_name':   self.last_name,
            'name':        f"{self.first_name} {self.last_name}",
            'email':       self.email,
            'institution': self.institution,
            'department':  self.department,
            'role':        self.role,
        }


class Tutor(db.Model):
    __tablename__ = 'tutors'

    id         = db.Column(db.Integer,     primary_key=True)
    name       = db.Column(db.String(120), nullable=False)
    staff_id   = db.Column(db.String(40),  unique=True, nullable=False)
    department = db.Column(db.String(120), nullable=True)
    email      = db.Column(db.String(120), unique=True, nullable=True)
    phone      = db.Column(db.String(30),  nullable=True)
    created_at = db.Column(db.DateTime,    server_default=db.func.now())

    # One tutor can have many courses
    courses    = db.relationship('Course', backref='tutor', lazy=True)

    def to_dict(self):
        return {
            'id':         self.id,
            'name':       self.name,
            'staff_id':   self.staff_id,
            'department': self.department,
            'email':      self.email,
            'phone':      self.phone,
        }


class Course(db.Model):
    __tablename__ = 'courses'

    id            = db.Column(db.Integer,     primary_key=True)
    code          = db.Column(db.String(20),  unique=True, nullable=False)
    name          = db.Column(db.String(150), nullable=False)
    units         = db.Column(db.Integer,     nullable=False, default=3)
    department    = db.Column(db.String(120), nullable=True)
    level         = db.Column(
                        db.Enum('L100', 'L200', 'L300', 'L400'),
                        nullable=False, default='L100'
                    )
    student_count = db.Column(db.Integer,     nullable=False, default=0)
    tutor_id      = db.Column(db.Integer,     db.ForeignKey('tutors.id'), nullable=True)
    duration      = db.Column(db.String(20),  default='3 hrs')
    created_at    = db.Column(db.DateTime,    server_default=db.func.now())

    def to_dict(self):
        return {
            'id':            self.id,
            'code':          self.code,
            'name':          self.name,
            'units':         self.units,
            'department':    self.department,
            'level':         self.level,
            'student_count': self.student_count,
            'tutor_id':      self.tutor_id,
            'tutor_name':    self.tutor.name if self.tutor else None,
            'duration':      self.duration,
        }


class Hall(db.Model):
    __tablename__ = 'halls'

    id         = db.Column(db.Integer,     primary_key=True)
    name       = db.Column(db.String(120), nullable=False)
    location   = db.Column(db.String(120), nullable=True)
    capacity   = db.Column(db.Integer,     nullable=False, default=0)
    facilities = db.Column(db.Text,        nullable=True)   # stored as comma-separated string
    status     = db.Column(
                    db.Enum('available', 'unavailable'),
                    nullable=False, default='available'
                )
    created_at = db.Column(db.DateTime,    server_default=db.func.now())

    def to_dict(self):
        return {
            'id':         self.id,
            'name':       self.name,
            'location':   self.location,
            'capacity':   self.capacity,
            'facilities': self.facilities.split(',') if self.facilities else [],
            'status':     self.status,
        }


class ScheduleSession(db.Model):
    __tablename__ = 'schedule_sessions'

    id           = db.Column(db.Integer, primary_key=True)
    date         = db.Column(db.Date,    nullable=False)
    session_type = db.Column(
                        db.Enum('morning', 'afternoon', 'evening'),
                        nullable=False
                    )
    start_time   = db.Column(db.Time,    nullable=False)
    end_time     = db.Column(db.Time,    nullable=False)
    created_at   = db.Column(db.DateTime, server_default=db.func.now())

    # One session can have many timetable entries
    entries      = db.relationship('TimetableEntry', backref='session', lazy=True)

    def to_dict(self):
        return {
            'id':           self.id,
            'date':         str(self.date),
            'session_type': self.session_type,
            'start_time':   str(self.start_time),
            'end_time':     str(self.end_time),
        }


class TimetableEntry(db.Model):
    __tablename__ = 'timetable_entries'

    id           = db.Column(db.Integer,  primary_key=True)
    session_id   = db.Column(db.Integer,  db.ForeignKey('schedule_sessions.id'), nullable=False)
    course_id    = db.Column(db.Integer,  db.ForeignKey('courses.id'),           nullable=False)
    hall_id      = db.Column(db.Integer,  db.ForeignKey('halls.id'),             nullable=False)
    tutor_id     = db.Column(db.Integer,  db.ForeignKey('tutors.id'),            nullable=True)
    generated_at = db.Column(db.DateTime, server_default=db.func.now())

    # Relationships for easy lookups
    course       = db.relationship('Course', backref='timetable_entries')
    hall         = db.relationship('Hall',   backref='timetable_entries')
    tutor        = db.relationship('Tutor',  backref='timetable_entries')

    def to_dict(self):
        return {
            'id':          self.id,
            'session':     self.session.to_dict() if self.session else None,
            'course':      self.course.to_dict()  if self.course  else None,
            'hall':        self.hall.to_dict()    if self.hall    else None,
            'tutor_name':  self.tutor.name        if self.tutor   else None,
        }


# ══════════════════════════════════════════════════════════
#  PAGE ROUTES  (serve HTML from /templates)
# ══════════════════════════════════════════════════════════

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/dashboard')
def dashboard_page():
    return render_template('dashboard.html')

@app.route('/courses')
def courses_page():
    return render_template('courses.html')

@app.route('/halls')
def halls_page():
    return render_template('halls.html')

@app.route('/tutors')
def tutors_page():
    return render_template('tutors.html')

@app.route('/generation')
def generation_page():
    return render_template('generation.html')

@app.route('/schedule')
def schedule_page():
    return render_template('schedule.html')

@app.route('/timetable')
def timetable_page():
    return render_template('timetable.html')


# ══════════════════════════════════════════════════════════
#  AUTH API ROUTES
# ══════════════════════════════════════════════════════════

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()

    required = ['first_name', 'last_name', 'email', 'password', 'institution']
    missing  = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({'error': f"Missing fields: {', '.join(missing)}"}), 400

    if User.query.filter_by(email=data['email'].lower().strip()).first():
        return jsonify({'error': 'An account with this email already exists.'}), 409

    if len(data['password']) < 8:
        return jsonify({'error': 'Password must be at least 8 characters.'}), 400

    allowed_roles = ['registry', 'admin', 'tutor', 'viewer']
    role = data.get('role', 'viewer')
    if role not in allowed_roles:
        return jsonify({'error': f"Invalid role. Choose from: {', '.join(allowed_roles)}"}), 400

    user = User(
        first_name     = data['first_name'].strip(),
        last_name      = data['last_name'].strip(),
        email          = data['email'].lower().strip(),
        institution    = data['institution'].strip(),
        department     = data.get('department', '').strip(),
        role           = role,
        terms_accepted = data.get('terms_accepted', False),
    )
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({'token': token, 'user': user.to_dict()}), 201


@app.route('/api/auth/login', methods=['POST'])
def login():
    data     = request.get_json()
    email    = data.get('email', '').lower().strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid email or password.'}), 401

    remember = data.get('remember_me', False)
    expires  = timedelta(days=30) if remember else timedelta(days=7)
    token    = create_access_token(identity=str(user.id), expires_delta=expires)
    return jsonify({'token': token, 'user': user.to_dict()}), 200


@app.route('/api/auth/me', methods=['GET'])
@jwt_required()
def get_me():
    user_id = get_jwt_identity()
    user    = User.query.get(int(user_id))
    if not user:
        return jsonify({'error': 'User not found.'}), 404
    return jsonify({'user': user.to_dict()}), 200


@app.route('/api/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    return jsonify({'message': 'Logged out successfully.'}), 200


# ══════════════════════════════════════════════════════════
#  TUTORS API
# ══════════════════════════════════════════════════════════

@app.route('/api/tutors', methods=['GET'])
@jwt_required()
def get_tutors():
    q      = request.args.get('q', '')
    tutors = Tutor.query.filter(Tutor.name.ilike(f'%{q}%')).all() if q else Tutor.query.all()
    return jsonify({'tutors': [t.to_dict() for t in tutors]}), 200


@app.route('/api/tutors', methods=['POST'])
@jwt_required()
def create_tutor():
    data = request.get_json()
    if not data.get('name') or not data.get('staff_id'):
        return jsonify({'error': 'Name and staff_id are required.'}), 400
    if Tutor.query.filter_by(staff_id=data['staff_id']).first():
        return jsonify({'error': 'Staff ID already exists.'}), 409

    tutor = Tutor(
        name       = data['name'].strip(),
        staff_id   = data['staff_id'].strip(),
        department = data.get('department', '').strip(),
        email      = data.get('email', '').strip() or None,
        phone      = data.get('phone', '').strip() or None,
    )
    db.session.add(tutor)
    db.session.commit()
    return jsonify({'tutor': tutor.to_dict()}), 201


@app.route('/api/tutors/<int:tutor_id>', methods=['PUT'])
@jwt_required()
def update_tutor(tutor_id):
    tutor = Tutor.query.get_or_404(tutor_id)
    data  = request.get_json()
    tutor.name       = data.get('name',       tutor.name)
    tutor.staff_id   = data.get('staff_id',   tutor.staff_id)
    tutor.department = data.get('department', tutor.department)
    tutor.email      = data.get('email',      tutor.email)
    tutor.phone      = data.get('phone',      tutor.phone)
    db.session.commit()
    return jsonify({'tutor': tutor.to_dict()}), 200


@app.route('/api/tutors/<int:tutor_id>', methods=['DELETE'])
@jwt_required()
def delete_tutor(tutor_id):
    tutor = Tutor.query.get_or_404(tutor_id)
    db.session.delete(tutor)
    db.session.commit()
    return jsonify({'message': 'Tutor deleted.'}), 200


# ══════════════════════════════════════════════════════════
#  COURSES API
# ══════════════════════════════════════════════════════════

@app.route('/api/courses', methods=['GET'])
@jwt_required()
def get_courses():
    q       = request.args.get('q', '')
    courses = Course.query.filter(
        (Course.name.ilike(f'%{q}%')) | (Course.code.ilike(f'%{q}%'))
    ).all() if q else Course.query.all()
    return jsonify({'courses': [c.to_dict() for c in courses]}), 200


@app.route('/api/courses', methods=['POST'])
@jwt_required()
def create_course():
    data = request.get_json()
    if not data.get('code') or not data.get('name'):
        return jsonify({'error': 'Code and name are required.'}), 400
    if Course.query.filter_by(code=data['code'].upper()).first():
        return jsonify({'error': 'Course code already exists.'}), 409

    course = Course(
        code          = data['code'].upper().strip(),
        name          = data['name'].strip(),
        units         = int(data.get('units', 3)),
        department    = data.get('department', '').strip(),
        level         = data.get('level', 'L100'),
        student_count = int(data.get('student_count', 0)),
        tutor_id      = data.get('tutor_id') or None,
        duration      = data.get('duration', '3 hrs'),
    )
    db.session.add(course)
    db.session.commit()
    return jsonify({'course': course.to_dict()}), 201


@app.route('/api/courses/<int:course_id>', methods=['PUT'])
@jwt_required()
def update_course(course_id):
    course = Course.query.get_or_404(course_id)
    data   = request.get_json()
    course.code          = data.get('code',          course.code)
    course.name          = data.get('name',          course.name)
    course.units         = data.get('units',         course.units)
    course.department    = data.get('department',    course.department)
    course.level         = data.get('level',         course.level)
    course.student_count = data.get('student_count', course.student_count)
    course.tutor_id      = data.get('tutor_id',      course.tutor_id)
    course.duration      = data.get('duration',      course.duration)
    db.session.commit()
    return jsonify({'course': course.to_dict()}), 200


@app.route('/api/courses/<int:course_id>', methods=['DELETE'])
@jwt_required()
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    return jsonify({'message': 'Course deleted.'}), 200


# ══════════════════════════════════════════════════════════
#  HALLS API
# ══════════════════════════════════════════════════════════

@app.route('/api/halls', methods=['GET'])
@jwt_required()
def get_halls():
    halls = Hall.query.all()
    return jsonify({'halls': [h.to_dict() for h in halls]}), 200


@app.route('/api/halls', methods=['POST'])
@jwt_required()
def create_hall():
    data = request.get_json()
    if not data.get('name') or not data.get('capacity'):
        return jsonify({'error': 'Name and capacity are required.'}), 400

    # Accept facilities as list or comma string
    facilities = data.get('facilities', '')
    if isinstance(facilities, list):
        facilities = ','.join(facilities)

    hall = Hall(
        name       = data['name'].strip(),
        location   = data.get('location', '').strip(),
        capacity   = int(data['capacity']),
        facilities = facilities.strip(),
        status     = data.get('status', 'available'),
    )
    db.session.add(hall)
    db.session.commit()
    return jsonify({'hall': hall.to_dict()}), 201


@app.route('/api/halls/<int:hall_id>', methods=['PUT'])
@jwt_required()
def update_hall(hall_id):
    hall = Hall.query.get_or_404(hall_id)
    data = request.get_json()
    facilities = data.get('facilities', hall.facilities)
    if isinstance(facilities, list):
        facilities = ','.join(facilities)
    hall.name       = data.get('name',     hall.name)
    hall.location   = data.get('location', hall.location)
    hall.capacity   = data.get('capacity', hall.capacity)
    hall.facilities = facilities
    hall.status     = data.get('status',   hall.status)
    db.session.commit()
    return jsonify({'hall': hall.to_dict()}), 200


@app.route('/api/halls/<int:hall_id>', methods=['DELETE'])
@jwt_required()
def delete_hall(hall_id):
    hall = Hall.query.get_or_404(hall_id)
    db.session.delete(hall)
    db.session.commit()
    return jsonify({'message': 'Hall deleted.'}), 200


# ══════════════════════════════════════════════════════════
#  SCHEDULE SESSIONS API
# ══════════════════════════════════════════════════════════

@app.route('/api/schedule/sessions', methods=['GET'])
@jwt_required()
def get_sessions():
    sessions = ScheduleSession.query.order_by(ScheduleSession.date).all()
    return jsonify({'sessions': [s.to_dict() for s in sessions]}), 200


@app.route('/api/schedule/sessions', methods=['POST'])
@jwt_required()
def create_session():
    data = request.get_json()
    if not data.get('date') or not data.get('session_type'):
        return jsonify({'error': 'Date and session_type are required.'}), 400

    from datetime import datetime, time as dtime
    session = ScheduleSession(
        date         = datetime.strptime(data['date'], '%Y-%m-%d').date(),
        session_type = data['session_type'],
        start_time   = datetime.strptime(data['start_time'], '%H:%M').time(),
        end_time     = datetime.strptime(data['end_time'],   '%H:%M').time(),
    )
    db.session.add(session)
    db.session.commit()
    return jsonify({'session': session.to_dict()}), 201


@app.route('/api/schedule/sessions/<int:session_id>', methods=['DELETE'])
@jwt_required()
def delete_session(session_id):
    session = ScheduleSession.query.get_or_404(session_id)
    db.session.delete(session)
    db.session.commit()
    return jsonify({'message': 'Session deleted.'}), 200


# ══════════════════════════════════════════════════════════
#  TIMETABLE API
# ══════════════════════════════════════════════════════════

@app.route('/api/timetable/generate', methods=['POST'])
@jwt_required()
def generate_timetable():
    """
    Basic round-robin scheduler.
    Assigns each course to an available session + hall.
    Replace the scheduling logic here with your GA/SA optimizer.py later.
    """
    courses  = Course.query.all()
    sessions = ScheduleSession.query.order_by(ScheduleSession.date).all()
    halls    = Hall.query.filter_by(status='available').all()

    if not courses:
        return jsonify({'error': 'No courses found. Add courses first.'}), 400
    if not sessions:
        return jsonify({'error': 'No schedule sessions found. Add sessions first.'}), 400
    if not halls:
        return jsonify({'error': 'No available halls found. Add halls first.'}), 400

    # Clear previous timetable
    TimetableEntry.query.delete()

    entries = []
    hall_idx   = 0
    session_idx = 0

    for course in courses:
        # Pick a hall with enough capacity (or fall back to any hall)
        suitable_halls = [h for h in halls if h.capacity >= course.student_count]
        chosen_hall    = suitable_halls[hall_idx % len(suitable_halls)] if suitable_halls else halls[hall_idx % len(halls)]
        chosen_session = sessions[session_idx % len(sessions)]

        entry = TimetableEntry(
            session_id = chosen_session.id,
            course_id  = course.id,
            hall_id    = chosen_hall.id,
            tutor_id   = course.tutor_id,
        )
        db.session.add(entry)
        entries.append(entry)
        hall_idx    += 1
        session_idx += 1

    db.session.commit()
    return jsonify({
        'message':       'Timetable generated successfully.',
        'total_entries': len(entries),
    }), 201


@app.route('/api/timetable/latest', methods=['GET'])
@jwt_required()
def get_timetable():
    entries = TimetableEntry.query.all()
    return jsonify({'entries': [e.to_dict() for e in entries]}), 200


# ══════════════════════════════════════════════════════════
#  DASHBOARD STATS
# ══════════════════════════════════════════════════════════

@app.route('/api/dashboard/stats', methods=['GET'])
@jwt_required()
def dashboard_stats():
    return jsonify({
        'total_courses':  Course.query.count(),
        'total_tutors':   Tutor.query.count(),
        'total_halls':    Hall.query.count(),
        'total_exams':    TimetableEntry.query.count(),
    }), 200


# ══════════════════════════════════════════════════════════
#  RUN
# ══════════════════════════════════════════════════════════

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅ Connected to MySQL — all tables are ready.")
    app.run(debug=True, port=5000)
