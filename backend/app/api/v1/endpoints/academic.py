"""Academic domain API endpoints version 1."""

from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.academic_deps import (
    get_current_faculty_profile,
    get_current_student_profile,
    verify_faculty_course_access,
    verify_student_record_access,
)
from app.core.auth_deps import get_current_user, require_permission, require_role
from app.core.database import get_db
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
from app.models.user import User
from app.repositories.academic_repo import AcademicRepository
from app.schemas.academic import (
    AcademicTermResponse,
    AssessmentCreate,
    AssessmentResponse,
    AssessmentResultCreate,
    AssessmentResultResponse,
    AssignmentCreate,
    AssignmentResponse,
    AssignmentSubmissionCreate,
    AssignmentSubmissionResponse,
    AttendanceRecordCreate,
    AttendanceRecordResponse,
    AttendanceSummaryResponse,
    BatchResponse,
    CourseResponse,
    DepartmentResponse,
    EnrollmentCreate,
    EnrollmentResponse,
    FacultyCourseAssignmentResponse,
    FacultyProfileCreate,
    FacultyProfileResponse,
    InstitutionResponse,
    ProgramResponse,
    SectionResponse,
    StudentProfileCreate,
    StudentProfileResponse,
    SubmissionGradeRequest,
)
from app.services.academic_service import AcademicService

router = APIRouter(tags=["Academic Foundation"])


# =============================================================================
# 1. Profiles
# =============================================================================

@router.get("/student-profiles/me", response_model=StudentProfileResponse)
def get_my_student_profile(
    student_prof: StudentProfile = Depends(get_current_student_profile),
) -> StudentProfileResponse:
    """Return the academic profile of the currently authenticated student."""
    return StudentProfileResponse(
        id=student_prof.id,
        user_id=student_prof.user_id,
        enrollment_number=student_prof.enrollment_number,
        program_id=student_prof.program_id,
        batch_id=student_prof.batch_id,
        section_id=student_prof.section_id,
        current_semester=student_prof.current_semester,
        admission_date=student_prof.admission_date,
        academic_status=student_prof.academic_status,
        created_at=student_prof.created_at,
        program_name=student_prof.program.name if student_prof.program else None,
        batch_name=student_prof.batch.name if student_prof.batch else None,
        section_name=student_prof.section.name if student_prof.section else None,
        full_name=student_prof.user.full_name if student_prof.user else None,
        email=student_prof.user.email if student_prof.user else None,
    )


