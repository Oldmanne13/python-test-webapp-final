from flask import Flask, render_template, request, redirect, url_for, session, Response
import sqlite3
import json
import csv
import io
import os
import hmac
import random
import copy
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-in-production")
TEACHER_PASSWORD = os.environ.get("TEACHER_PASSWORD", "python123")
DB = "python_test.db"

QUESTIONS = [
    {
        "id": 1,
        "phase": "all",
        "category": "Variable",
        "prompt": "Hvad skriver koden?",
        "code": "a = 2026\nb = 3\nc = a + b\nprint(c)",
        "options": ["2023", "2026", "2029", "Fejl"],
        "answer": "2029",
        "explanation": "c bliver summen af a og b: 2026 + 3 = 2029.",
    },
    {
        "id": 2,
        "phase": "all",
        "category": "Variable",
        "prompt": "Hvad er formålet med en variabel?",
        "code": "",
        "options": [
            "At gemme en værdi",
            "At gentage kode",
            "At importere et bibliotek",
            "At stoppe programmet",
        ],
        "answer": "At gemme en værdi",
        "explanation": "En variabel binder et navn til en værdi, som programmet kan bruge og ændre.",
    },
    {
        "id": 3,
        "phase": "all",
        "category": "Loops",
        "prompt": "Hvilke tal udskrives?",
        "code": "for i in range(0, 4):\n    print(i)",
        "options": ["0, 1, 2, 3", "0, 1, 2, 3, 4", "1, 2, 3, 4", "4"],
        "answer": "0, 1, 2, 3",
        "explanation": "Slutværdien i range er ikke inkluderet.",
    },
    {
        "id": 4,
        "phase": "all",
        "category": "Betingelser",
        "prompt": "Hvad udskrives?",
        "code": "afstand = 25\nif afstand < 20:\n    print(\"STOP\")\nelse:\n    print(\"OK\")",
        "options": ["STOP", "OK", "25", "Fejl"],
        "answer": "OK",
        "explanation": "25 er ikke mindre end 20, så else-grenen udføres.",
    },
    {
        "id": 5,
        "phase": "all",
        "category": "Fejlfinding",
        "prompt": "Hvilken ændring retter koden?",
        "code": "if a == 10\n    print(\"a er lig med 10\")",
        "options": ["Tilføj : efter 10", "Skift == til =", "Fjern indryk", "Skift if til for"],
        "answer": "Tilføj : efter 10",
        "explanation": "En if-sætning afsluttes med kolon før den indrykkede blok.",
    },
    {
        "id": 6,
        "phase": "all",
        "category": "Loops",
        "prompt": "Hvad gør while True typisk?",
        "code": "while True:\n    print(\"kører\")",
        "options": [
            "Gentager uendeligt indtil programmet afbrydes",
            "Kører én gang",
            "Kører kun hvis True er en variabel",
            "Giver altid syntaxfejl",
        ],
        "answer": "Gentager uendeligt indtil programmet afbrydes",
        "explanation": "Betingelsen True forbliver sand, så løkken fortsætter.",
    },
    {
        "id": 7,
        "phase": "all",
        "category": "Biblioteker",
        "prompt": "Hvad betyder import time?",
        "code": "import time\ntime.sleep(1)",
        "options": [
            "Gør funktioner fra time-biblioteket tilgængelige",
            "Starter en timer automatisk",
            "Opretter variablen time",
            "Importerer alle Python-programmer",
        ],
        "answer": "Gør funktioner fra time-biblioteket tilgængelige",
        "explanation": "import gør modulets funktioner tilgængelige, fx time.sleep().",
    },
    {
        "id": 8,
        "phase": "all",
        "category": "Kodelæsning",
        "prompt": "Hvad er værdien af a til sidst?",
        "code": "a = 1\na = a + 1\na += 1",
        "options": ["1", "2", "3", "4"],
        "answer": "3",
        "explanation": "Begge de sidste linjer øger a med 1.",
    },
    {
        "id": 9,
        "phase": "all",
        "category": "Betingelser",
        "prompt": "Hvornår udføres print-linjen?",
        "code": "if sensor < 30:\n    print(\"Tæt på\")",
        "options": [
            "Når sensor er mindre end 30",
            "Når sensor er præcis 30",
            "Når sensor er større end 30",
            "Altid",
        ],
        "answer": "Når sensor er mindre end 30",
        "explanation": "Operatoren < betyder mindre end.",
    },
    {
        "id": 10,
        "phase": "all",
        "category": "Fejlfinding",
        "prompt": "Hvorfor er indryk vigtigt i Python?",
        "code": "if True:\n    print(\"hej\")",
        "options": ["Det markerer kodeblokke", "Det gør koden hurtigere", "Det er kun kosmetisk", "Det erstatter variable"],
        "answer": "Det markerer kodeblokke",
        "explanation": "Python bruger indryk til at afgøre, hvilke linjer der hører til fx if- og loop-blokke.",
    },
    {
        "id": 11,
        "phase": "all",
        "category": "Funktioner",
        "prompt": "Hvad gør return?",
        "code": "def afstand():\n    måling = 42\n    return måling",
        "options": [
            "Sender en værdi tilbage fra funktionen",
            "Udskriver altid værdien",
            "Stopper hele Python",
            "Importerer måling",
        ],
        "answer": "Sender en værdi tilbage fra funktionen",
        "explanation": "return afslutter funktionen og giver en værdi tilbage til kaldestedet.",
    },
    {
        "id": 12,
        "phase": "all",
        "category": "Hardware",
        "prompt": "Hvad angiver Pin.OUT typisk i MicroPython?",
        "code": "LED = Pin(14, Pin.OUT)",
        "options": ["At pinnen bruges som output", "At pinnen er analog", "At LED slukkes", "At pin 14 slettes"],
        "answer": "At pinnen bruges som output",
        "explanation": "Pin.OUT konfigurerer GPIO-pinnen som udgang, fx til en LED.",
    },
]


