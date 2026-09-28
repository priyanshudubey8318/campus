"""Academic business logic service enforcing deterministic domain validations,
enrollment integrity, mark boundaries, submission attempt tracking, and audit logging.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.academic_deps import verify_faculty_course_access
from app.models.academic import (
    AcademicTerm,
    Assessment,
    AssessmentResult,
    Assignment,
    AssignmentSubmission,
    AttendanceRecord,
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
from app.models.audit_log import AuditLog
from app.models.user import User
from app.repositories.academic_repo import AcademicRepository
from app.schemas.academic import (
    AssessmentCreate,
    AssessmentResultCreate,
    AssignmentCreate,
    AssignmentSubmissionCreate,
    AttendanceRecordCreate,
    EnrollmentCreate,
    FacultyProfileCreate,
    StudentProfileCreate,
    SubmissionGradeRequest,
)


class AcademicService:
    """Orchestrates deterministic academic business operations and audit events."""

    @staticmethod
    def _record_audit(
        db: Session,
        action: str,
        actor_id: Optional[str] = None,
        actor_role: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        try:
            log_entry = AuditLog(
                action=action,
                actor_id=actor_id,
                actor_role=actor_role,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details,
                ip_address=ip_address,
            )
            db.add(log_entry)
            db.commit()
        except Exception:
            db.rollback()

    # -------------------------------------------------------------------------
    # Hierarchy & Course Integrity
    # -------------------------------------------------------------------------

    @classmethod
    def create_course(
        cls,
        db: Session,
        institution_id: str,
        department_id: str,
        code: str,
        title: str,
        credits: int = 3,
        course_type: str = "THEORY",
        syllabus_summary: Optional[str] = None,
        actor_user: Optional[User] = None,
    ) -> Course:
        dept = AcademicRepository.get_department_by_id(db, department_id)
        if not dept:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found",
            )
        if dept.institution_id != institution_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Course institution does not match department institution",
            )

        existing = (
            db.query(Course)
            .filter(Course.institution_id == institution_id, Course.code == code.strip().upper())
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Course with code '{code}' already exists in this institution",
            )

        import uuid
        course = Course(
            id=str(uuid.uuid4()),
            institution_id=institution_id,
            department_id=department_id,
            code=code.strip().upper(),
            title=title.strip(),
            credits=credits,
            course_type=course_type,
            syllabus_summary=syllabus_summary.strip() if syllabus_summary else None,
            is_active=True,
        )
        db.add(course)
        db.commit()
        db.refresh(course)

        cls._record_audit(
            db,
            action="COURSE_CREATED",
            actor_id=actor_user.id if actor_user else None,
            actor_role=actor_user.role_names[0] if actor_user and actor_user.role_names else None,
            entity_type="Course",
            entity_id=course.id,
            details=f"Course {course.code} created for department {dept.code}",
        )
        return course

    # -------------------------------------------------------------------------
    # Profiles
    # -------------------------------------------------------------------------

    @classmethod
    def create_student_profile(
        cls,
        db: Session,
        payload: StudentProfileCreate,
        actor_user: Optional[User] = None,
    ) -> StudentProfile:
        # 1. Verify user exists and doesn't already have a student profile
        existing = AcademicRepository.get_student_profile_by_user_id(db, payload.user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Student profile already exists for this user",
            )

        existing_enr = AcademicRepository.get_student_profile_by_enrollment_number(
            db, payload.enrollment_number
        )
        if existing_enr:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Enrollment number is already in use",
            )

        # 2. Validate hierarchy consistency
        batch = AcademicRepository.get_batch_by_id(db, payload.batch_id)
        if not batch:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")

        if batch.program_id != payload.program_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Batch does not belong to the specified program",
            )

        if payload.section_id:
            section = AcademicRepository.get_section_by_id(db, payload.section_id)
            if not section:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")
            if section.batch_id != payload.batch_id:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Section does not belong to the specified batch",
                )

        profile = AcademicRepository.create_student_profile(
            db,
            user_id=payload.user_id,
            enrollment_number=payload.enrollment_number,
            program_id=payload.program_id,
            batch_id=payload.batch_id,
            section_id=payload.section_id,
            current_semester=payload.current_semester,
            admission_date=payload.admission_date,
            academic_status=payload.academic_status,
        )

        cls._record_audit(
            db,
            action="STUDENT_PROFILE_CREATED",
            actor_id=actor_user.id if actor_user else None,
            actor_role=actor_user.role_names[0] if actor_user and actor_user.role_names else None,
            entity_type="StudentProfile",
            entity_id=profile.id,
            details=f"Student profile created with enrollment {profile.enrollment_number}",
        )
        return profile

    @classmethod
    def create_faculty_profile(
        cls,
        db: Session,
        payload: FacultyProfileCreate,
        actor_user: Optional[User] = None,
    ) -> FacultyProfile:
        existing = AcademicRepository.get_faculty_profile_by_user_id(db, payload.user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Faculty profile already exists for this user",
            )

        existing_emp = AcademicRepository.get_faculty_profile_by_employee_id(db, payload.employee_id)
        if existing_emp:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Employee ID is already in use",
            )

        dept = AcademicRepository.get_department_by_id(db, payload.department_id)
        if not dept:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

        profile = AcademicRepository.create_faculty_profile(
            db,
            user_id=payload.user_id,
            employee_id=payload.employee_id,
            department_id=payload.department_id,
            designation=payload.designation,
            qualification=payload.qualification,
            specialization=payload.specialization,
            joining_date=payload.joining_date,
            is_active=payload.is_active,
        )

        cls._record_audit(
            db,
            action="FACULTY_PROFILE_CREATED",
            actor_id=actor_user.id if actor_user else None,
            actor_role=actor_user.role_names[0] if actor_user and actor_user.role_names else None,
            entity_type="FacultyProfile",
            entity_id=profile.id,
            details=f"Faculty profile created with employee ID {profile.employee_id}",
        )
        return profile

    # -------------------------------------------------------------------------
    # Enrollments
    # -------------------------------------------------------------------------

    @classmethod
    def enroll_student(
        cls,
        db: Session,
        payload: EnrollmentCreate,
        actor_user: Optional[User] = None,
    ) -> Enrollment:
        student = AcademicRepository.get_student_profile_by_id(db, payload.student_id)
        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")
        if student.academic_status != "ENROLLED":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Cannot enroll student with status '{student.academic_status}'",
            )

        course = AcademicRepository.get_course_by_id(db, payload.course_id)
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
        if not course.is_active:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Cannot enroll in an inactive course",
            )

        term = AcademicRepository.get_term_by_id(db, payload.term_id)
        if not term:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Academic term not found")
        if course.institution_id != term.institution_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Course and academic term must belong to the same institution",
            )

        # Check unique constraint
        existing = (
            db.query(Enrollment)
            .filter(
                Enrollment.student_id == payload.student_id,
                Enrollment.course_id == payload.course_id,
                Enrollment.term_id == payload.term_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Student is already enrolled in this course for the specified term",
            )

        enrollment = AcademicRepository.create_enrollment(
            db,
            student_id=payload.student_id,
            course_id=payload.course_id,
            term_id=payload.term_id,
            section_id=payload.section_id,
            enrollment_date=payload.enrollment_date,
            status=payload.status,
        )

        cls._record_audit(
            db,
            action="STUDENT_ENROLLED",
            actor_id=actor_user.id if actor_user else None,
            actor_role=actor_user.role_names[0] if actor_user and actor_user.role_names else None,
            entity_type="Enrollment",
            entity_id=enrollment.id,
            details=f"Student {student.enrollment_number} enrolled in {course.code} ({term.name})",
        )
        return enrollment

    # -------------------------------------------------------------------------
    # Attendance
    # -------------------------------------------------------------------------

    @classmethod
    def record_attendance(
        cls,
        db: Session,
        payload: AttendanceRecordCreate,
        current_user: User,
    ) -> AttendanceRecord:
        # 1. Resolve recording faculty profile
        faculty_prof = AcademicRepository.get_faculty_profile_by_user_id(db, current_user.id)
        if not faculty_prof and "SUPER_ADMIN" not in current_user.role_names and "ADMIN" not in current_user.role_names:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only assigned faculty or administrators may record attendance",
            )

        # 2. Verify faculty course assignment if faculty
        if faculty_prof and "SUPER_ADMIN" not in current_user.role_names and "ADMIN" not in current_user.role_names:
            verify_faculty_course_access(
                faculty_id=faculty_prof.id,
                course_id=payload.course_id,
                term_id=payload.term_id,
                section_id=None,
                db=db,
            )

        # 3. Verify student enrollment in that course and term
        is_enrolled = AcademicRepository.is_student_enrolled_in_course(
            db,
            student_id=payload.student_id,
            course_id=payload.course_id,
            term_id=payload.term_id,
        )
        if not is_enrolled:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Student is not actively enrolled in this course and term",
            )

        # 4. Check duplicate attendance session
        existing = (
            db.query(AttendanceRecord)
            .filter(
                AttendanceRecord.student_id == payload.student_id,
                AttendanceRecord.course_id == payload.course_id,
                AttendanceRecord.session_date == payload.session_date,
                AttendanceRecord.session_slot == payload.session_slot.strip(),
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Attendance already recorded for session slot '{payload.session_slot}' on {payload.session_date}",
            )

        record = AcademicRepository.create_attendance_record(
            db,
            student_id=payload.student_id,
            course_id=payload.course_id,
            term_id=payload.term_id,
            session_date=payload.session_date,
            session_slot=payload.session_slot,
            status=payload.status,
            source=payload.source,
            recorded_by_faculty_id=faculty_prof.id if faculty_prof else None,
            remarks=payload.remarks,
        )

        cls._record_audit(
            db,
            action="ATTENDANCE_RECORDED",
            actor_id=current_user.id,
            actor_role=current_user.role_names[0] if current_user.role_names else None,
            entity_type="AttendanceRecord",
            entity_id=record.id,
            details=f"Attendance {record.status} recorded for student on {record.session_date}",
        )
        return record

    # -------------------------------------------------------------------------
    # Coursework & Submissions
    # -------------------------------------------------------------------------

    @classmethod
    def create_assignment(
        cls,
        db: Session,
        payload: AssignmentCreate,
        current_user: User,
    ) -> Assignment:
        faculty_prof = AcademicRepository.get_faculty_profile_by_user_id(db, current_user.id)
        if not faculty_prof and "SUPER_ADMIN" not in current_user.role_names and "ADMIN" not in current_user.role_names:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only assigned faculty may create course assignments",
            )

        if faculty_prof and "SUPER_ADMIN" not in current_user.role_names and "ADMIN" not in current_user.role_names:
            verify_faculty_course_access(
                faculty_id=faculty_prof.id,
                course_id=payload.course_id,
                term_id=payload.term_id,
                section_id=payload.section_id,
                db=db,
            )

        # Validate dates deterministically
        if payload.release_date > payload.due_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Assignment release date cannot be after due date",
            )

        if payload.cutoff_date and payload.due_date > payload.cutoff_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Assignment due date cannot be after cutoff date",
            )

        # Check unique constraint
        existing = (
            db.query(Assignment)
            .filter(
                Assignment.course_id == payload.course_id,
                Assignment.term_id == payload.term_id,
                Assignment.title == payload.title.strip(),
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An assignment with this title already exists for this course and term",
            )

        assignment = AcademicRepository.create_assignment(
            db,
            course_id=payload.course_id,
            term_id=payload.term_id,
            created_by_faculty_id=faculty_prof.id if faculty_prof else None,
            title=payload.title,
            description=payload.description,
            max_marks=payload.max_marks,
            weightage_percentage=payload.weightage_percentage,
            release_date=payload.release_date,
            due_date=payload.due_date,
            cutoff_date=payload.cutoff_date,
            section_id=payload.section_id,
            allow_late_submission=payload.allow_late_submission,
        )

        cls._record_audit(
            db,
            action="ASSIGNMENT_CREATED",
            actor_id=current_user.id,
            actor_role=current_user.role_names[0] if current_user.role_names else None,
            entity_type="Assignment",
            entity_id=assignment.id,
            details=f"Assignment '{assignment.title}' created with max marks {assignment.max_marks}",
        )
        return assignment

    @classmethod
    def submit_assignment(
        cls,
        db: Session,
        assignment_id: str,
        payload: AssignmentSubmissionCreate,
        current_user: User,
    ) -> AssignmentSubmission:
        student_prof = AcademicRepository.get_student_profile_by_user_id(db, current_user.id)
        if not student_prof:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Student academic profile required to submit assignments",
            )

        assignment = AcademicRepository.get_assignment_by_id(db, assignment_id)
        if not assignment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

        # Verify student enrollment in course
        is_enrolled = AcademicRepository.is_student_enrolled_in_course(
            db,
            student_id=student_prof.id,
            course_id=assignment.course_id,
            term_id=assignment.term_id,
        )
        if not is_enrolled:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not enrolled in the course offering for this assignment",
            )

        now = datetime.now(timezone.utc)

        # Validate deadlines
        if assignment.cutoff_date and now > assignment.cutoff_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Final submission cutoff deadline has passed. Submissions are closed.",
            )

        if not assignment.allow_late_submission and now > assignment.due_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assignment due date has passed and late submissions are not allowed.",
            )

        # Derive status deterministically
        submission_status = "LATE" if now > assignment.due_date else "SUBMITTED"

        # Calculate next attempt number
        latest = AcademicRepository.get_latest_submission(db, assignment_id, student_prof.id)
        next_attempt = (latest.attempt_number + 1) if latest else 1

        submission = AcademicRepository.create_submission(
            db,
            assignment_id=assignment_id,
            student_id=student_prof.id,
            attempt_number=next_attempt,
            submitted_at=now,
            status=submission_status,
            submission_content=payload.submission_content,
            attachment_path=payload.attachment_path,
        )

        cls._record_audit(
            db,
            action="ASSIGNMENT_SUBMITTED",
            actor_id=current_user.id,
            actor_role="STUDENT",
            entity_type="AssignmentSubmission",
            entity_id=submission.id,
            details=f"Attempt #{next_attempt} submitted for assignment '{assignment.title}' (Status: {submission_status})",
        )
        return submission

    @classmethod
    def grade_submission(
        cls,
        db: Session,
        submission_id: str,
        payload: SubmissionGradeRequest,
        current_user: User,
    ) -> AssignmentSubmission:
        submission = db.query(AssignmentSubmission).filter(AssignmentSubmission.id == submission_id).first()
        if not submission:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

        assignment = submission.assignment
        faculty_prof = AcademicRepository.get_faculty_profile_by_user_id(db, current_user.id)
        if not faculty_prof and "SUPER_ADMIN" not in current_user.role_names and "ADMIN" not in current_user.role_names:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only assigned faculty may grade coursework")

        if faculty_prof and "SUPER_ADMIN" not in current_user.role_names and "ADMIN" not in current_user.role_names:
            verify_faculty_course_access(faculty_prof.id, assignment.course_id, db)

        # Marks validation
        if payload.marks_obtained < Decimal("0.00"):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Marks cannot be negative")
        if payload.marks_obtained > assignment.max_marks:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Marks obtained ({payload.marks_obtained}) exceeds maximum allowed ({assignment.max_marks})",
            )

        graded = AcademicRepository.grade_submission(
            db,
            submission_id=submission_id,
            marks_obtained=payload.marks_obtained,
            feedback=payload.feedback,
            evaluated_by_faculty_id=faculty_prof.id if faculty_prof else None,
        )

        cls._record_audit(
            db,
            action="SUBMISSION_GRADED",
            actor_id=current_user.id,
            actor_role=current_user.role_names[0] if current_user.role_names else None,
            entity_type="AssignmentSubmission",
            entity_id=submission.id,
            details=f"Submission {submission.id} graded: {payload.marks_obtained}/{assignment.max_marks}",
        )
        return graded

    # -------------------------------------------------------------------------
    # Assessments & Results
    # -------------------------------------------------------------------------

    @classmethod
    def create_assessment(
        cls,
        db: Session,
        payload: AssessmentCreate,
        current_user: User,
    ) -> Assessment:
        faculty_prof = AcademicRepository.get_faculty_profile_by_user_id(db, current_user.id)
        if not faculty_prof and "SUPER_ADMIN" not in current_user.role_names and "ADMIN" not in current_user.role_names:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only assigned faculty may create assessments")

        if faculty_prof and "SUPER_ADMIN" not in current_user.role_names and "ADMIN" not in current_user.role_names:
            verify_faculty_course_access(
                faculty_id=faculty_prof.id,
                course_id=payload.course_id,
                term_id=payload.term_id,
                section_id=payload.section_id,
                db=db,
            )

        existing = (
            db.query(Assessment)
            .filter(
                Assessment.course_id == payload.course_id,
                Assessment.term_id == payload.term_id,
                Assessment.title == payload.title.strip(),
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An assessment with this title already exists for this course and term",
            )

        assessment = AcademicRepository.create_assessment(
            db,
            course_id=payload.course_id,
            term_id=payload.term_id,
            created_by_faculty_id=faculty_prof.id if faculty_prof else None,
            title=payload.title,
            assessment_type=payload.assessment_type,
            max_marks=payload.max_marks,
            weightage_percentage=payload.weightage_percentage,
            assessment_date=payload.assessment_date,
            section_id=payload.section_id,
        )

        cls._record_audit(
            db,
            action="ASSESSMENT_CREATED",
            actor_id=current_user.id,
            actor_role=current_user.role_names[0] if current_user.role_names else None,
            entity_type="Assessment",
            entity_id=assessment.id,
            details=f"Assessment '{assessment.title}' ({assessment.assessment_type}) created",
        )
        return assessment

    @classmethod
    def record_assessment_result(
        cls,
        db: Session,
        assessment_id: str,
        payload: AssessmentResultCreate,
        current_user: User,
    ) -> AssessmentResult:
        assessment = AcademicRepository.get_assessment_by_id(db, assessment_id)
        if not assessment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

        faculty_prof = AcademicRepository.get_faculty_profile_by_user_id(db, current_user.id)
        if not faculty_prof and "SUPER_ADMIN" not in current_user.role_names and "ADMIN" not in current_user.role_names:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only assigned faculty may grade assessments")

        if faculty_prof and "SUPER_ADMIN" not in current_user.role_names and "ADMIN" not in current_user.role_names:
            verify_faculty_course_access(faculty_prof.id, assessment.course_id, db)

        # Verify student enrollment
        is_enrolled = AcademicRepository.is_student_enrolled_in_course(
            db,
            student_id=payload.student_id,
            course_id=assessment.course_id,
            term_id=assessment.term_id,
        )
        if not is_enrolled:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Student is not actively enrolled in this assessment's course offering",
            )

        # Check unique constraint
        existing = (
            db.query(AssessmentResult)
            .filter(
                AssessmentResult.assessment_id == assessment_id,
                AssessmentResult.student_id == payload.student_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Assessment result already recorded for this student",
            )

        # Marks validation
        if payload.is_absent:
            if payload.marks_obtained is not None and payload.marks_obtained > Decimal("0.00"):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Absent student cannot be awarded positive marks",
                )
            final_marks = None
        else:
            if payload.marks_obtained is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Marks obtained is required for non-absent students",
                )
            if payload.marks_obtained < Decimal("0.00"):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Marks cannot be negative",
                )
            if payload.marks_obtained > assessment.max_marks:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Marks obtained ({payload.marks_obtained}) exceeds maximum allowed ({assessment.max_marks})",
                )
            final_marks = payload.marks_obtained

        result = AcademicRepository.create_assessment_result(
            db,
            assessment_id=assessment_id,
            student_id=payload.student_id,
            marks_obtained=final_marks,
            is_absent=payload.is_absent,
            remarks=payload.remarks,
            evaluated_by_faculty_id=faculty_prof.id if faculty_prof else None,
        )

        cls._record_audit(
            db,
            action="ASSESSMENT_RESULT_RECORDED",
            actor_id=current_user.id,
            actor_role=current_user.role_names[0] if current_user.role_names else None,
            entity_type="AssessmentResult",
            entity_id=result.id,
            details=f"Result recorded for student {payload.student_id}: marks={final_marks}, absent={payload.is_absent}",
        )
        return result
