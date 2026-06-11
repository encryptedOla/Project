ExamSync — University Examination Scheduling
System
A web-based interface for building conflict-free examination timetables. Manage tutors,
courses, halls, and generate schedules automatically.
Table of Contents
Prerequisites
Getting the Project
Running the Interface
Navigating the App
Connecting to a Backend
Project Structure
Troubleshooting
Prerequisites
You don’t need to install anything special to view the frontend. You just need:
A computer with a modern browser (Chrome, Firefox, Edge, or Safari)
Git — to clone the repo
A simple local server — one of the options below
Why do I need a local server? Browsers block certain features (like loading CSS and JS
files) when you open HTML directly from your file system using file:// . A local server
fixes this by serving files over http://localhost instead.
Getting the Project
Open your terminal (Command Prompt, PowerShell, or Terminal on Mac/Linux) and run:
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/examsynced.git
# 2. Move into the project folder
cd examsynced
Replace YOUR_USERNAME with the actual GitHub username of the repo owner.
Running the Interface
Pick one of the methods below depending on what you have installed.
Option 1 — Python (Recommended, easiest)
Python comes pre-installed on most computers. Check if you have it:
python --version
# or
python3 --version
If you see a version number, run this inside the examsynced/ folder:
# Python 3
python3 -m http.server 3000
# Python 2 (older machines)
python -m SimpleHTTPServer 3000
Then open your browser and go to:
http://localhost:3000/login.html
Option 2 — Node.js / npx
If you have Node.js installed:
npx serve .
Then open your browser and go to:
http://localhost:3000/login.html
Option 3 — VS Code Live Server (easiest if you use VS Code)
1. Open VS Code
2. Install the Live Server extension (search for it in the Extensions tab)
3. Open the examsynced/ folder in VS Code
4. Right-click on login.html in the file explorer
5. Click “Open with Live Server”
Your browser will open automatically at http://127.0.0.1:5500/login.html .
Option 4 — PHP (if you have it installed)
php -S localhost:3000
Then open:
http://localhost:3000/login.html
Navigating the App
Once the server is running, this is the intended flow:
login.html
│
├── New user? → register.html → back to login.html
│
└── Existing user? → pages/dashboard.html
│
├── pages/tutors.html (Add / manage tutors)
Start here: http://localhost:3000/login.html
Use the sidebar on any dashboard page to move between sections. Every page is fully
navigable from the sidebar.
Note: Until you connect a real backend, forms will not save data permanently. The UI will
still open and display correctly, but submitted data will not persist after a page refresh.
Project Structure
examsynced/
│
├── login.html ← Sign-in page (start here)
├── register.html ← New account registration
│
├── auth.css ← Styles for login & register pages
├── styles.css ← Styles for all dashboard pages
├── app.js ← Shared JavaScript (you will create/edit this)
│
├── README.md ← This file
├── INTEGRATION_GUIDE.md ← Full backend wiring reference
│
└── pages/
├── dashboard.html ← Overview: stats, charts, activity
├── tutors.html ← Tutor/invigilator management
├── courses.html ← Course registration
├── halls.html ← Exam hall/venue management
├── schedule.html ← Exam window & session setup
├── generation.html ← Timetable generation (algorithm settings)
└── timetable.html ← View, filter & export the timetable
Connecting to a Backend
See INTEGRATION_GUIDE.md for the full breakdown of every input field and its matching
API endpoint.
├── pages/courses.html (Add / manage courses)
├── pages/halls.html (Add / manage exam halls)
├── pages/schedule.html (Set exam dates & time slots)
├── pages/generation.html (Run the scheduling algorithm)
└── pages/timetable.html (View & export the timetable)
Quick setup
1. Open app.js (create it in the root examsynced/ folder if it doesn’t exist yet)
2. Set your backend URL at the top of the file:
const API_BASE = 'http://localhost:8000'; // change this to your backend URL
3. All fetch calls in the app should use this variable:
const res = await fetch(`${API_BASE}/api/tutors`, {
method: 'GET',
headers: {
'Authorization': `Bearer ${localStorage.getItem('token')}`
}
});
4. After a successful login, store the token so all pages can use it:
localStorage.setItem('token', data.token);
5. To log out from any page:
localStorage.removeItem('token');
window.location.href = '../login.html';
Troubleshooting
The page is blank or CSS is not loading → You are opening the HTML file directly with
file:// . Use one of the local server options above instead.
Clicking a link goes to a 404 page → Make sure your server is running from inside the
examsynced/ folder, not from a parent folder.
Forms submit but nothing saves after refresh → The backend is not connected yet. Data
is only held in memory until you wire up the API. See INTEGRATION_GUIDE.md .
CORS error in the browser console → Your backend needs to allow requests from
http://localhost:3000 . Add this header on your backend:
Access-Control-Allow-Origin: http://localhost:3000
Port 3000 is already in use → Change the port number in your server command, e.g.
python3 -m http.server 4000 , then visit http://localhost:4000/login.html .
Login redirects but pages look broken → Check that styles.css and app.js paths are
correct. Dashboard pages reference them as ../styles.css and ../app.js .
Two Key Files to Read
File What it covers
README.md How to run the interface locally (this file)
INTEGRATION_GUIDE.md Every input field, API endpoint, and backend wiring instruction
ExamSync — University Scheduling System
