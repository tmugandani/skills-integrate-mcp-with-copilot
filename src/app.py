"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

import hashlib
import hmac
import json
import os
import secrets
import time
from fastapi.staticfiles import StaticFiles
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")
TEACHERS_FILE = current_dir / "teachers.json"
SESSION_COOKIE = "teacher_session"
SESSION_DURATION_SECONDS = 8 * 60 * 60
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
sessions: dict[str, tuple[str, float]] = {}


class LoginRequest(BaseModel):
    username: str
    password: str


def hash_password(password: str) -> str:
    """Hash a teacher password using PBKDF2-HMAC-SHA256."""
    iterations = 600_000
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password hash produced by hash_password."""
    try:
        algorithm, iterations, salt, expected_digest = password_hash.split("$")
        if algorithm != "pbkdf2_sha256":
            raise ValueError("Unsupported password hash algorithm")
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt), int(iterations)
        )
    except (ValueError, TypeError) as error:
        raise HTTPException(
            status_code=500, detail="Teacher credential configuration is invalid"
        ) from error
    return hmac.compare_digest(digest.hex(), expected_digest)


def load_teacher_accounts() -> dict[str, str]:
    try:
        accounts = json.loads(TEACHERS_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=503,
            detail="Teacher accounts are not configured on this server",
        ) from error
    except (OSError, json.JSONDecodeError) as error:
        raise HTTPException(
            status_code=500, detail="Teacher account file could not be read"
        ) from error

    if not isinstance(accounts, dict) or any(
        not isinstance(username, str) or not isinstance(password_hash, str)
        for username, password_hash in accounts.items()
    ):
        raise HTTPException(
            status_code=500, detail="Teacher account configuration is invalid"
        )
    return accounts


def get_current_teacher(request: Request) -> str:
    token = request.cookies.get(SESSION_COOKIE)
    session = sessions.get(token) if token else None
    if session is None or session[1] <= time.time():
        if token:
            sessions.pop(token, None)
        raise HTTPException(status_code=401, detail="Teacher login required")
    return session[0]


@app.post("/auth/login")
def login(credentials: LoginRequest, response: Response):
    accounts = load_teacher_accounts()
    password_hash = accounts.get(credentials.username)
    if password_hash is None or not verify_password(
        credentials.password, password_hash
    ):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = secrets.token_urlsafe(32)
    sessions[token] = (
        credentials.username,
        time.time() + SESSION_DURATION_SECONDS,
    )
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=SESSION_DURATION_SECONDS,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="strict",
        path="/",
    )
    return {"username": credentials.username}


@app.get("/auth/session")
def get_session(request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    session = sessions.get(token) if token else None
    if session is None or session[1] <= time.time():
        if token:
            sessions.pop(token, None)
        return {"authenticated": False}
    return {"authenticated": True, "username": session[0]}


@app.post("/auth/logout")
def logout(request: Request, response: Response):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        sessions.pop(token, None)
    response.delete_cookie(SESSION_COOKIE, path="/", samesite="strict")
    return {"message": "Signed out"}

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(
    activity_name: str, email: str, _teacher: str = Depends(get_current_teacher)
):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(
    activity_name: str, email: str, _teacher: str = Depends(get_current_teacher)
):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
