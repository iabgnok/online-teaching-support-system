from models import db, Users, Student
from app import app

with app.app_context():
    students = Users.query.filter_by(role='student').all()
    print('Total students:', len(students))
    for u in students:
        print(f'User {u.user_id}: {u.username}, profile: {u.student_profile}')