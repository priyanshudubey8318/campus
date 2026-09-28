"""Academic domain repository handling data access for institutions, profiles,
enrollments, teaching assignments, attendance, coursework, and assessments.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Any
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.academic import (
    AcademicTerm,
    Assessment,
    AssessmentResult,
    Assignment,
    AssignmentSubmission,
    AttendanceRecord,
    Batch,
    Course,
    Department,
    Enrollment,
    FacultyCourseAssignment,
    FacultyProfile,
    Institution,
    Program,
    Section,
    StudentProfile,
)


class AcademicRepository:
    """Centralized database access methods for academic domain entities."""

    # -------------------------------------------------------------------------
    # Institutional Hierarchy
    # -------------------------------------------------------------------------

    @staticmethod
    def get_institutions(db: Session) -> List[Institution]:
        return db.query(Institution).filter(Institution.is_active == True).all()

    @staticmethod
    def get_institution_by_id(db: Session, institution_id: str) -> Optional[Institution]:
        return db.query(Institution).filter(Institution.id == institution_id).first()

    @staticmethod
    def get_departments(db: Session, institution_id: Optional[str] = None) -> List[Department]:
        query = db.query(Department).filter(Department.is_active == True)
        if institution_id:
            query = query.filter(Department.institution_id == institution_id)
        return query.all()

    @staticmethod
    def get_department_by_id(db: Session, department_id: str) -> Optional[Department]:
        return db.query(Department).filter(Department.id == department_id).first()

    @staticmethod
    def get_programs(db: Session, department_id: Optional[str] = None) -> List[Program]:
        query = db.query(Program).filter(Program.is_active == True)
        if department_id:
            query = query.filter(Program.department_id == department_id)
        return query.all()

    @staticmethod
    def get_program_by_id(db: Session, program_id: str) -> Optional[Program]:
        return db.query(Program).filter(Program.id == program_id).first()

    @staticmethod
    def get_batches(db: Session, program_id: Optional[str] = None) -> List[Batch]:
        query = db.query(Batch).filter(Batch.is_active == True)
        if program_id:
            query = query.filter(Batch.program_id == program_id)
        return query.all()

    @staticmethod
    def get_batch_by_id(db: Session, batch_id: str) -> Optional[Batch]:
        return db.query(Batch).filter(Batch.id == batch_id).first()

    @staticmethod
    def get_sections(db: Session, batch_id: Optional[str] = None) -> List[Section]:
        query = db.query(Section).filter(Section.is_active == True)
        if batch_id:
            query = query.filter(Section.batch_id == batch_id)
        return query.all()

    @staticmethod
    def get_section_by_id(db: Session, section_id: str) -> Optional[Section]:
        return db.query(Section).filter(Section.id == section_id).first()

    @staticmethod
    def get_terms(db: Session, institution_id: Optional[str] = None) -> List[AcademicTerm]:
        query = db.query(AcademicTerm)
        if institution_id:
            query = query.filter(AcademicTerm.institution_id == institution_id)
        return query.order_by(AcademicTerm.start_date.desc()).all()

    @staticmethod
    def get_current_term(db: Session, institution_id: Optional[str] = None) -> Optional[AcademicTerm]:
        query = db.query(AcademicTerm).filter(AcademicTerm.is_current == True)
        if institution_id:
            query = query.filter(AcademicTerm.institution_id == institution_id)
        return query.first()

    @staticmethod
    def get_term_by_id(db: Session, term_id: str) -> Optional[AcademicTerm]:
        return db.query(AcademicTerm).filter(AcademicTerm.id == term_id).first()

    @staticmethod
    def get_courses(
        db: Session,
        institution_id: Optional[str] = None,
        department_id: Optional[str] = None,
    ) -> List[Course]:
        query = db.query(Course).filter(Course.is_active == True)
        if institution_id:
            query = query.filter(Course.institution_id == institution_id)
        if department_id:
            query = query.filter(Course.department_id == department_id)
        return query.all()

    @staticmethod
    def get_course_by_id(db: Session, course_id: str) -> Optional[Course]:
        return db.query(Course).filter(Course.id == course_id).first()

    # -------------------------------------------------------------------------
    # Profiles
    # -------------------------------------------------------------------------

    @staticmethod
    def get_student_profile_by_user_id(db: Session, user_id: str) -> Optional[StudentProfile]:
        return (
            db.query(StudentProfile)
            .options(
                joinedload(StudentProfile.program),
                joinedload(StudentProfile.batch),
                joinedload(StudentProfile.section),
                joinedload(StudentProfile.user),
            )
            .filter(StudentProfile.user_id == user_id)
            .first()
        )

    @staticmethod
    def get_student_profile_by_id(db: Session, profile_id: str) -> Optional[StudentProfile]:
        return (
            db.query(StudentProfile)
            .options(
                joinedload(StudentProfile.program),
                joinedload(StudentProfile.batch),
                joinedload(StudentProfile.section),
                joinedload(StudentProfile.user),
            )
            .filter(StudentProfile.id == profile_id)
            .first()
        )

    @staticmethod
    def get_student_profile_by_enrollment_number(db: Session, enr_no: str) -> Optional[StudentProfile]:
        return (
            db.query(StudentProfile)
            .filter(StudentProfile.enrollment_number == enr_no.strip())
            .first()
        )

    @staticmethod
    def create_student_profile(
        db: Session,
        user_id: str,
        enrollment_number: str,
        program_id: str,
        batch_id: str,
        section_id: Optional[str] = None,
        current_semester: int = 1,
        admission_date: Optional[date] = None,
        academic_status: str = "ENROLLED",
    ) -> StudentProfile:
        profile = StudentProfile(
            id=str(uuid.uuid4()),
            user_id=user_id,
            enrollment_number=enrollment_number.strip(),
            program_id=program_id,
            batch_id=batch_id,
            section_id=section_id,
            current_semester=current_semester,
            admission_date=admission_date or date.today(),
            academic_status=academic_status,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def get_faculty_profile_by_user_id(db: Session, user_id: str) -> Optional[FacultyProfile]:
        return (
            db.query(FacultyProfile)
            .options(
                joinedload(FacultyProfile.department),
                joinedload(FacultyProfile.user),
            )
            .filter(FacultyProfile.user_id == user_id)
            .first()
        )

    @staticmethod
    def get_faculty_profile_by_id(db: Session, profile_id: str) -> Optional[FacultyProfile]:
        return (
            db.query(FacultyProfile)
            .options(
                joinedload(FacultyProfile.department),
                joinedload(FacultyProfile.user),
            )
            .filter(FacultyProfile.id == profile_id)
            .first()
        )

    @staticmethod
    def get_faculty_profile_by_employee_id(db: Session, emp_id: str) -> Optional[FacultyProfile]:
        return db.query(FacultyProfile).filter(FacultyProfile.employee_id == emp_id.strip()).first()

    @staticmethod
    def create_faculty_profile(
        db: Session,
        user_id: str,
        employee_id: str,
        department_id: str,
        designation: str,
        qualification: Optional[str] = None,
        specialization: Optional[str] = None,
        joining_date: Optional[date] = None,
        is_active: bool = True,
    ) -> FacultyProfile:
        profile = FacultyProfile(
            id=str(uuid.uuid4()),
            user_id=user_id,
            employee_id=employee_id.strip(),
            department_id=department_id,
            designation=designation.strip(),
            qualification=qualification.strip() if qualification else None,
            specialization=specialization.strip() if specialization else None,
            joining_date=joining_date or date.today(),
            is_active=is_active,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    # -------------------------------------------------------------------------
    # Teaching Assignments & Scoping
    # -------------------------------------------------------------------------

    @staticmethod
    def get_faculty_assignments(
        db: Session,
        faculty_id: Optional[str] = None,
        course_id: Optional[str] = None,
        term_id: Optional[str] = None,
    ) -> List[FacultyCourseAssignment]:
        query = (
            db.query(FacultyCourseAssignment)
            .options(
                joinedload(FacultyCourseAssignment.course),
                joinedload(FacultyCourseAssignment.term),
                joinedload(FacultyCourseAssignment.section),
            )
        )
        if faculty_id:
            query = query.filter(FacultyCourseAssignment.faculty_id == faculty_id)
        if course_id:
            query = query.filter(FacultyCourseAssignment.course_id == course_id)
        if term_id:
            query = query.filter(FacultyCourseAssignment.term_id == term_id)
        return query.all()

    @staticmethod
    def is_faculty_assigned_to_course(
        db: Session,
        faculty_id: str,
        course_id: str,
        term_id: Optional[str] = None,
        section_id: Optional[str] = None,
    ) -> bool:
        """Verify whether a faculty member is assigned to a course/section in a given term."""
        query = db.query(FacultyCourseAssignment).filter(
            FacultyCourseAssignment.faculty_id == faculty_id,
            FacultyCourseAssignment.course_id == course_id,
        )
        if term_id:
            query = query.filter(FacultyCourseAssignment.term_id == term_id)
        if section_id:
            # Matches if assigned specifically to that section OR assigned course-wide (section_id IS NULL)
            query = query.filter(
                (FacultyCourseAssignment.section_id == section_id)
                | (FacultyCourseAssignment.section_id.is_(None))
            )
        return query.first() is not None

    # -------------------------------------------------------------------------
    # Enrollments
    # -------------------------------------------------------------------------

    @staticmethod
    def get_enrollments(
        db: Session,
        student_id: Optional[str] = None,
        course_id: Optional[str] = None,
        term_id: Optional[str] = None,
    ) -> List[Enrollment]:
        query = (
            db.query(Enrollment)
            .options(
                joinedload(Enrollment.course),
                joinedload(Enrollment.term),
                joinedload(Enrollment.section),
                joinedload(Enrollment.student).joinedload(StudentProfile.user),
            )
        )
        if student_id:
            query = query.filter(Enrollment.student_id == student_id)
        if course_id:
            query = query.filter(Enrollment.course_id == course_id)
        if term_id:
            query = query.filter(Enrollment.term_id == term_id)
        return query.all()

    @staticmethod
    def is_student_enrolled_in_course(
        db: Session,
        student_id: str,
        course_id: str,
        term_id: Optional[str] = None,
    ) -> bool:
        query = db.query(Enrollment).filter(
            Enrollment.student_id == student_id,
            Enrollment.course_id == course_id,
            Enrollment.status.in_(["ENROLLED", "AUDITING"]),
        )
        if term_id:
            query = query.filter(Enrollment.term_id == term_id)
        return query.first() is not None

    @staticmethod
    def create_enrollment(
        db: Session,
        student_id: str,
        course_id: str,
        term_id: str,
        section_id: Optional[str] = None,
        enrollment_date: Optional[date] = None,
        status: str = "ENROLLED",
    ) -> Enrollment:
        enrollment = Enrollment(
            id=str(uuid.uuid4()),
            student_id=student_id,
            course_id=course_id,
            term_id=term_id,
            section_id=section_id,
            enrollment_date=enrollment_date or date.today(),
            status=status,
        )
        db.add(enrollment)
        db.commit()
        db.refresh(enrollment)
        return enrollment

    # -------------------------------------------------------------------------
    # Attendance Records
    # -------------------------------------------------------------------------

    @staticmethod
    def get_attendance_records(
        db: Session,
        student_id: Optional[str] = None,
        course_id: Optional[str] = None,
        term_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[AttendanceRecord]:
        query = (
            db.query(AttendanceRecord)
            .options(
                joinedload(AttendanceRecord.course),
                joinedload(AttendanceRecord.student).joinedload(StudentProfile.user),
            )
            .order_by(AttendanceRecord.session_date.desc())
        )
        if student_id:
            query = query.filter(AttendanceRecord.student_id == student_id)
        if course_id:
            query = query.filter(AttendanceRecord.course_id == course_id)
        if term_id:
            query = query.filter(AttendanceRecord.term_id == term_id)
        if start_date:
            query = query.filter(AttendanceRecord.session_date >= start_date)
        if end_date:
            query = query.filter(AttendanceRecord.session_date <= end_date)
        return query.all()

    @staticmethod
    def create_attendance_record(
        db: Session,
        student_id: str,
        course_id: str,
        term_id: str,
        session_date: date,
        session_slot: str,
        status: str,
        source: str = "MANUAL",
        recorded_by_faculty_id: Optional[str] = None,
        remarks: Optional[str] = None,
    ) -> AttendanceRecord:
        record = AttendanceRecord(
            id=str(uuid.uuid4()),
            student_id=student_id,
            course_id=course_id,
            term_id=term_id,
            session_date=session_date,
            session_slot=session_slot.strip(),
            status=status.upper().strip(),
            source=source.upper().strip(),
            recorded_by_faculty_id=recorded_by_faculty_id,
            remarks=remarks.strip() if remarks else None,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    @staticmethod
    def calculate_student_attendance_summary(
        db: Session,
        student_id: str,
        course_id: Optional[str] = None,
        term_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Derive attendance totals and percentages on demand from raw session events."""
        query = db.query(AttendanceRecord).filter(AttendanceRecord.student_id == student_id)
        if course_id:
            query = query.filter(AttendanceRecord.course_id == course_id)
        if term_id:
            query = query.filter(AttendanceRecord.term_id == term_id)

        records = query.all()
        total = len(records)
        if total == 0:
            return {
                "total_sessions": 0,
                "present_count": 0,
                "absent_count": 0,
                "late_count": 0,
                "excused_count": 0,
                "attendance_percentage": 100.0,
            }

        present = sum(1 for r in records if r.status == "PRESENT")
        late = sum(1 for r in records if r.status == "LATE")
        absent = sum(1 for r in records if r.status == "ABSENT")
        excused = sum(1 for r in records if r.status == "EXCUSED")

        # In standard academic rules: Present = 1.0, Late = 0.5 (or counted present), Excused removed from denominator or credited
        # Standard conservative: (present + late) / total * 100
        attendance_pct = round(((present + late) / total) * 100.0, 2)

        return {
            "total_sessions": total,
            "present_count": present,
            "absent_count": absent,
            "late_count": late,
            "excused_count": excused,
            "attendance_percentage": attendance_pct,
        }

    # -------------------------------------------------------------------------
    # Coursework & Submissions
    # -------------------------------------------------------------------------

    @staticmethod
    def get_assignments(
        db: Session,
        course_id: Optional[str] = None,
        term_id: Optional[str] = None,
        section_id: Optional[str] = None,
    ) -> List[Assignment]:
        query = (
            db.query(Assignment)
            .options(
                joinedload(Assignment.course),
                joinedload(Assignment.term),
                joinedload(Assignment.created_by).joinedload(FacultyProfile.user),
            )
            .order_by(Assignment.due_date.asc())
        )
        if course_id:
            query = query.filter(Assignment.course_id == course_id)
        if term_id:
            query = query.filter(Assignment.term_id == term_id)
        if section_id:
            query = query.filter(
                (Assignment.section_id == section_id) | (Assignment.section_id.is_(None))
            )
        return query.all()

    @staticmethod
    def get_assignment_by_id(db: Session, assignment_id: str) -> Optional[Assignment]:
        return (
            db.query(Assignment)
            .options(
                joinedload(Assignment.course),
                joinedload(Assignment.term),
                joinedload(Assignment.created_by),
            )
            .filter(Assignment.id == assignment_id)
            .first()
        )

    @staticmethod
    def create_assignment(
        db: Session,
        course_id: str,
        term_id: str,
        created_by_faculty_id: str,
        title: str,
        description: Optional[str],
        max_marks: Decimal,
        weightage_percentage: Decimal,
        release_date: datetime,
        due_date: datetime,
        cutoff_date: Optional[datetime] = None,
        section_id: Optional[str] = None,
        allow_late_submission: bool = True,
    ) -> Assignment:
        asg = Assignment(
            id=str(uuid.uuid4()),
            course_id=course_id,
            term_id=term_id,
            section_id=section_id,
            created_by_faculty_id=created_by_faculty_id,
            title=title.strip(),
            description=description.strip() if description else None,
            max_marks=max_marks,
            weightage_percentage=weightage_percentage,
            release_date=release_date,
            due_date=due_date,
            cutoff_date=cutoff_date,
            allow_late_submission=allow_late_submission,
        )
        db.add(asg)
        db.commit()
        db.refresh(asg)
        return asg

    @staticmethod
    def get_submissions(
        db: Session,
        assignment_id: Optional[str] = None,
        student_id: Optional[str] = None,
    ) -> List[AssignmentSubmission]:
        query = (
            db.query(AssignmentSubmission)
            .options(
                joinedload(AssignmentSubmission.assignment).joinedload(Assignment.course),
                joinedload(AssignmentSubmission.student).joinedload(StudentProfile.user),
            )
            .order_by(AssignmentSubmission.submitted_at.desc())
        )
        if assignment_id:
            query = query.filter(AssignmentSubmission.assignment_id == assignment_id)
        if student_id:
            query = query.filter(AssignmentSubmission.student_id == student_id)
        return query.all()

    @staticmethod
    def get_latest_submission(
        db: Session,
        assignment_id: str,
        student_id: str,
    ) -> Optional[AssignmentSubmission]:
        return (
            db.query(AssignmentSubmission)
            .filter(
                AssignmentSubmission.assignment_id == assignment_id,
                AssignmentSubmission.student_id == student_id,
            )
            .order_by(AssignmentSubmission.attempt_number.desc())
            .first()
        )

    @staticmethod
    def create_submission(
        db: Session,
        assignment_id: str,
        student_id: str,
        attempt_number: int,
        submitted_at: datetime,
        status: str,
        submission_content: Optional[str] = None,
        attachment_path: Optional[str] = None,
    ) -> AssignmentSubmission:
        sub = AssignmentSubmission(
            id=str(uuid.uuid4()),
            assignment_id=assignment_id,
            student_id=student_id,
            attempt_number=attempt_number,
            submission_content=submission_content,
            attachment_path=attachment_path,
            submitted_at=submitted_at,
            status=status,
        )
        db.add(sub)
        db.commit()
        db.refresh(sub)
        return sub

    @staticmethod
    def grade_submission(
        db: Session,
        submission_id: str,
        marks_obtained: Decimal,
        feedback: Optional[str],
        evaluated_by_faculty_id: str,
    ) -> Optional[AssignmentSubmission]:
        sub = db.query(AssignmentSubmission).filter(AssignmentSubmission.id == submission_id).first()
        if not sub:
            return None
        sub.marks_obtained = marks_obtained
        sub.feedback = feedback.strip() if feedback else None
        sub.evaluated_by_faculty_id = evaluated_by_faculty_id
        sub.evaluated_at = datetime.now(timezone.utc)
        sub.status = "EVALUATED"
        db.commit()
        db.refresh(sub)
        return sub

    # -------------------------------------------------------------------------
    # Assessments & Results
    # -------------------------------------------------------------------------

    @staticmethod
    def get_assessments(
        db: Session,
        course_id: Optional[str] = None,
        term_id: Optional[str] = None,
        section_id: Optional[str] = None,
    ) -> List[Assessment]:
        query = (
            db.query(Assessment)
            .options(
                joinedload(Assessment.course),
                joinedload(Assessment.term),
                joinedload(Assessment.created_by).joinedload(FacultyProfile.user),
            )
            .order_by(Assessment.assessment_date.asc())
        )
        if course_id:
            query = query.filter(Assessment.course_id == course_id)
        if term_id:
            query = query.filter(Assessment.term_id == term_id)
        if section_id:
            query = query.filter(
                (Assessment.section_id == section_id) | (Assessment.section_id.is_(None))
            )
        return query.all()

    @staticmethod
    def get_assessment_by_id(db: Session, assessment_id: str) -> Optional[Assessment]:
        return (
            db.query(Assessment)
            .options(
                joinedload(Assessment.course),
                joinedload(Assessment.term),
                joinedload(Assessment.created_by),
            )
            .filter(Assessment.id == assessment_id)
            .first()
        )

    @staticmethod
    def create_assessment(
        db: Session,
        course_id: str,
        term_id: str,
        created_by_faculty_id: str,
        title: str,
        assessment_type: str,
        max_marks: Decimal,
        weightage_percentage: Decimal,
        assessment_date: date,
        section_id: Optional[str] = None,
    ) -> Assessment:
        assessment = Assessment(
            id=str(uuid.uuid4()),
            course_id=course_id,
            term_id=term_id,
            section_id=section_id,
            created_by_faculty_id=created_by_faculty_id,
            title=title.strip(),
            assessment_type=assessment_type.upper().strip(),
            max_marks=max_marks,
            weightage_percentage=weightage_percentage,
            assessment_date=assessment_date,
        )
        db.add(assessment)
        db.commit()
        db.refresh(assessment)
        return assessment

    @staticmethod
    def get_assessment_results(
        db: Session,
        assessment_id: Optional[str] = None,
        student_id: Optional[str] = None,
    ) -> List[AssessmentResult]:
        query = (
            db.query(AssessmentResult)
            .options(
                joinedload(AssessmentResult.assessment).joinedload(Assessment.course),
                joinedload(AssessmentResult.student).joinedload(StudentProfile.user),
            )
        )
        if assessment_id:
            query = query.filter(AssessmentResult.assessment_id == assessment_id)
        if student_id:
            query = query.filter(AssessmentResult.student_id == student_id)
        return query.all()

    @staticmethod
    def create_assessment_result(
        db: Session,
        assessment_id: str,
        student_id: str,
        marks_obtained: Optional[Decimal],
        is_absent: bool = False,
        remarks: Optional[str] = None,
        evaluated_by_faculty_id: Optional[str] = None,
    ) -> AssessmentResult:
        res = AssessmentResult(
            id=str(uuid.uuid4()),
            assessment_id=assessment_id,
            student_id=student_id,
            marks_obtained=marks_obtained if not is_absent else None,
            is_absent=is_absent,
            remarks=remarks.strip() if remarks else None,
            evaluated_by_faculty_id=evaluated_by_faculty_id,
            evaluated_at=datetime.now(timezone.utc) if evaluated_by_faculty_id else None,
        )
        db.add(res)
        db.commit()
        db.refresh(res)
        return res