@router.get("/student-profiles/{profile_id}", response_model=StudentProfileResponse)
def get_student_profile_by_id(
    profile_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StudentProfileResponse:
    """Return student profile by ID with scoped authorization checks."""
    verify_student_record_access(current_user, profile_id, db)
    student_prof = AcademicRepository.get_student_profile_by_id(db, profile_id)
    if not student_prof:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")

    return StudentProfileResponse(
        id=student_prof.id,
        user_id=student_prof.user_id,
        enrollment_number=student_prof.enrollment_number,
        program_id=student_prof.program_id,
        batch_id=student_prof.batch_id,
        section_id=student_prof.section_id,
        current_semester=student_prof.current_semester,
        admission_date=student_prof.admission_date,
        academic_status=student_prof.academic_status,
        created_at=student_prof.created_at,
        program_name=student_prof.program.name if student_prof.program else None,
        batch_name=student_prof.batch.name if student_prof.batch else None,
        section_name=student_prof.section.name if student_prof.section else None,
        full_name=student_prof.user.full_name if student_prof.user else None,
        email=student_prof.user.email if student_prof.user else None,
    )


@router.post("/student-profiles", response_model=StudentProfileResponse, status_code=status.HTTP_201_CREATED)
def create_student_profile(
    payload: StudentProfileCreate,
    current_user: User = Depends(require_permission("academic:write_all")),
    db: Session = Depends(get_db),
) -> StudentProfileResponse:
    """Create a new student academic profile (Admins/SuperAdmins only)."""
    prof = AcademicService.create_student_profile(db, payload, actor_user=current_user)
    return StudentProfileResponse.model_validate(prof)


@router.get("/faculty-profiles/me", response_model=FacultyProfileResponse)
def get_my_faculty_profile(
    faculty_prof: FacultyProfile = Depends(get_current_faculty_profile),
) -> FacultyProfileResponse:
    """Return the academic profile of the currently authenticated faculty member."""
    return FacultyProfileResponse(
        id=faculty_prof.id,
        user_id=faculty_prof.user_id,
        employee_id=faculty_prof.employee_id,
        department_id=faculty_prof.department_id,
        designation=faculty_prof.designation,
        qualification=faculty_prof.qualification,
        specialization=faculty_prof.specialization,
        joining_date=faculty_prof.joining_date,
        is_active=faculty_prof.is_active,
        created_at=faculty_prof.created_at,
        department_name=faculty_prof.department.name if faculty_prof.department else None,
        full_name=faculty_prof.user.full_name if faculty_prof.user else None,
        email=faculty_prof.user.email if faculty_prof.user else None,
    )


@router.get("/faculty-profiles/{profile_id}", response_model=FacultyProfileResponse)
def get_faculty_profile_by_id(
    profile_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FacultyProfileResponse:
    """Return faculty profile by ID."""
    prof = AcademicRepository.get_faculty_profile_by_id(db, profile_id)
    if not prof:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Faculty profile not found")
    return FacultyProfileResponse(
        id=prof.id,
        user_id=prof.user_id,
        employee_id=prof.employee_id,
        department_id=prof.department_id,
        designation=prof.designation,
        qualification=prof.qualification,
        specialization=prof.specialization,
        joining_date=prof.joining_date,
        is_active=prof.is_active,
        created_at=prof.created_at,
        department_name=prof.department.name if prof.department else None,
        full_name=prof.user.full_name if prof.user else None,
        email=prof.user.email if prof.user else None,
    )


@router.post("/faculty-profiles", response_model=FacultyProfileResponse, status_code=status.HTTP_201_CREATED)
def create_faculty_profile(
    payload: FacultyProfileCreate,
    current_user: User = Depends(require_permission("academic:write_all")),
    db: Session = Depends(get_db),
) -> FacultyProfileResponse:
    """Create a new faculty profile (Admins/SuperAdmins only)."""
    prof = AcademicService.create_faculty_profile(db, payload, actor_user=current_user)
    return FacultyProfileResponse.model_validate(prof)


# =============================================================================
# 2. Institutional Hierarchy
# =============================================================================

@router.get("/institutions", response_model=List[InstitutionResponse])
def list_institutions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[InstitutionResponse]:
    return [InstitutionResponse.model_validate(i) for i in AcademicRepository.get_institutions(db)]


@router.get("/departments", response_model=List[DepartmentResponse])
def list_departments(
    institution_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[DepartmentResponse]:
    return [DepartmentResponse.model_validate(d) for d in AcademicRepository.get_departments(db, institution_id)]


@router.get("/programs", response_model=List[ProgramResponse])
def list_programs(
    department_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[ProgramResponse]:
    return [ProgramResponse.model_validate(p) for p in AcademicRepository.get_programs(db, department_id)]


@router.get("/batches", response_model=List[BatchResponse])
def list_batches(
    program_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[BatchResponse]:
    return [BatchResponse.model_validate(b) for b in AcademicRepository.get_batches(db, program_id)]


@router.get("/sections", response_model=List[SectionResponse])
def list_sections(
    batch_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[SectionResponse]:
    return [SectionResponse.model_validate(s) for s in AcademicRepository.get_sections(db, batch_id)]


@router.get("/terms", response_model=List[AcademicTermResponse])
def list_terms(
    institution_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[AcademicTermResponse]:
    return [AcademicTermResponse.model_validate(t) for t in AcademicRepository.get_terms(db, institution_id)]


@router.get("/terms/current", response_model=AcademicTermResponse)
def get_current_term(
    institution_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AcademicTermResponse:
    term = AcademicRepository.get_current_term(db, institution_id)
    if not term:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active academic term found")
    return AcademicTermResponse.model_validate(term)


@router.get("/courses", response_model=List[CourseResponse])
def list_courses(
    institution_id: Optional[str] = Query(None),
    department_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[CourseResponse]:
    return [
        CourseResponse.model_validate(c)
        for c in AcademicRepository.get_courses(db, institution_id, department_id)
    ]


# =============================================================================
# 3. Enrollments & Teaching Assignments
# =============================================================================

@router.get("/enrollments", response_model=List[EnrollmentResponse])
def list_enrollments(
    student_id: Optional[str] = Query(None),
    course_id: Optional[str] = Query(None),
    term_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[EnrollmentResponse]:
    """List enrollments with role-based scoping."""
    role_names = set(current_user.role_names)

    # Scoping
    if "STUDENT" in role_names and "ADMIN" not in role_names and "SUPER_ADMIN" not in role_names:
        student_prof = AcademicRepository.get_student_profile_by_user_id(db, current_user.id)
        if not student_prof:
            return []
        student_id = student_prof.id

    enrollments = AcademicRepository.get_enrollments(db, student_id=student_id, course_id=course_id, term_id=term_id)
    results = []
    for e in enrollments:
        results.append(
            EnrollmentResponse(
                id=e.id,
                student_id=e.student_id,
                course_id=e.course_id,
                term_id=e.term_id,
                section_id=e.section_id,
                enrollment_date=e.enrollment_date,
                status=e.status,
                created_at=e.created_at,
                course_code=e.course.code if e.course else None,
                course_title=e.course.title if e.course else None,
                course_credits=e.course.credits if e.course else None,
                term_name=e.term.name if e.term else None,
            )
        )
    return results


@router.post("/enrollments", response_model=EnrollmentResponse, status_code=status.HTTP_201_CREATED)
def enroll_student(
    payload: EnrollmentCreate,
    current_user: User = Depends(require_permission("academic:write_assigned")),
    db: Session = Depends(get_db),
) -> EnrollmentResponse:
    enrollment = AcademicService.enroll_student(db, payload, actor_user=current_user)
    return EnrollmentResponse.model_validate(enrollment)


@router.get("/faculty-assignments", response_model=List[FacultyCourseAssignmentResponse])
def list_faculty_assignments(
    faculty_id: Optional[str] = Query(None),
    course_id: Optional[str] = Query(None),
    term_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[FacultyCourseAssignmentResponse]:
    """List faculty course assignments with role scoping."""
    role_names = set(current_user.role_names)
    if "FACULTY" in role_names and "ADMIN" not in role_names and "SUPER_ADMIN" not in role_names:
        faculty_prof = AcademicRepository.get_faculty_profile_by_user_id(db, current_user.id)
        if not faculty_prof:
            return []
        faculty_id = faculty_prof.id

    assignments = AcademicRepository.get_faculty_assignments(
        db, faculty_id=faculty_id, course_id=course_id, term_id=term_id
    )
    results = []
    for a in assignments:
        results.append(
            FacultyCourseAssignmentResponse(
                id=a.id,
                faculty_id=a.faculty_id,
                course_id=a.course_id,
                term_id=a.term_id,
                section_id=a.section_id,
                role=a.role,
                created_at=a.created_at,
                course_code=a.course.code if a.course else None,
                course_title=a.course.title if a.course else None,
                term_name=a.term.name if a.term else None,
                section_name=a.section.name if a.section else None,
            )
        )
    return results


# =============================================================================
# 4. Attendance
# =============================================================================

@router.get("/attendance", response_model=List[AttendanceRecordResponse])
def list_attendance_records(
    student_id: Optional[str] = Query(None),
    course_id: Optional[str] = Query(None),
    term_id: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[AttendanceRecordResponse]:
    role_names = set(current_user.role_names)

    if "STUDENT" in role_names and "ADMIN" not in role_names and "SUPER_ADMIN" not in role_names:
        student_prof = AcademicRepository.get_student_profile_by_user_id(db, current_user.id)
        if not student_prof:
            return []
        student_id = student_prof.id
    elif student_id:
        verify_student_record_access(current_user, student_id, db, course_id=course_id)

    records = AcademicRepository.get_attendance_records(
        db,
        student_id=student_id,
        course_id=course_id,
        term_id=term_id,
        start_date=start_date,
        end_date=end_date,
    )
    return [
        AttendanceRecordResponse(
            id=r.id,
            student_id=r.student_id,
            course_id=r.course_id,
            term_id=r.term_id,
            session_date=r.session_date,
            session_slot=r.session_slot,
            status=r.status,
            source=r.source,
            recorded_by_faculty_id=r.recorded_by_faculty_id,
            remarks=r.remarks,
            created_at=r.created_at,
            course_code=r.course.code if r.course else None,
            course_title=r.course.title if r.course else None,
        )
        for r in records
    ]


@router.get("/attendance/summary", response_model=AttendanceSummaryResponse)
def get_attendance_summary(
    student_id: Optional[str] = Query(None),
    course_id: Optional[str] = Query(None),
    term_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AttendanceSummaryResponse:
    """Calculate derived attendance statistics on demand from raw session records."""
    role_names = set(current_user.role_names)

    if "STUDENT" in role_names and "ADMIN" not in role_names and "SUPER_ADMIN" not in role_names:
        student_prof = AcademicRepository.get_student_profile_by_user_id(db, current_user.id)
        if not student_prof:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")
        student_id = student_prof.id
    else:
        if not student_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="student_id query parameter required")
        verify_student_record_access(current_user, student_id, db, course_id=course_id)

    stats = AcademicRepository.calculate_student_attendance_summary(
        db, student_id=student_id, course_id=course_id, term_id=term_id
    )
    return AttendanceSummaryResponse(**stats)


@router.post("/attendance", response_model=AttendanceRecordResponse, status_code=status.HTTP_201_CREATED)
def record_attendance(
    payload: AttendanceRecordCreate,
    current_user: User = Depends(require_permission("academic:write_assigned")),
    db: Session = Depends(get_db),
) -> AttendanceRecordResponse:
    rec = AcademicService.record_attendance(db, payload, current_user)
    return AttendanceRecordResponse.model_validate(rec)


# =============================================================================
# 5. Coursework / Assignments
# =============================================================================

@router.get("/assignments", response_model=List[AssignmentResponse])
def list_assignments(
    course_id: Optional[str] = Query(None),
    term_id: Optional[str] = Query(None),
    section_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[AssignmentResponse]:
    assignments = AcademicRepository.get_assignments(db, course_id=course_id, term_id=term_id, section_id=section_id)
    return [
        AssignmentResponse(
            id=a.id,
            course_id=a.course_id,
            term_id=a.term_id,
            section_id=a.section_id,
            created_by_faculty_id=a.created_by_faculty_id,
            title=a.title,
            description=a.description,
            max_marks=a.max_marks,
            weightage_percentage=a.weightage_percentage,
            release_date=a.release_date,
            due_date=a.due_date,
            cutoff_date=a.cutoff_date,
            allow_late_submission=a.allow_late_submission,
            created_at=a.created_at,
            course_code=a.course.code if a.course else None,
            course_title=a.course.title if a.course else None,
        )
        for a in assignments
    ]


@router.post("/assignments", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
def create_assignment(
    payload: AssignmentCreate,
    current_user: User = Depends(require_permission("academic:write_assigned")),
    db: Session = Depends(get_db),
) -> AssignmentResponse:
    asg = AcademicService.create_assignment(db, payload, current_user)
    return AssignmentResponse.model_validate(asg)


@router.get("/assignments/{assignment_id}/submissions", response_model=List[AssignmentSubmissionResponse])
def list_assignment_submissions(
    assignment_id: str,
    student_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[AssignmentSubmissionResponse]:
    role_names = set(current_user.role_names)

    if "STUDENT" in role_names and "ADMIN" not in role_names and "SUPER_ADMIN" not in role_names:
        student_prof = AcademicRepository.get_student_profile_by_user_id(db, current_user.id)
        if not student_prof:
            return []
        student_id = student_prof.id

    subs = AcademicRepository.get_submissions(db, assignment_id=assignment_id, student_id=student_id)
    return [
        AssignmentSubmissionResponse(
            id=s.id,
            assignment_id=s.assignment_id,
            student_id=s.student_id,
            attempt_number=s.attempt_number,
            submission_content=s.submission_content,
            attachment_path=s.attachment_path,
            submitted_at=s.submitted_at,
            status=s.status,
            marks_obtained=s.marks_obtained,
            feedback=s.feedback,
            evaluated_by_faculty_id=s.evaluated_by_faculty_id,
            evaluated_at=s.evaluated_at,
            created_at=s.created_at,
            assignment_title=s.assignment.title if s.assignment else None,
            max_marks=s.assignment.max_marks if s.assignment else None,
        )
        for s in subs
    ]


@router.post("/assignments/{assignment_id}/submit", response_model=AssignmentSubmissionResponse, status_code=status.HTTP_201_CREATED)
def submit_assignment(
    assignment_id: str,
    payload: AssignmentSubmissionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssignmentSubmissionResponse:
    sub = AcademicService.submit_assignment(db, assignment_id, payload, current_user)
    return AssignmentSubmissionResponse.model_validate(sub)


@router.post("/submissions/{submission_id}/grade", response_model=AssignmentSubmissionResponse)
def grade_submission(
    submission_id: str,
    payload: SubmissionGradeRequest,
    current_user: User = Depends(require_permission("academic:write_assigned")),
    db: Session = Depends(get_db),
) -> AssignmentSubmissionResponse:
    graded = AcademicService.grade_submission(db, submission_id, payload, current_user)
    return AssignmentSubmissionResponse.model_validate(graded)


# =============================================================================
# 6. Assessments & Results
# =============================================================================

@router.get("/assessments", response_model=List[AssessmentResponse])
def list_assessments(
    course_id: Optional[str] = Query(None),
    term_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[AssessmentResponse]:
    assessments = AcademicRepository.get_assessments(db, course_id=course_id, term_id=term_id)
    return [
        AssessmentResponse(
            id=a.id,
            course_id=a.course_id,
            term_id=a.term_id,
            section_id=a.section_id,
            created_by_faculty_id=a.created_by_faculty_id,
            title=a.title,
            assessment_type=a.assessment_type,
            max_marks=a.max_marks,
            weightage_percentage=a.weightage_percentage,
            assessment_date=a.assessment_date,
            created_at=a.created_at,
            course_code=a.course.code if a.course else None,
            course_title=a.course.title if a.course else None,
        )
        for a in assessments
    ]


@router.post("/assessments", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
def create_assessment(
    payload: AssessmentCreate,
    current_user: User = Depends(require_permission("academic:write_assigned")),
    db: Session = Depends(get_db),
) -> AssessmentResponse:
    assessment = AcademicService.create_assessment(db, payload, current_user)
    return AssessmentResponse.model_validate(assessment)


@router.get("/assessments/{assessment_id}/results", response_model=List[AssessmentResultResponse])
def list_assessment_results(
    assessment_id: str,
    student_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[AssessmentResultResponse]:
    role_names = set(current_user.role_names)

    if "STUDENT" in role_names and "ADMIN" not in role_names and "SUPER_ADMIN" not in role_names:
        student_prof = AcademicRepository.get_student_profile_by_user_id(db, current_user.id)
        if not student_prof:
            return []
        student_id = student_prof.id

    results = AcademicRepository.get_assessment_results(db, assessment_id=assessment_id, student_id=student_id)
    return [
        AssessmentResultResponse(
            id=r.id,
            assessment_id=r.assessment_id,
            student_id=r.student_id,
            marks_obtained=r.marks_obtained,
            is_absent=r.is_absent,
            remarks=r.remarks,
            evaluated_by_faculty_id=r.evaluated_by_faculty_id,
            evaluated_at=r.evaluated_at,
            created_at=r.created_at,
            assessment_title=r.assessment.title if r.assessment else None,
            assessment_type=r.assessment.assessment_type if r.assessment else None,
            max_marks=r.assessment.max_marks if r.assessment else None,
            student_enrollment_number=r.student.enrollment_number if r.student else None,
            student_name=r.student.user.full_name if r.student and r.student.user else None,
        )
        for r in results
    ]


@router.post("/assessments/{assessment_id}/results", response_model=AssessmentResultResponse, status_code=status.HTTP_201_CREATED)
def record_assessment_result(
    assessment_id: str,
    payload: AssessmentResultCreate,
    current_user: User = Depends(require_permission("academic:write_assigned")),
    db: Session = Depends(get_db),
) -> AssessmentResultResponse:
    result = AcademicService.record_assessment_result(db, assessment_id, payload, current_user)
    return AssessmentResultResponse.model_validate(result)
