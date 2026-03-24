from app import app, db
from models.user import User
from models.course import Course, Semester, Subject
from models.library import Book
from models.event import Event
from models.fee import Fee
from models.attendance import Attendance, AttendanceReport
from models.exam import Exam, ExamMark
from models.notification import Notification, NotificationRecipient
from models.feedback import Feedback, Contact
from datetime import datetime, timedelta, date

def init_database():
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@college.com',
                role='admin',
                first_name='Admin',
                last_name='User',
                is_active=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
        
        # Create sample faculty user if not exists
        faculty = User.query.filter_by(username='faculty').first()
        if not faculty:
            # Check if faculty with this ID exists but is inactive
            existing_faculty = User.query.filter_by(faculty_id='FAC2024001').first()
            if existing_faculty:
                # Reactivate existing faculty
                faculty = existing_faculty
                faculty.is_active = True
                faculty.username = 'faculty'
                faculty.email = 'faculty@college.com'
                faculty.set_password('faculty123')
            else:
                # Create new faculty
                faculty = User(
                    username='faculty',
                    email='faculty@college.com',
                    role='faculty',
                    first_name='John',
                    last_name='Smith',
                    faculty_id='FAC2024002',  # Changed ID to avoid conflict
                    department='Computer Science',
                    qualification='Ph.D. Computer Science',
                    experience_years=8,
                    is_active=True
                )
                faculty.set_password('faculty123')
                db.session.add(faculty)
        
        # Create sample student user if not exists
        student = User.query.filter_by(username='student').first()
        if not student:
            # Check if student with this ID exists but is inactive
            existing_student = User.query.filter_by(student_id='STU2024001').first()
            if existing_student:
                # Reactivate existing student
                student = existing_student
                student.is_active = True
                student.username = 'student'
                student.email = 'student@college.com'
                student.set_password('student123')
            else:
                # Create new student
                student = User(
                    username='student',
                    email='student@college.com',
                    role='student',
                    first_name='Alice',
                    last_name='Johnson',
                    student_id='STU2024002',  # Changed ID to avoid conflict
                    enrollment_date=datetime.now().date(),
                    is_active=True
                )
                student.set_password('student123')
                db.session.add(student)
        
        # Create sample courses
        courses_data = [
            {
                'name': 'Bachelor of Technology',
                'code': 'BTECH',
                'duration': '4 years',
                'description': 'Bachelor of Technology in Computer Science and Engineering',
                'total_semesters': 8
            },
            {
                'name': 'Master of Computer Applications',
                'code': 'MCA',
                'duration': '2 years',
                'description': 'Master of Computer Applications',
                'total_semesters': 4
            },
            {
                'name': 'Master of Business Administration',
                'code': 'MBA',
                'duration': '2 years',
                'description': 'Master of Business Administration',
                'total_semesters': 4
            }
        ]
        
        for course_data in courses_data:
            course = Course.query.filter_by(code=course_data['code']).first()
            if not course:
                course = Course(**course_data)
                db.session.add(course)
                db.session.flush()  # Get the ID
                
                # Create semesters for each course
                for i in range(1, course.total_semesters + 1):
                    semester = Semester(
                        name=f"{i}{'st' if i == 1 else 'nd' if i == 2 else 'rd' if i == 3 else 'th'} Semester",
                        number=i,
                        course_id=course.id
                    )
                    db.session.add(semester)
        
        # Create sample subjects for BTech 1st semester
        btech_course = Course.query.filter_by(code='BTECH').first()
        if btech_course:
            btech_sem1 = Semester.query.filter_by(course_id=btech_course.id, number=1).first()
            if btech_sem1:
                subjects_data = [
                    {
                        'name': 'Computer Programming',
                        'code': 'CS101',
                        'semester_id': btech_sem1.id,
                        'faculty_id': faculty.id if faculty else None,
                        'credits': 4,
                        'description': 'Introduction to programming concepts',
                        'syllabus': 'Variables, Data Types, Control Structures, Functions, Arrays'
                    },
                    {
                        'name': 'Mathematics',
                        'code': 'MA101',
                        'semester_id': btech_sem1.id,
                        'faculty_id': faculty.id if faculty else None,
                        'credits': 3,
                        'description': 'Engineering Mathematics',
                        'syllabus': 'Calculus, Linear Algebra, Differential Equations'
                    },
                    {
                        'name': 'Physics',
                        'code': 'PH101',
                        'semester_id': btech_sem1.id,
                        'faculty_id': faculty.id if faculty else None,
                        'credits': 3,
                        'description': 'Engineering Physics',
                        'syllabus': 'Mechanics, Waves, Optics, Electricity'
                    }
                ]
                
                for subject_data in subjects_data:
                    subject = Subject.query.filter_by(code=subject_data['code']).first()
                    if not subject:
                        subject = Subject(**subject_data)
                        db.session.add(subject)
        
        # Assign student to course and semester
        if student and btech_course and btech_sem1:
            student.course_id = btech_course.id
            student.semester_id = btech_sem1.id
        
        # Create sample books
        books_data = [
            {
                'title': 'Introduction to Algorithms',
                'author': 'Thomas H. Cormen',
                'isbn': '9780262033848',
                'publisher': 'MIT Press',
                'publication_year': 2009,
                'category': 'Academic',
                'total_copies': 5,
                'available_copies': 5,
                'location': 'Shelf A1',
                'description': 'Comprehensive guide to algorithms and data structures'
            },
            {
                'title': 'Database System Concepts',
                'author': 'Abraham Silberschatz',
                'isbn': '9780073523323',
                'publisher': 'McGraw-Hill',
                'publication_year': 2010,
                'category': 'Academic',
                'total_copies': 3,
                'available_copies': 3,
                'location': 'Shelf A2',
                'description': 'Database management systems concepts'
            },
            {
                'title': 'The Art of Computer Programming',
                'author': 'Donald E. Knuth',
                'isbn': '9780201896831',
                'publisher': 'Addison-Wesley',
                'publication_year': 1997,
                'category': 'Academic',
                'total_copies': 2,
                'available_copies': 2,
                'location': 'Shelf A3',
                'description': 'Fundamental algorithms and data structures'
            }
        ]
        
        for book_data in books_data:
            book = Book.query.filter_by(isbn=book_data['isbn']).first()
            if not book:
                book = Book(**book_data)
                db.session.add(book)
        
        # Create sample events
        events_data = [
            {
                'title': 'Annual Tech Fest',
                'description': 'Annual technology festival showcasing student projects and innovations',
                'event_date': datetime.now() + timedelta(days=30),
                'venue': 'Main Auditorium',
                'organizer': 'Computer Science Department',
                'category': 'Academic',
                'is_featured': True
            },
            {
                'title': 'Sports Meet',
                'description': 'Annual sports competition between different departments',
                'event_date': datetime.now() + timedelta(days=45),
                'venue': 'Sports Complex',
                'organizer': 'Physical Education Department',
                'category': 'Sports'
            },
            {
                'title': 'Cultural Night',
                'description': 'Annual cultural program featuring music, dance, and drama',
                'event_date': datetime.now() + timedelta(days=60),
                'venue': 'Open Air Theater',
                'organizer': 'Cultural Committee',
                'category': 'Cultural'
            }
        ]
        
        for event_data in events_data:
            event = Event.query.filter_by(title=event_data['title']).first()
            if not event:
                event = Event(**event_data)
                db.session.add(event)
        
        # Create sample fees for student
        if student:
            fees_data = [
                {
                    'student_id': student.id,
                    'fee_type': 'Tuition Fee',
                    'amount': 50000.00,
                    'due_date': datetime.now() + timedelta(days=30),
                    'status': 'pending'
                },
                {
                    'student_id': student.id,
                    'fee_type': 'Library Fee',
                    'amount': 2000.00,
                    'due_date': datetime.now() + timedelta(days=15),
                    'status': 'pending'
                }
            ]
            
            for fee_data in fees_data:
                fee = Fee.query.filter_by(student_id=fee_data['student_id'], fee_type=fee_data['fee_type']).first()
                if not fee:
                    fee = Fee(**fee_data)
                    db.session.add(fee)
        
        # Create sample attendance records
        if student and faculty:
            cs101_subject = Subject.query.filter_by(code='CS101').first()
            if cs101_subject:
                # Create attendance for last 7 days
                for i in range(7):
                    attendance_date = date.today() - timedelta(days=i)
                    if attendance_date.weekday() < 5:  # Monday to Friday only
                        attendance = Attendance(
                            student_id=student.id,
                            subject_id=cs101_subject.id,
                            date=attendance_date,
                            status='present' if i % 3 != 0 else 'absent',  # Some absences
                            marked_by=faculty.id
                        )
                        db.session.add(attendance)
        
        # Create sample exams
        if faculty and cs101_subject:
            exams_data = [
                {
                    'name': 'Mid-Term Exam',
                    'subject_id': cs101_subject.id,
                    'exam_type': 'mid-term',
                    'total_marks': 50,
                    'date': date.today() + timedelta(days=14),
                    'duration': 120,
                    'description': 'Mid-term examination covering first half of the syllabus'
                },
                {
                    'name': 'Final Exam',
                    'subject_id': cs101_subject.id,
                    'exam_type': 'final',
                    'total_marks': 100,
                    'date': date.today() + timedelta(days=60),
                    'duration': 180,
                    'description': 'Final examination covering the entire syllabus'
                }
            ]
            
            for exam_data in exams_data:
                exam = Exam.query.filter_by(name=exam_data['name'], subject_id=exam_data['subject_id']).first()
                if not exam:
                    exam = Exam(**exam_data)
                    db.session.add(exam)
                    db.session.flush()
                    
                    # Add sample marks for the first exam
                    if exam.exam_type == 'mid-term' and student:
                        mark = ExamMark(
                            exam_id=exam.id,
                            student_id=student.id,
                            marks_obtained=42.5,
                            remarks='Good understanding of basic concepts',
                            graded_by=faculty.id
                        )
                        db.session.add(mark)
        
        # Create sample notifications
        if admin:
            notifications_data = [
                {
                    'title': 'Welcome to New Academic Year',
                    'message': 'Welcome all students to the new academic year 2024-25. We wish you all the best for your studies.',
                    'type': 'announcement',
                    'priority': 'normal',
                    'target_role': 'all',
                    'created_by': admin.id
                },
                {
                    'title': 'Mid-Term Examinations Schedule',
                    'message': 'Mid-term examinations will be held from next week. Please check your respective subject schedules.',
                    'type': 'notification',
                    'priority': 'high',
                    'target_role': 'student',
                    'created_by': admin.id
                },
                {
                    'title': 'Faculty Meeting',
                    'message': 'All faculty members are requested to attend the monthly meeting on Friday at 3 PM.',
                    'type': 'notification',
                    'priority': 'normal',
                    'target_role': 'faculty',
                    'created_by': admin.id
                }
            ]
            
            for notif_data in notifications_data:
                notification = Notification.query.filter_by(title=notif_data['title']).first()
                if not notification:
                    notification = Notification(**notif_data)
                    db.session.add(notification)
        
        # Create sample feedback
        if student:
            feedback_data = [
                {
                    'subject': 'Library Services Improvement',
                    'message': 'The library could benefit from more study spaces and extended hours during exam periods.',
                    'feedback_type': 'suggestion',
                    'priority': 'normal',
                    'submitted_by': student.id,
                    'status': 'pending'
                }
            ]
            
            for feedback_item in feedback_data:
                feedback = Feedback.query.filter_by(subject=feedback_item['subject']).first()
                if not feedback:
                    feedback = Feedback(**feedback_item)
                    db.session.add(feedback)
        
        # Commit all changes
        db.session.commit()
        print("Database initialized successfully!")
        print("Admin credentials: username=admin, password=admin123")
        print("Faculty credentials: username=faculty, password=faculty123")
        print("Student credentials: username=student, password=student123")

if __name__ == '__main__':
    init_database() 