def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    c = conn()
    c.executescript(
        """
        CREATE TABLE IF NOT EXISTS attempts(
            id INTEGER PRIMARY KEY,
            student_id TEXT,
            phase TEXT,
            score INTEGER,
            total INTEGER,
            details TEXT,
            created TEXT
        );

        CREATE TABLE IF NOT EXISTS feedback(
            id INTEGER PRIMARY KEY,
            student_id TEXT,
            escape_room INTEGER,
            wokwi INTEGER,
            confidence INTEGER,
            most_useful TEXT,
            hardest TEXT,
            comment TEXT,
            created TEXT
        );

        CREATE TABLE IF NOT EXISTS students(
            student_id TEXT PRIMARY KEY
        );

        CREATE TABLE IF NOT EXISTS background(
            student_id TEXT PRIMARY KEY,
            programmed_before TEXT,
            languages TEXT,
            experience_level TEXT,
            python_experience TEXT,
            microcontroller_experience TEXT,
            reading_confidence INTEGER,
            writing_confidence INTEGER,
            created TEXT
        );

        CREATE TABLE IF NOT EXISTS settings(
            key TEXT PRIMARY KEY,
            value TEXT
        );

        INSERT OR IGNORE INTO settings(key, value) VALUES('mid_open', '0');
        INSERT OR IGNORE INTO settings(key, value) VALUES('final_open', '0');
        """
    )

    # Standardhold: 17 ikke-systematiske elev-ID’er plus to separate testkonti.
    # INSERT OR IGNORE betyder, at eksisterende elevdata ikke overskrives.
    default_student_ids = ['T3EV', 'WHQA', 'TYPB', 'PTXJ', 'FHFB', 'YHBV', 'BR68', 'G8Z2', '3Q7U', 'XU4Q', 'B8KX', '3Q7J', 'F9A6', 'MFQ4', '6VV8', '33E3', 'N277', 'TEST01', 'TEST02']
    for student_id in default_student_ids:
        c.execute(
            "INSERT OR IGNORE INTO students(student_id) VALUES(?)",
            (student_id,),
        )

    c.commit()
    c.close()


def get_setting(key, default="0"):
    c = conn()
    row = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    c.close()
    return row["value"] if row else default


