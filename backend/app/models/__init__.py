"""All ORM models, re-exported; Alembic's env.py sees every table via one wildcard import."""

from app.models.field_of_study import FieldOfStudy
from app.models.feedback import Feedback
from app.models.grade import Grade
from app.models.grade_category import GradeCategory
from app.models.group_membership import GroupMembership
from app.models.lesson_slot import LessonSlot
from app.models.lesson_topic import LessonTopic
from app.models.material import Material
from app.models.message import Message
from app.models.message_read_status import MessageReadStatus
from app.models.notification import Notification, NotificationType
from app.models.refresh_token import RefreshToken
from app.models.student_group import StudentGroup
from app.models.subject import Subject
from app.models.teaching_assignment import TeachingAssignment
from app.models.user import User, UserRole

__all__ = [
    "FieldOfStudy",
    "Feedback",
    "Grade",
    "GradeCategory",
    "GroupMembership",
    "LessonSlot",
    "LessonTopic",
    "Material",
    "Message",
    "MessageReadStatus",
    "Notification",
    "NotificationType",
    "RefreshToken",
    "StudentGroup",
    "Subject",
    "TeachingAssignment",
    "User",
    "UserRole",
]
