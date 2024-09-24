import sqlite3
import xml.etree.ElementTree as ET

tree = ET.parse('plan_do_librusa.xml')  
root = tree.getroot()
conn = sqlite3.connect('plan_lekcji10.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS periods (
                    periodid INTEGER PRIMARY KEY AUTOINCREMENT,
                    period TEXT, name TEXT, short TEXT, starttime TEXT, endtime TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS subjects (
                    subjectid TEXT PRIMARY KEY, name TEXT, short TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS teachers (
                    teacherid TEXT PRIMARY KEY, firstname TEXT, lastname TEXT, short TEXT, gender TEXT, color TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS classrooms (
                    classroomid TEXT PRIMARY KEY, name TEXT, short TEXT, capacity TEXT)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS classes (
                    classid TEXT PRIMARY KEY, name TEXT, short TEXT, teacherid TEXT, classroomids TEXT, grade TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS groups (
                    groupid TEXT PRIMARY KEY, name TEXT, classid TEXT, entireclass TEXT, divisiontag TEXT, studentcount TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS lessons (
                    lessonid TEXT PRIMARY KEY, classid TEXT, subjectid TEXT, teacherid TEXT, 
                    classroomid TEXT, groupid TEXT, periodspercard INTEGER, periodsperweek REAL, 
                    daysdefid TEXT, weeksdefid TEXT, termsdefid TEXT, seminargroup TEXT, capacity TEXT)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS days (
                    dayid TEXT PRIMARY KEY, name TEXT, short TEXT, binary TEXT)''')

cursor.execute('''CREATE TABLE IF NOT EXISTS cards (
                    cardid INTEGER PRIMARY KEY AUTOINCREMENT,
                    lessonid TEXT, classroomids TEXT, period INTEGER, 
                    days TEXT, weeks TEXT, terms TEXT)''')

for period in root.find('periods'):
    print(f"Inserting period: {period.get('period')}")  
    cursor.execute('INSERT INTO periods (period, name, short, starttime, endtime) VALUES (?, ?, ?, ?, ?)', 
                   (period.get('period'), period.get('name'), period.get('short'), period.get('starttime'), period.get('endtime')))

# Subjects
for subject in root.find('subjects'):
    print(f"Inserting subject: {subject.get('name')}")
    cursor.execute('INSERT INTO subjects (subjectid, name, short) VALUES (?, ?, ?)', 
                   (subject.get('id'), subject.get('name'), subject.get('short')))
# Teachers
for teacher in root.find('teachers'):
    print(f"Inserting teacher: {teacher.get('firstname')} {teacher.get('lastname')}") 
    cursor.execute('INSERT INTO teachers (teacherid, firstname, lastname, short, gender, color) VALUES (?, ?, ?, ?, ?, ?)', 
                   (teacher.get('id'), teacher.get('firstname'), teacher.get('lastname'), teacher.get('short'), teacher.get('gender'), teacher.get('color')))
# Classrooms
for classroom in root.find('classrooms'):
    print(f"Inserting classroom: {classroom.get('name')}")  
    cursor.execute('INSERT INTO classrooms (classroomid, name, short, capacity) VALUES (?, ?, ?, ?)', 
                   (classroom.get('id'), classroom.get('name'), classroom.get('short'), classroom.get('capacity')))
# Classes
for class_ in root.find('classes'):
    print(f"Inserting class: {class_.get('name')}")  
    cursor.execute('INSERT INTO classes (classid, name, short, teacherid, classroomids, grade) VALUES (?, ?, ?, ?, ?, ?)', 
                   (class_.get('id'), class_.get('name'), class_.get('short'), class_.get('teacherid'), class_.get('classroomids'), class_.get('grade')))
# Groups
for group in root.find('groups'):
    print(f"Inserting group: {group.get('name')}")  
    cursor.execute('INSERT INTO groups (groupid, name, classid, entireclass, divisiontag, studentcount) VALUES (?, ?, ?, ?, ?, ?)', 
                   (group.get('id'), group.get('name'), group.get('classid'), group.get('entireclass'), group.get('divisiontag'), group.get('studentcount')))

# Days (dni tyg)
for day in root.find('daysdefs'):
    print(f"Inserting day: {day.get('name')}")  
    cursor.execute('INSERT INTO days (dayid, name, short, binary) VALUES (?, ?, ?, ?)', 
                   (day.get('id'), day.get('name'), day.get('short'), day.get('days')))

# Lessons 
for lesson in root.find('lessons'):
    print(f"Inserting lesson: {lesson.get('id')}")  
    cursor.execute('INSERT INTO lessons (lessonid, classid, subjectid, teacherid, classroomid, groupid, periodspercard, periodsperweek, daysdefid, weeksdefid, termsdefid, seminargroup, capacity) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', 
                   (lesson.get('id'), lesson.get('classids'), lesson.get('subjectid'), lesson.get('teacherids'), 
                    lesson.get('classroomids'), lesson.get('groupids'), int(lesson.get('periodspercard')), 
                    float(lesson.get('periodsperweek')), lesson.get('daysdefid'), lesson.get('weeksdefid'), 
                    lesson.get('termsdefid'), lesson.get('seminargroup'), lesson.get('capacity')))

for card in root.find('cards'):
    print(f"Inserting card with lessonid: {card.get('lessonid')}, period: {card.get('period')}") 
    cursor.execute('INSERT INTO cards (lessonid, classroomids, period, days, weeks, terms) VALUES (?, ?, ?, ?, ?, ?)', 
                   (card.get('lessonid'), card.get('classroomids'), int(card.get('period')), 
                    card.get('days'), card.get('weeks'), card.get('terms')))
conn.commit()
conn.close()
print("Dane zostały pomyślnie przeniesione do bazy SQLite!")