def set_setting(key, value):
    c = conn()
    c.execute(
        """
        INSERT INTO settings(key, value) VALUES(?,?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value
        """,
        (key, str(value)),
    )
    c.commit()
    c.close()


def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("role") != "student" or not session.get("student_id"):
            return redirect(url_for("index"))
        return f(*args, **kwargs)

    return decorated_function


def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Hvis en elev prøver at skrive /teacher eller /export.csv direkte,
        # sendes eleven tilbage til eget dashboard.
        if session.get("role") == "student":
            return redirect(url_for("student"))
        if session.get("role") != "teacher":
            return redirect(url_for("teacher_login"))
        return f(*args, **kwargs)

    return decorated_function


@app.before_request
def setup():
    init_db()


@app.route("/", methods=["GET", "POST"])
def index():
    error = None

    if request.method == "POST":
        sid = request.form.get("student_id", "").strip().upper()

        c = conn()
        student = c.execute(
            "SELECT student_id FROM students WHERE student_id=?",
            (sid,),
        ).fetchone()
        c.close()

        if not student:
            error = "Elev-ID findes ikke på klasselisten. Kontakt læreren."
        else:
            session.clear()
            session["role"] = "student"
            session["student_id"] = sid
            return redirect(url_for("student"))

    return render_template("index.html", error=error)


@app.route("/student")
@student_required
def student():
    sid = session["student_id"]
    c = conn()
    attempts = c.execute(
        "SELECT * FROM attempts WHERE student_id=? ORDER BY created",
        (sid,),
    ).fetchall()
    feedback_row = c.execute(
        "SELECT id FROM feedback WHERE student_id=? LIMIT 1",
        (sid,),
    ).fetchone()
    background_row = c.execute(
        "SELECT student_id FROM background WHERE student_id=? LIMIT 1",
        (sid,),
    ).fetchone()
    c.close()

    latest = {}
    for attempt in attempts:
        latest[attempt["phase"]] = attempt

    return render_template(
        "student.html",
        sid=sid,
        attempts=latest,
        feedback_done=bool(feedback_row),
        background_done=bool(background_row),
        mid_open=get_setting("mid_open") == "1",
        final_open=get_setting("final_open") == "1",
    )


