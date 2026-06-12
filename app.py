from flask import Flask, render_template

# Initialize the Flask application
app = Flask(__name__)

# ==========================================
# AUTHENTICATION & LANDING ROUTES
# ==========================================
@app.route('/')
def index():
    # The default landing page
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

# ==========================================
# MAIN DASHBOARD & DATA ENTRY ROUTES
# ==========================================
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/courses')
def courses():
    return render_template('courses.html')

@app.route('/tutors')
def tutors():
    return render_template('tutors.html')

@app.route('/halls')
def halls():
    return render_template('halls.html')

# ==========================================
# ALGORITHM & TIMETABLE ROUTES
# ==========================================
@app.route('/schedule')
def schedule():
    return render_template('schedule.html')

@app.route('/generation')
def generation():
    return render_template('generation.html')

@app.route('/timetable')
def timetable():
    return render_template('timetable.html')

# Start the server when this script is run
if __name__ == '__main__':
    app.run(debug=True)