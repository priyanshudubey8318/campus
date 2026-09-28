"""Scoped authorization dependencies and profile resolution for the Academic Domain."""

from typing import Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth_deps import get_current_user
from app.core.database import get_db
from app.models.academic import FacultyProfile, StudentProfile
from app.models.user import User
from app.repositories.academic_repo import AcademicRepository


def get_current_student_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StudentProfile:
    """Resolve and return the StudentProfile for the authenticated caller.
    
    Raises:
        HTTPException(403): If the caller does not hold the STUDENT role.
        HTTPException(404): If no StudentProfile is linked to this user.
    """
    profile = AcademicRepository.get_student_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student academic profile not found for the current user",
        )
    return profile


def get_current_faculty_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FacultyProfile:
    """Resolve and return the FacultyProfile for the authenticated caller.
    
    Raises:
        HTTPException(403): If the caller does not hold the FACULTY role.
        HTTPException(404): If no FacultyProfile is linked to this user.
    """
    profile = AcademicRepository.get_faculty_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Faculty academic profile not found for the current user",
        )
    return profile


def verify_faculty_course_access(
    faculty_id: str,
    course_id: str,
    db: Session,
    term_id: Optional[str] = None,
    section_id: Optional[str] = None,
) -> bool:
    """Verify that a faculty member is assigned to teach the given course/section.
    
    Raises:
        HTTPException(403): If faculty is not authorized for this course offering.
    """
    is_assigned = AcademicRepository.is_faculty_assigned_to_course(
        db,
        faculty_id=faculty_id,
        course_id=course_id,
        term_id=term_id,
        section_id=section_id,
    )
    if not is_assigned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Faculty member is not assigned to this course offering",
        )
    return True


def verify_student_record_access(
    current_user: User,
    target_student_id: str,
    db: Session,
    course_id: Optional[str] = None,
) -> bool:
    """Enforce scoped authorization over student academic records.
    
    Rules:
    - SUPER_ADMIN, ADMIN: Full institutional access.
    - STUDENT: Allowed ONLY for their own StudentProfile id.
    - FACULTY: Allowed ONLY for students enrolled in courses assigned to this faculty.
    - Others: Access denied (403).
    """
    role_names = set(current_user.role_names)

    if "SUPER_ADMIN" in role_names or "ADMIN" in role_names or "ADVISOR" in role_names:
        return True

    if "STUDENT" in role_names:
        student_prof = AcademicRepository.get_student_profile_by_user_id(db, current_user.id)
        if not student_prof or student_prof.id != target_student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Students may only inspect their own academic records",
            )
        return True

    if "FACULTY" in role_names:
        faculty_prof = AcademicRepository.get_faculty_profile_by_user_id(db, current_user.id)
        if not faculty_prof:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Faculty profile not found",
            )

        if course_id:
            # Check faculty is assigned to this course
            verify_faculty_course_access(faculty_prof.id, course_id, db)
            # Check student is enrolled in this course
            if not AcademicRepository.is_student_enrolled_in_course(db, target_student_id, course_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied: Student is not enrolled in the specified course",
                )
            return True

        # If no specific course_id provided, verify that the student is enrolled in AT LEAST ONE
        # course assigned to this faculty member
        faculty_assignments = AcademicRepository.get_faculty_assignments(db, faculty_id=faculty_prof.id)
        assigned_course_ids = {fa.course_id for fa in faculty_assignments}

        student_enrollments = AcademicRepository.get_enrollments(db, student_id=target_student_id)
        enrolled_course_ids = {e.course_id for e in student_enrollments}

        if not (assigned_course_ids & enrolled_course_ids):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Faculty member does not teach any course taken by this student",
            )
        return True

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied: Caller role does not have permission to view this academic record",
    )
