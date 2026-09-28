"""Academic domain deterministic seeder for development and testing environments.

Idempotently populates an educational hierarchy, course offerings,
student and faculty profiles, teaching assignments, enrollments, attendance records,
assignments, submissions, assessments, and marks.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
import uuid
from typing import Optional
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.academic import (
    Institution,
    Department,
    Program,
    Batch,
    Section,
    AcademicTerm,
    Course,
    StudentProfile,
    FacultyProfile,
    Enrollment,
    FacultyCourseAssignment,
    AttendanceRecord,
    Assignment,
    AssignmentSubmission,
    Assessment,
    AssessmentResult,
)


def seed_academic_data(db: Session) -> dict:
    """Seed the canonical academic foundation dataset idempotently."""

    # 1. Institution
    inst = db.query(Institution).filter(Institution.code == "AIT").first()
    if not inst:
        inst = Institution(
            id=str(uuid.uuid4()),
            name="Apex Institute of Technology",
            code="AIT",
            address="100 Innovation Boulevard, Tech City",
            contact_email="academics@apex.edu",
            is_active=True,
        )
        db.add(inst)
        db.flush()

    # 2. Departments
    dept_cse = db.query(Department).filter(
        Department.institution_id == inst.id,
        Department.code == "CSE",
    ).first()
    if not dept_cse:
        dept_cse = Department(
            id=str(uuid.uuid4()),
            institution_id=inst.id,
            name="Computer Science & Engineering",
            code="CSE",
            is_active=True,
        )
        db.add(dept_cse)

    dept_it = db.query(Department).filter(
        Department.institution_id == inst.id,
        Department.code == "IT",
    ).first()
    if not dept_it:
        dept_it = Department(
            id=str(uuid.uuid4()),
            institution_id=inst.id,
            name="Information Technology",
            code="IT",
            is_active=True,
        )
        db.add(dept_it)
    db.flush()

    # 3. Programs
    prog_btech = db.query(Program).filter(
        Program.department_id == dept_cse.id,
        Program.code == "BTECH_CSE",
    ).first()
    if not prog_btech:
        prog_btech = Program(
            id=str(uuid.uuid4()),
            department_id=dept_cse.id,
            name="Bachelor of Technology in Computer Science",
            code="BTECH_CSE",
            degree_level="UG",
            duration_years=4,
            is_active=True,
        )
        db.add(prog_btech)

    prog_mca = db.query(Program).filter(
        Program.department_id == dept_it.id,
        Program.code == "MCA",
    ).first()
    if not prog_mca:
        prog_mca = Program(
            id=str(uuid.uuid4()),
            department_id=dept_it.id,
            name="Master of Computer Applications",
            code="MCA",
            degree_level="PG",
            duration_years=2,
            is_active=True,
        )
        db.add(prog_mca)
    db.flush()

    # 4. Batches
    batch_btech = db.query(Batch).filter(
        Batch.program_id == prog_btech.id,
        Batch.name == "2024-2028",
    ).first()
    if not batch_btech:
        batch_btech = Batch(
            id=str(uuid.uuid4()),
            program_id=prog_btech.id,
            name="2024-2028",
            start_year=2024,
            end_year=2028,
            current_semester=5,
            is_active=True,
        )
        db.add(batch_btech)

    batch_mca = db.query(Batch).filter(
        Batch.program_id == prog_mca.id,
        Batch.name == "2025-2027",
    ).first()
    if not batch_mca:
        batch_mca = Batch(
            id=str(uuid.uuid4()),
            program_id=prog_mca.id,
            name="2025-2027",
            start_year=2025,
            end_year=2027,
            current_semester=3,
            is_active=True,
        )
        db.add(batch_mca)
    db.flush()

    # 5. Sections
    sec_a = db.query(Section).filter(
        Section.batch_id == batch_btech.id,
        Section.name == "Section A",
    ).first()
    if not sec_a:
        sec_a = Section(
            id=str(uuid.uuid4()),
            batch_id=batch_btech.id,
            name="Section A",
            capacity=60,
            is_active=True,
        )
        db.add(sec_a)

    sec_b = db.query(Section).filter(
        Section.batch_id == batch_btech.id,
        Section.name == "Section B",
    ).first()
    if not sec_b:
        sec_b = Section(
            id=str(uuid.uuid4()),
            batch_id=batch_btech.id,
            name="Section B",
            capacity=60,
            is_active=True,
        )
        db.add(sec_b)
    db.flush()

    # 6. Academic Terms
    term_fall2026 = db.query(AcademicTerm).filter(
        AcademicTerm.institution_id == inst.id,
        AcademicTerm.name == "Fall 2026",
    ).first()
    if not term_fall2026:
        term_fall2026 = AcademicTerm(
            id=str(uuid.uuid4()),
            institution_id=inst.id,
            name="Fall 2026",
            term_type="SEMESTER",
            start_date=date(2026, 8, 1),
            end_date=date(2026, 12, 15),
            is_current=True,
        )
        db.add(term_fall2026)
        db.flush()

    # 7. Courses
    courses_defs = [
        ("CS101", "Data Structures & Algorithms", dept_cse.id, 4, "THEORY"),
        ("CS201", "Database Management Systems", dept_cse.id, 4, "THEORY"),
        ("CS301", "Operating Systems", dept_cse.id, 3, "THEORY"),
        ("IT202", "Web Technologies", dept_it.id, 3, "LAB"),
    ]
    created_courses = {}
    for code, title, dept_id, credits_cnt, ctype in courses_defs:
        course = db.query(Course).filter(
            Course.institution_id == inst.id,
            Course.code == code,
        ).first()
        if not course:
            course = Course(
                id=str(uuid.uuid4()),
                institution_id=inst.id,
                department_id=dept_id,
                code=code,
                title=title,
                credits=credits_cnt,
                course_type=ctype,
                is_active=True,
            )
            db.add(course)
            db.flush()
        created_courses[code] = course

    # 8. User Profile Attachment (Faculty & Student)
    from app.core.security import hash_password
    from app.repositories.user_repo import UserRepository

    faculty_user = db.query(User).filter(User.email == "faculty@campuspulse.edu").first()
    if not faculty_user:
        faculty_user = UserRepository.create_user(
            db,
            email="faculty@campuspulse.edu",
            password_hash=hash_password("CampusPulse@2026!"),
            full_name="Dr. Rajesh Kumar",
            phone="+919876543210",
            is_active=True,
            is_verified=True,
        )
    UserRepository.set_user_roles(db, faculty_user.id, ["FACULTY"])

    student_user = db.query(User).filter(User.email == "student@campuspulse.edu").first()
    if not student_user:
        student_user = UserRepository.create_user(
            db,
            email="student@campuspulse.edu",
            password_hash=hash_password("CampusPulse@2026!"),
            full_name="Aarav Sharma",
            phone="+919876543211",
            is_active=True,
            is_verified=True,
        )
    UserRepository.set_user_roles(db, student_user.id, ["STUDENT"])

    admin_user = db.query(User).filter(User.email == "admin@campuspulse.edu").first()
    if not admin_user:
        admin_user = UserRepository.create_user(
            db,
            email="admin@campuspulse.edu",
            password_hash=hash_password("CampusPulse@2026!"),
            full_name="Institutional Administrator",
            phone="+919876543212",
            is_active=True,
            is_verified=True,
        )
    UserRepository.set_user_roles(db, admin_user.id, ["ADMIN"])

    faculty_prof = db.query(FacultyProfile).filter(FacultyProfile.user_id == faculty_user.id).first()
    if not faculty_prof:
        faculty_prof = FacultyProfile(
            id=str(uuid.uuid4()),
            user_id=faculty_user.id,
            employee_id="FAC-001",
            department_id=dept_cse.id,
            designation="Associate Professor",
            qualification="Ph.D. in Computer Science",
            specialization="Systems & Algorithms",
            joining_date=date(2022, 1, 10),
            is_active=True,
        )
        db.add(faculty_prof)
        db.flush()

    student_prof = db.query(StudentProfile).filter(StudentProfile.user_id == student_user.id).first()
    if not student_prof:
        student_prof = StudentProfile(
            id=str(uuid.uuid4()),
            user_id=student_user.id,
            enrollment_number="STU-2024-001",
            program_id=prog_btech.id,
            batch_id=batch_btech.id,
            section_id=sec_a.id,
            current_semester=5,
            admission_date=date(2024, 8, 1),
            academic_status="ENROLLED",
        )
        db.add(student_prof)
        db.flush()

    # 9. Faculty Course Assignments
    if faculty_prof:
        # CS101 Section A
        fa_cs101 = db.query(FacultyCourseAssignment).filter(
            FacultyCourseAssignment.faculty_id == faculty_prof.id,
            FacultyCourseAssignment.course_id == created_courses["CS101"].id,
            FacultyCourseAssignment.term_id == term_fall2026.id,
            FacultyCourseAssignment.section_id == sec_a.id,
        ).first()
        if not fa_cs101:
            fa_cs101 = FacultyCourseAssignment(
                id=str(uuid.uuid4()),
                faculty_id=faculty_prof.id,
                course_id=created_courses["CS101"].id,
                term_id=term_fall2026.id,
                section_id=sec_a.id,
                role="PRIMARY_INSTRUCTOR",
            )
            db.add(fa_cs101)

        # CS201 Course-wide (section_id=None)
        fa_cs201 = db.query(FacultyCourseAssignment).filter(
            FacultyCourseAssignment.faculty_id == faculty_prof.id,
            FacultyCourseAssignment.course_id == created_courses["CS201"].id,
            FacultyCourseAssignment.term_id == term_fall2026.id,
            FacultyCourseAssignment.section_id.is_(None),
        ).first()
        if not fa_cs201:
            fa_cs201 = FacultyCourseAssignment(
                id=str(uuid.uuid4()),
                faculty_id=faculty_prof.id,
                course_id=created_courses["CS201"].id,
                term_id=term_fall2026.id,
                section_id=None,
                role="PRIMARY_INSTRUCTOR",
            )
            db.add(fa_cs201)
        db.flush()

    # 10. Enrollments
    if student_prof:
        enr_cs101 = db.query(Enrollment).filter(
            Enrollment.student_id == student_prof.id,
            Enrollment.course_id == created_courses["CS101"].id,
            Enrollment.term_id == term_fall2026.id,
        ).first()
        if not enr_cs101:
            enr_cs101 = Enrollment(
                id=str(uuid.uuid4()),
                student_id=student_prof.id,
                course_id=created_courses["CS101"].id,
                term_id=term_fall2026.id,
                section_id=sec_a.id,
                enrollment_date=date(2026, 8, 1),
                status="ENROLLED",
            )
            db.add(enr_cs101)

        enr_cs201 = db.query(Enrollment).filter(
            Enrollment.student_id == student_prof.id,
            Enrollment.course_id == created_courses["CS201"].id,
            Enrollment.term_id == term_fall2026.id,
        ).first()
        if not enr_cs201:
            enr_cs201 = Enrollment(
                id=str(uuid.uuid4()),
                student_id=student_prof.id,
                course_id=created_courses["CS201"].id,
                term_id=term_fall2026.id,
                section_id=None,
                enrollment_date=date(2026, 8, 1),
                status="ENROLLED",
            )
            db.add(enr_cs201)
        db.flush()

    # 11. Attendance Records (CS101 for STU-2024-001)
    if student_prof and faculty_prof:
        attendance_sessions = [
            (date(2026, 8, 10), "SLOT_1", "PRESENT"),
            (date(2026, 8, 12), "SLOT_1", "PRESENT"),
            (date(2026, 8, 17), "SLOT_1", "LATE"),
            (date(2026, 8, 19), "SLOT_1", "PRESENT"),
            (date(2026, 8, 24), "SLOT_1", "ABSENT"),
            (date(2026, 8, 26), "SLOT_1", "PRESENT"),
        ]
        for sdate, slot, status in attendance_sessions:
            att = db.query(AttendanceRecord).filter(
                AttendanceRecord.student_id == student_prof.id,
                AttendanceRecord.course_id == created_courses["CS101"].id,
                AttendanceRecord.session_date == sdate,
                AttendanceRecord.session_slot == slot,
            ).first()
            if not att:
                att = AttendanceRecord(
                    id=str(uuid.uuid4()),
                    student_id=student_prof.id,
                    course_id=created_courses["CS101"].id,
                    term_id=term_fall2026.id,
                    session_date=sdate,
                    session_slot=slot,
                    status=status,
                    source="MANUAL",
                    recorded_by_faculty_id=faculty_prof.id,
                )
                db.add(att)
        db.flush()

    # 12. Assignments
    asg_cs101 = None
    if faculty_prof:
        asg_cs101 = db.query(Assignment).filter(
            Assignment.course_id == created_courses["CS101"].id,
            Assignment.term_id == term_fall2026.id,
            Assignment.title == "Binary Trees & BST Implementation",
        ).first()
        if not asg_cs101:
            asg_cs101 = Assignment(
                id=str(uuid.uuid4()),
                course_id=created_courses["CS101"].id,
                term_id=term_fall2026.id,
                section_id=sec_a.id,
                created_by_faculty_id=faculty_prof.id,
                title="Binary Trees & BST Implementation",
                description="Implement binary search tree operations, insertions, deletions, and AVL balancing.",
                max_marks=Decimal("50.00"),
                weightage_percentage=Decimal("10.00"),
                release_date=datetime(2026, 8, 15, 9, 0, 0, tzinfo=timezone.utc),
                due_date=datetime(2026, 9, 1, 23, 59, 59, tzinfo=timezone.utc),
                cutoff_date=datetime(2026, 9, 5, 23, 59, 59, tzinfo=timezone.utc),
                allow_late_submission=True,
            )
            db.add(asg_cs101)

        asg_cs201 = db.query(Assignment).filter(
            Assignment.course_id == created_courses["CS201"].id,
            Assignment.term_id == term_fall2026.id,
            Assignment.title == "Relational Normalization & SQL Queries",
        ).first()
        if not asg_cs201:
            asg_cs201 = Assignment(
                id=str(uuid.uuid4()),
                course_id=created_courses["CS201"].id,
                term_id=term_fall2026.id,
                section_id=None,
                created_by_faculty_id=faculty_prof.id,
                title="Relational Normalization & SQL Queries",
                description="Normalize schema from 1NF to BCNF and write complex multi-table analytical queries.",
                max_marks=Decimal("100.00"),
                weightage_percentage=Decimal("15.00"),
                release_date=datetime(2026, 8, 20, 9, 0, 0, tzinfo=timezone.utc),
                due_date=datetime(2026, 9, 15, 23, 59, 59, tzinfo=timezone.utc),
                allow_late_submission=True,
            )
            db.add(asg_cs201)
        db.flush()

    # 13. Submissions
    if student_prof and asg_cs101 and faculty_prof:
        sub = db.query(AssignmentSubmission).filter(
            AssignmentSubmission.assignment_id == asg_cs101.id,
            AssignmentSubmission.student_id == student_prof.id,
            AssignmentSubmission.attempt_number == 1,
        ).first()
        if not sub:
            sub = AssignmentSubmission(
                id=str(uuid.uuid4()),
                assignment_id=asg_cs101.id,
                student_id=student_prof.id,
                attempt_number=1,
                submission_content="Implementation of BST, in-order traversal, and rotation balance attached.",
                submitted_at=datetime(2026, 8, 30, 14, 30, 0, tzinfo=timezone.utc),
                status="EVALUATED",
                marks_obtained=Decimal("46.00"),
                feedback="Excellent tree traversal and balance handling. Well-structured code.",
                evaluated_by_faculty_id=faculty_prof.id,
                evaluated_at=datetime(2026, 9, 2, 11, 0, 0, tzinfo=timezone.utc),
            )
            db.add(sub)
        db.flush()

    # 14. Assessments & Results
    if faculty_prof and student_prof:
        assessment = db.query(Assessment).filter(
            Assessment.course_id == created_courses["CS101"].id,
            Assessment.term_id == term_fall2026.id,
            Assessment.title == "Midterm Examination",
        ).first()
        if not assessment:
            assessment = Assessment(
                id=str(uuid.uuid4()),
                course_id=created_courses["CS101"].id,
                term_id=term_fall2026.id,
                section_id=sec_a.id,
                created_by_faculty_id=faculty_prof.id,
                title="Midterm Examination",
                assessment_type="MIDTERM",
                max_marks=Decimal("50.00"),
                weightage_percentage=Decimal("25.00"),
                assessment_date=date(2026, 9, 10),
            )
            db.add(assessment)
            db.flush()

        result = db.query(AssessmentResult).filter(
            AssessmentResult.assessment_id == assessment.id,
            AssessmentResult.student_id == student_prof.id,
        ).first()
        if not result:
            result = AssessmentResult(
                id=str(uuid.uuid4()),
                assessment_id=assessment.id,
                student_id=student_prof.id,
                marks_obtained=Decimal("42.50"),
                is_absent=False,
                remarks="Strong analytical performance.",
                evaluated_by_faculty_id=faculty_prof.id,
                evaluated_at=datetime(2026, 9, 12, 16, 0, 0, tzinfo=timezone.utc),
            )
            db.add(result)
        db.flush()

    db.commit()

    return {
        "institution_id": inst.id,
        "department_ids": [dept_cse.id, dept_it.id],
        "course_ids": [c.id for c in created_courses.values()],
        "student_profile_id": student_prof.id if student_prof else None,
        "faculty_profile_id": faculty_prof.id if faculty_prof else None,
    }
