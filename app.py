from flask import Flask, render_template, request, redirect, url_for, session, Response
import sqlite3, json, csv, io, os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-this-in-production')
DB = 'python_test.db'

QUESTIONS = [
 {'id':1,'phase':'all','category':'Variable','prompt':'Hvad skriver koden?','code':'a = 2026\nb = 3\nc = a + b\nprint(c)','options':['2023','2026','2029','Fejl'],'answer':'2029','explanation':'c bliver summen af a og b: 2026 + 3 = 2029.'},
 {'id':2,'phase':'all','category':'Variable','prompt':'Hvad er formålet med en variabel?','code':'','options':['At gemme en værdi','At gentage kode','At importere et bibliotek','At stoppe programmet'],'answer':'At gemme en værdi','explanation':'En variabel binder et navn til en værdi, som programmet kan bruge og ændre.'},
 {'id':3,'phase':'all','category':'Loops','prompt':'Hvilke tal udskrives?','code':'for i in range(0, 4):\n    print(i)','options':['0, 1, 2, 3','0, 1, 2, 3, 4','1, 2, 3, 4','4'],'answer':'0, 1, 2, 3','explanation':'Slutværdien i range er ikke inkluderet.'},
 {'id':4,'phase':'all','category':'Betingelser','prompt':'Hvad udskrives?','code':'afstand = 25\nif afstand < 20:\n    print("STOP")\nelse:\n    print("OK")','options':['STOP','OK','25','Fejl'],'answer':'OK','explanation':'25 er ikke mindre end 20, så else-grenen udføres.'},
 {'id':5,'phase':'all','category':'Fejlfinding','prompt':'Hvilken ændring retter koden?','code':'if a == 10\n    print("a er lig med 10")','options':['Tilføj : efter 10','Skift == til =','Fjern indryk','Skift if til for'],'answer':'Tilføj : efter 10','explanation':'En if-sætning afsluttes med kolon før den indrykkede blok.'},
 {'id':6,'phase':'all','category':'Loops','prompt':'Hvad gør while True typisk?','code':'while True:\n    print("kører")','options':['Gentager uendeligt indtil programmet afbrydes','Kører én gang','Kører kun hvis True er en variabel','Giver altid syntaxfejl'],'answer':'Gentager uendeligt indtil programmet afbrydes','explanation':'Betingelsen True forbliver sand, så løkken fortsætter.'},
 {'id':7,'phase':'all','category':'Biblioteker','prompt':'Hvad betyder import time?','code':'import time\ntime.sleep(1)','options':['Gør funktioner fra time-biblioteket tilgængelige','Starter en timer automatisk','Opretter variablen time','Importerer alle Python-programmer'],'answer':'Gør funktioner fra time-biblioteket tilgængelige','explanation':'import gør modulets funktioner tilgængelige, fx time.sleep().' },
 {'id':8,'phase':'all','category':'Kodelæsning','prompt':'Hvad er værdien af a til sidst?','code':'a = 1\na = a + 1\na += 1','options':['1','2','3','4'],'answer':'3','explanation':'Begge de sidste linjer øger a med 1.'},
 {'id':9,'phase':'all','category':'Betingelser','prompt':'Hvornår udføres print-linjen?','code':'if sensor < 30:\n    print("Tæt på")','options':['Når sensor er mindre end 30','Når sensor er præcis 30','Når sensor er større end 30','Altid'],'answer':'Når sensor er mindre end 30','explanation':'Operatoren < betyder mindre end.'},
 {'id':10,'phase':'all','category':'Fejlfinding','prompt':'Hvorfor er indryk vigtigt i Python?','code':'if True:\n    print("hej")','options':['Det markerer kodeblokke','Det gør koden hurtigere','Det er kun kosmetisk','Det erstatter variable'],'answer':'Det markerer kodeblokke','explanation':'Python bruger indryk til at afgøre, hvilke linjer der hører til fx if- og loop-blokke.'},
 {'id':11,'phase':'all','category':'Funktioner','prompt':'Hvad gør return?','code':'def afstand():\n    måling = 42\n    return måling','options':['Sender en værdi tilbage fra funktionen','Udskriver altid værdien','Stopper hele Python','Importerer måling'],'answer':'Sender en værdi tilbage fra funktionen','explanation':'return afslutter funktionen og giver en værdi tilbage til kaldestedet.'},
 {'id':12,'phase':'all','category':'Hardware','prompt':'Hvad angiver Pin.OUT typisk i MicroPython?','code':'LED = Pin(14, Pin.OUT)','options':['At pinnen bruges som output','At pinnen er analog','At LED slukkes','At pin 14 slettes'],'answer':'At pinnen bruges som output','explanation':'Pin.OUT konfigurerer GPIO-pinnen som udgang, fx til en LED.'},
]