@app.route("/background", methods=["GET", "POST"])
@student_required
def background():
    sid = session["student_id"]

    if request.method == "POST":
        programmed_before = request.form.get("programmed_before", "")
        languages = request.form.getlist("languages")
        other_language = request.form.get("other_language", "").strip()
        if other_language:
            languages.append(f"Andet: {other_language}")

        experience_level = request.form.get("experience_level", "")
        python_experience = request.form.get("python_experience", "")
        microcontroller_experience = request.form.get("microcontroller_experience", "")
        reading_confidence = request.form.get("reading_confidence", "")
        writing_confidence = request.form.get("writing_confidence", "")

        c = conn()
        c.execute(
            """
            INSERT INTO background(
                student_id, programmed_before, languages, experience_level,
                python_experience, microcontroller_experience,
                reading_confidence, writing_confidence, created
            ) VALUES(?,?,?,?,?,?,?,?,?)
            ON CONFLICT(student_id) DO UPDATE SET
                programmed_before=excluded.programmed_before,
                languages=excluded.languages,
                experience_level=excluded.experience_level,
                python_experience=excluded.python_experience,
                microcontroller_experience=excluded.microcontroller_experience,
                reading_confidence=excluded.reading_confidence,
                writing_confidence=excluded.writing_confidence,
                created=excluded.created
            """,
            (
                sid, programmed_before, json.dumps(languages, ensure_ascii=False),
                experience_level, python_experience, microcontroller_experience,
                reading_confidence, writing_confidence,
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        c.commit()
        c.close()
        return redirect(url_for("student"))

    c = conn()
    existing = c.execute(
        "SELECT * FROM background WHERE student_id=?",
        (sid,),
    ).fetchone()
    c.close()

    selected_languages = []
    if existing and existing["languages"]:
        try:
            selected_languages = json.loads(existing["languages"])
        except json.JSONDecodeError:
            selected_languages = []

    return render_template(
        "background.html",
        existing=existing,
        selected_languages=selected_languages,
    )


@app.route("/test/<phase>", methods=["GET", "POST"])
@student_required
def test(phase):
    if phase not in ["start", "mid", "final"]:
        return "Ukendt test", 404

    sid = session["student_id"]

    # Midtvejs- og sluttest kan kun tages, når læreren har åbnet dem.
    if phase == "mid" and get_setting("mid_open") != "1":
        return redirect(url_for("student"))
    if phase == "final" and get_setting("final_open") != "1":
        return redirect(url_for("student"))

    # Baggrundsspørgsmål skal udfyldes før starttesten.
    if phase == "start":
        c = conn()
        background_done = c.execute(
            "SELECT 1 FROM background WHERE student_id=? LIMIT 1",
            (sid,),
        ).fetchone()
        c.close()
        if not background_done:
            return redirect(url_for("background"))

    base_qs = QUESTIONS[:8] if phase == "mid" else QUESTIONS

    if request.method == "POST":
        score = 0
        details = []
        cats = {}

        for q in base_qs:
            ans = request.form.get(f'q{q["id"]}', "")
            ok = ans == q["answer"]
            score += int(ok)
            cats.setdefault(q["category"], [0, 0])
            cats[q["category"]][1] += 1
            cats[q["category"]][0] += int(ok)
            details.append(
                {
                    "id": q["id"],
                    "category": q["category"],
                    "correct": ok,
                    "answer": ans,
                }
            )

        c = conn()
        c.execute(
            """
            INSERT INTO attempts(student_id,phase,score,total,details,created)
            VALUES(?,?,?,?,?,?)
            """,
            (
                sid,
                phase,
                score,
                len(base_qs),
                json.dumps(details, ensure_ascii=False),
                datetime.now().isoformat(timespec="seconds"),
            ),
        )
        c.commit()
        c.close()

        session["last_result"] = {
            "phase": phase,
            "score": score,
            "total": len(base_qs),
            "cats": cats,
        }
        return redirect(url_for("result"))

    qs = copy.deepcopy(base_qs)
    for q in qs:
        random.shuffle(q["options"])

    return render_template("test.html", phase=phase, questions=qs)


@app.route("/result")
@student_required
def result():
    r = session.get("last_result")
    if not r:
        return redirect(url_for("student"))

    explanations = QUESTIONS[:8] if r["phase"] == "mid" else []
    return render_template("result.html", r=r, explanations=explanations)


@app.route("/feedback", methods=["GET", "POST"])
@student_required
def feedback():
    sid = session["student_id"]

    if request.method == "POST":
        vals = (
            sid,
            request.form.get("escape"),
            request.form.get("wokwi"),
            request.form.get("confidence"),
            request.form.get("most_useful"),
            request.form.get("hardest"),
            request.form.get("comment"),
            datetime.now().isoformat(timespec="seconds"),
        )
        c = conn()
        c.execute(
            """
            INSERT INTO feedback(
                student_id,escape_room,wokwi,confidence,
                most_useful,hardest,comment,created
            ) VALUES(?,?,?,?,?,?,?,?)
            """,
            vals,
        )
        c.commit()
        c.close()
        return render_template("thanks.html")

    return render_template("feedback.html")


@app.route("/teacher-entry")
def teacher_entry():
    # Et bevidst klik på Lærerlogin afslutter elevsessionen.
    session.clear()
    return redirect(url_for("teacher_login"))


@app.route("/teacher/login", methods=["GET", "POST"])
def teacher_login():
    error = None

    if request.method == "POST":
        password = request.form.get("password", "")

        if hmac.compare_digest(password, TEACHER_PASSWORD):
            session.clear()
            session["role"] = "teacher"
            return redirect(url_for("teacher"))

        error = "Forkert adgangskode."

    return render_template("teacher_login.html", error=error)


@app.route("/teacher")
@teacher_required
def teacher():
    c = conn()
    student_rows = c.execute(
        "SELECT student_id FROM students ORDER BY student_id"
    ).fetchall()
    attempt_rows = c.execute(
        "SELECT * FROM attempts ORDER BY student_id, created"
    ).fetchall()
    feedback_rows = c.execute(
        "SELECT * FROM feedback ORDER BY created DESC"
    ).fetchall()
    background_rows = c.execute(
        "SELECT * FROM background ORDER BY student_id"
    ).fetchall()
    c.close()

    students = {
        row["student_id"]: {
            "background": None,
            "start": None,
            "mid": None,
            "final": None,
            "feedback": False,
        }
        for row in student_rows
    }

    for bg in background_rows:
        sid = bg["student_id"]
        students.setdefault(
            sid,
            {"background": None, "start": None, "mid": None, "final": None, "feedback": False},
        )
        students[sid]["background"] = bg

    for attempt in attempt_rows:
        sid = attempt["student_id"]
        students.setdefault(
            sid,
            {"background": None, "start": None, "mid": None, "final": None, "feedback": False},
        )
        students[sid][attempt["phase"]] = attempt

    for fb in feedback_rows:
        sid = fb["student_id"]
        students.setdefault(
            sid,
            {"background": None, "start": None, "mid": None, "final": None, "feedback": False},
        )
        students[sid]["feedback"] = True

    return render_template(
        "teacher.html",
        students=students,
        feedback=feedback_rows,
        mid_open=get_setting("mid_open") == "1",
        final_open=get_setting("final_open") == "1",
    )


@app.route("/teacher/test-access/<phase>/<action>", methods=["POST"])
@teacher_required
def test_access(phase, action):
    if phase not in ["mid", "final"] or action not in ["open", "close"]:
        return "Ukendt handling", 404

    key = f"{phase}_open"
    set_setting(key, "1" if action == "open" else "0")
    return redirect(url_for("teacher"))


@app.route("/teacher/students", methods=["GET", "POST"])
@teacher_required
def manage_students():
    message = None

    if request.method == "POST":
        raw = request.form.get("student_ids", "")
        ids = []

        for line in raw.splitlines():
            sid = line.strip().upper()
            if sid and sid not in ids:
                ids.append(sid)

        if ids:
            c = conn()
            for sid in ids:
                c.execute(
                    "INSERT OR IGNORE INTO students(student_id) VALUES(?)",
                    (sid,),
                )
            c.commit()
            c.close()
            message = f"{len(ids)} elev-ID'er blev behandlet."

    c = conn()
    students = c.execute(
        "SELECT student_id FROM students ORDER BY student_id"
    ).fetchall()
    c.close()

    return render_template(
        "manage_students.html",
        students=students,
        message=message,
    )


@app.route("/teacher/students/delete/<student_id>", methods=["POST"])
@teacher_required
def delete_student(student_id):
    c = conn()
    has_attempts = c.execute(
        "SELECT 1 FROM attempts WHERE student_id=? LIMIT 1",
        (student_id,),
    ).fetchone()
    has_feedback = c.execute(
        "SELECT 1 FROM feedback WHERE student_id=? LIMIT 1",
        (student_id,),
    ).fetchone()

    if not has_attempts and not has_feedback:
        c.execute("DELETE FROM students WHERE student_id=?", (student_id,))
        c.commit()

    c.close()
    return redirect(url_for("manage_students"))


@app.route("/export.csv")
@teacher_required
def export_csv():
    c = conn()

    student_rows = c.execute(
        "SELECT student_id FROM students ORDER BY student_id"
    ).fetchall()

    attempt_rows = c.execute(
        """
        SELECT student_id, phase, score, total, details, created
        FROM attempts
        ORDER BY student_id, created
        """
    ).fetchall()

    feedback_rows = c.execute(
        """
        SELECT student_id, escape_room, wokwi, confidence,
               most_useful, hardest, comment, created
        FROM feedback
        ORDER BY student_id, created
        """
    ).fetchall()

    background_rows = c.execute(
        "SELECT * FROM background ORDER BY student_id"
    ).fetchall()

    c.close()

    # Seneste forsøg pr. elev og testfase.
    latest_attempt = {}
    for row in attempt_rows:
        latest_attempt[(row["student_id"], row["phase"])] = row

    # Seneste evaluering pr. elev.
    latest_feedback = {}
    for row in feedback_rows:
        latest_feedback[row["student_id"]] = row

    backgrounds = {
        row["student_id"]: row
        for row in background_rows
    }

    # Alle kompetencekategorier fra spørgebanken.
    categories = []
    for q in QUESTIONS:
        if q["category"] not in categories:
            categories.append(q["category"])

    def percent(score, total):
        if not total:
            return ""
        return round(100 * score / total, 1)

    def category_results(attempt_row):
        """
        Returnerer fx:
        {
            "Variable": "2/2 (100.0%)",
            "Loops": "1/2 (50.0%)"
        }
        """
        if not attempt_row or not attempt_row["details"]:
            return {}

        try:
            details = json.loads(attempt_row["details"])
        except (json.JSONDecodeError, TypeError):
            return {}

        counts = {}
        for item in details:
            category = item.get("category", "Ukendt")
            counts.setdefault(category, [0, 0])
            counts[category][1] += 1
            counts[category][0] += int(bool(item.get("correct")))

        result = {}
        for category, (correct, total) in counts.items():
            result[category] = (
                f"{correct}/{total} ({percent(correct, total)}%)"
            )
        return result

    s = io.StringIO()
    w = csv.writer(s)

    header = [
        "student_id",

        # Baggrund
        "programmed_before",
        "languages",
        "experience_level",
        "python_experience",
        "microcontroller_experience",
        "reading_confidence_before",
        "writing_confidence_before",

        # Samlede testresultater
        "start_score",
        "start_total",
        "start_percent",
        "start_date",

        "mid_score",
        "mid_total",
        "mid_percent",
        "mid_date",

        "final_score",
        "final_total",
        "final_percent",
        "final_date",

        "progression_percentage_points",
    ]

    # Kompetencer for hver testfase
    for phase in ["start", "mid", "final"]:
        for category in categories:
            header.append(f"{phase}_{category}")

    # Evaluering
    header.extend([
        "feedback_completed",
        "escape_room_rating",
        "wokwi_rating",
        "confidence_after",
        "most_useful",
        "hardest",
        "comment",
        "feedback_date",
    ])

    w.writerow(header)

    for student in student_rows:
        sid = student["student_id"]

        bg = backgrounds.get(sid)
        fb = latest_feedback.get(sid)

        start = latest_attempt.get((sid, "start"))
        mid = latest_attempt.get((sid, "mid"))
        final = latest_attempt.get((sid, "final"))

        start_pct = percent(start["score"], start["total"]) if start else ""
        mid_pct = percent(mid["score"], mid["total"]) if mid else ""
        final_pct = percent(final["score"], final["total"]) if final else ""

        progression = ""
        if start_pct != "" and final_pct != "":
            progression = round(final_pct - start_pct, 1)

        row = [
            sid,

            bg["programmed_before"] if bg else "",
            bg["languages"] if bg else "",
            bg["experience_level"] if bg else "",
            bg["python_experience"] if bg else "",
            bg["microcontroller_experience"] if bg else "",
            bg["reading_confidence"] if bg else "",
            bg["writing_confidence"] if bg else "",

            start["score"] if start else "",
            start["total"] if start else "",
            start_pct,
            start["created"] if start else "",

            mid["score"] if mid else "",
            mid["total"] if mid else "",
            mid_pct,
            mid["created"] if mid else "",

            final["score"] if final else "",
            final["total"] if final else "",
            final_pct,
            final["created"] if final else "",

            progression,
        ]

        phase_rows = {
            "start": start,
            "mid": mid,
            "final": final,
        }

        for phase in ["start", "mid", "final"]:
            cat_results = category_results(phase_rows[phase])
            for category in categories:
                row.append(cat_results.get(category, ""))

        row.extend([
            "ja" if fb else "nej",
            fb["escape_room"] if fb else "",
            fb["wokwi"] if fb else "",
            fb["confidence"] if fb else "",
            fb["most_useful"] if fb else "",
            fb["hardest"] if fb else "",
            fb["comment"] if fb else "",
            fb["created"] if fb else "",
        ])

        w.writerow(row)

    return Response(
        s.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
                "attachment; filename=python_test_detaljer.csv"
        },
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
