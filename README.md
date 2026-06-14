# ExamSync — University Examination Scheduling System

> A Flask-powered web application for building conflict-free examination timetables.
> Manage tutors, courses, halls, and generate schedules automatically.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Setting Up the Database](#setting-up-the-database)
- [Running the App](#running-the-app)
- [Navigating the App](#navigating-the-app)
- [API Endpoints](#api-endpoints)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

You need the following installed before you start:

- [Python 3.8+](https://www.python.org/downloads/)
- [MySQL](https://dev.mysql.com/downloads/mysql/) — the database server
- [Git](https://git-scm.com/downloads) — to clone the repo
- A terminal (Command Prompt, PowerShell, or Terminal on Mac/Linux)

---

## Project Structure

```
timetable_project/
│
├── static/                     # All styling, scripts, and images
│   ├── css/
│   │   └── styles.css          ← Move your styles.css here
│   ├── js/                     ← Future JavaScript files
│   └── img/                    ← Any logos or icons
│
├── templates/                  # All HTML files (Flask renders these)
│   ├── index.html              ← Landing page
│   ├── login.html              ← Sign-in page
│   ├── register.html           ← New account registration
│   ├── dashboard.html          ← Main admin panel
│   ├── courses.html            ← Where admin inputs course data
│   ├── halls.html              ← Where admin inputs room data
│   ├── tutors.html             ← Where admin inputs lecturers
│   ├── generation.html         ← Loading screen when GA/SA is running
│   ├── schedule.html           ← Schedule setup
│   └── timetable.html          ← Where the final result is displayed
│
├── app.py                      ← Main Python server file
├── optimizer.py                ← Where GA and SA Python code will live
├── database_setup.sql          ← MySQL table creation scripts
├── requirements.txt            ← Python dependencies
├── .env                        ← Your private credentials (never commit this)
├── .env.example                ← Template for .env
└── README.md                   ← This file
```

---

## Setting Up the Database

### Step 1 — Start MySQL and create the database

Open your terminal and log into MySQL:

```bash
mysql -u root -p
```

Then run the setup script which creates all tables automatically:

```bash
mysql -u root -p < database_setup.sql
```

This creates the `examsynced` database with these 6 tables:

| Table | What it stores |
|---|---|
| `users` | Login accounts (from register/login page) |
| `tutors` | Lecturers and invigilators |
| `courses` | Exam courses with student counts |
| `halls` | Exam venues with capacity |
| `schedule_sessions` | Available exam dates and time slots |
| `timetable_entries` | The final generated timetable |

---

### Step 2 — Create your `.env` file

```bash
cp .env.example .env
```

Open `.env` and fill in your MySQL password:

```env
DB_USER=root
DB_PASSWORD=your_mysql_password_here
DB_HOST=localhost
DB_NAME=examsynced
JWT_SECRET_KEY=pick-a-long-random-string
```

---

## Running the App

### Step 1 — Install Python dependencies

```bash
pip install -r requirements.txt
```

### Step 2 — Run Flask

```bash
python app.py
```

You will see:

```
✅ Connected to MySQL — all tables are ready.
 * Running on http://127.0.0.1:5000
```

### Step 3 — Open in browser

```
http://localhost:5000
```

You will land on the login page. Register a new account and you're in.

---

## Navigating the App

All pages are served by Flask from the `/templates` folder.
Use the URL routes below to navigate — do **not** open HTML files directly:

| URL | Page |
|---|---|
| `http://localhost:5000/` | Login page |
| `http://localhost:5000/login` | Login page |
| `http://localhost:5000/register` | Register page |
| `http://localhost:5000/dashboard` | Dashboard |
| `http://localhost:5000/tutors` | Tutor management |
| `http://localhost:5000/courses` | Course management |
| `http://localhost:5000/halls` | Exam halls |
| `http://localhost:5000/schedule` | Schedule setup |
| `http://localhost:5000/generation` | Timetable generation |
| `http://localhost:5000/timetable` | View timetable |

**App flow:**

```
/ (login)
  │
  ├── New user?  →  /register  →  /dashboard
  │
  └── Existing?  →  /dashboard
                      │
                      ├── /tutors
                      ├── /courses
                      ├── /halls
                      ├── /schedule
                      ├── /generation
                      └── /timetable
```

---

## API Endpoints

Every API call requires a JWT token in the header (except login and register):

```
Authorization: Bearer <your_token>
```

The token is returned when you log in or register, and stored in `localStorage`.

### Auth

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Create a new account |
| `POST` | `/api/auth/login` | Login, returns JWT token |
| `GET` | `/api/auth/me` | Get current logged-in user |
| `POST` | `/api/auth/logout` | Logout |

### Tutors

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/tutors` | List all tutors |
| `POST` | `/api/tutors` | Add a tutor |
| `PUT` | `/api/tutors/<id>` | Edit a tutor |
| `DELETE` | `/api/tutors/<id>` | Delete a tutor |

### Courses

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/courses` | List all courses |
| `POST` | `/api/courses` | Add a course |
| `PUT` | `/api/courses/<id>` | Edit a course |
| `DELETE` | `/api/courses/<id>` | Delete a course |

### Halls

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/halls` | List all halls |
| `POST` | `/api/halls` | Add a hall |
| `PUT` | `/api/halls/<id>` | Edit a hall |
| `DELETE` | `/api/halls/<id>` | Delete a hall |

### Schedule

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/schedule/sessions` | List all sessions |
| `POST` | `/api/schedule/sessions` | Add a session |
| `DELETE` | `/api/schedule/sessions/<id>` | Remove a session |

### Timetable

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/timetable/generate` | Run the scheduling algorithm |
| `GET` | `/api/timetable/latest` | Get the generated timetable |
| `GET` | `/api/dashboard/stats` | Get dashboard stats |

---

## Troubleshooting

**`ModuleNotFoundError`**
→ Run `pip install -r requirements.txt` again.

**`Access denied for user 'root'@'localhost'`**
→ Your MySQL password in `.env` is wrong. Double-check `DB_PASSWORD`.

**`Unknown database 'examsynced'`**
→ You haven't run the setup script yet. Run:
```bash
mysql -u root -p < database_setup.sql
```

**`Can't connect to MySQL server`**
→ MySQL is not running. Start it with:
```bash
# Mac
brew services start mysql

# Windows — open Services and start MySQL
# Linux
sudo systemctl start mysql
```

**`CORS error in the browser console`**
→ Flask-CORS is already configured in `app.py`. If you still see this, make sure you're accessing the app via `http://localhost:5000` and not opening HTML files directly.

**Page shows but CSS is missing**
→ Make sure `styles.css` is inside `static/css/styles.css`. Then in your HTML templates reference it as:
```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/styles.css') }}">
```

**`JWT token missing or expired`**
→ Log in again at `http://localhost:5000/login`. The token lasts 7 days (30 days if "Remember me" is checked).

---

*ExamSync — University Examination Scheduling System*
