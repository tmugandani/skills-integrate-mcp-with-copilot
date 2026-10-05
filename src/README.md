# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Create a teacher account. Passwords are stored as PBKDF2 hashes in a local,
   ignored `src/teachers.json` file:

   ```
   python src/create_teacher.py teacher
   ```

   The command prompts for the teacher's password. Add one account per teacher.
   Do not commit `src/teachers.json`.

3. Run the application:

   ```
   uvicorn src.app:app --reload
   ```

4. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc
   - Activities page: http://localhost:8000/

   Set `COOKIE_SECURE=true` when serving over HTTPS.

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/auth/login`                                                      | Sign in as a teacher                                                 |
| GET    | `/auth/session`                                                    | Check the current teacher session                                    |
| POST   | `/auth/logout`                                                     | Sign out                                                             |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up a student (teacher login required)                            |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Unregister a student (teacher login required)                      |

Teacher sessions expire after eight hours. Anyone can view activities and
participant rosters, but only authenticated teachers can register or unregister
students.

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in memory, which means data will be reset when the server restarts.