def conn():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def init_db():
    c=conn()
    c.executescript('''
    CREATE TABLE IF NOT EXISTS attempts(id INTEGER PRIMARY KEY, student_id TEXT, phase TEXT, score INTEGER, total INTEGER, details TEXT, created TEXT);
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
    '''); c.commit(); c.close()

@app.before_request
def setup(): init_db()

@app.route('/', methods=['GET','POST'])
def index():
    if request.method=='POST':
        sid=request.form.get('student_id','').strip()
        if sid: session['student_id']=sid; return redirect(url_for('student'))
    return render_template('index.html')

@app.route('/student')
def student():
    sid=session.get('student_id')
    if not sid:return redirect(url_for('index'))
    c=conn(); attempts=c.execute('SELECT * FROM attempts WHERE student_id=? ORDER BY created',(sid,)).fetchall(); c.close()
    return render_template('student.html', sid=sid, attempts=attempts)

@app.route('/test/<phase>', methods=['GET','POST'])
def test(phase):
    if phase not in ['start','mid','final']: return 'Ukendt test',404
    sid=session.get('student_id');
    if not sid:return redirect(url_for('index'))
    qs=QUESTIONS[:8] if phase=='mid' else QUESTIONS
    if request.method=='POST':
        score=0; details=[]; cats={}
        for q in qs:
            ans=request.form.get(f'q{q["id"]}','')
            ok=ans==q['answer']; score += int(ok)
            cats.setdefault(q['category'],[0,0]); cats[q['category']][1]+=1; cats[q['category']][0]+=int(ok)
            details.append({'id':q['id'],'category':q['category'],'correct':ok,'answer':ans})
        c=conn(); c.execute('INSERT INTO attempts(student_id,phase,score,total,details,created) VALUES(?,?,?,?,?,?)',(sid,phase,score,len(qs),json.dumps(details),datetime.now().isoformat(timespec='seconds'))); c.commit(); c.close()
        session['last_result']={'phase':phase,'score':score,'total':len(qs),'cats':cats}
        return redirect(url_for('result'))
    return render_template('test.html', phase=phase, questions=qs)

@app.route('/result')
def result():
    r=session.get('last_result');
    if not r:return redirect(url_for('student'))
    # No item-level answers for start/final. Midway may show explanations after submission.
    explanations = QUESTIONS[:8] if r['phase']=='mid' else []
    return render_template('result.html', r=r, explanations=explanations)

@app.route('/feedback', methods=['GET','POST'])
def feedback():
    sid=session.get('student_id');
    if not sid:return redirect(url_for('index'))
    if request.method=='POST':
        vals=(sid,request.form.get('escape'),request.form.get('wokwi'),request.form.get('confidence'),request.form.get('most_useful'),request.form.get('hardest'),request.form.get('comment'),datetime.now().isoformat(timespec='seconds'))
        c=conn(); c.execute(
    'INSERT INTO feedback(student_id,escape_room,wokwi,confidence,most_useful,hardest,comment,created) VALUES(?,?,?,?,?,?,?,?)',
    vals
); c.commit(); c.close()
        return render_template('thanks.html')
    return render_template('feedback.html')

@app.route('/teacher')
def teacher():
    c=conn(); rows=c.execute('SELECT * FROM attempts ORDER BY student_id, created').fetchall(); fb=c.execute('SELECT * FROM feedback ORDER BY created DESC').fetchall(); c.close()
    students={}
    for x in rows: students.setdefault(x['student_id'],{})[x['phase']]=x
    return render_template('teacher.html', students=students, feedback=fb)

@app.route('/export.csv')
def export_csv():
    c=conn(); rows=c.execute('SELECT student_id,phase,score,total,created FROM attempts ORDER BY student_id,created').fetchall(); c.close()
    s=io.StringIO(); w=csv.writer(s); w.writerow(['student_id','phase','score','total','percent','created'])
    for r in rows:w.writerow([r['student_id'],r['phase'],r['score'],r['total'],round(100*r['score']/r['total'],1),r['created']])
    return Response(s.getvalue(),mimetype='text/csv',headers={'Content-Disposition':'attachment; filename=python_test_results.csv'})

if __name__=='__main__':
    init_db(); app.run(debug=True)
