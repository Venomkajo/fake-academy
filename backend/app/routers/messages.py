"""Messages domain module (/messages): threads, announcements, read receipts.

Two audience rules shape every route here (README cards S3/W4):

- a STUDENT writes only to the teachers of their own subjects (resolved
  through group memberships → teaching assignments),
- a TEACHER writes to their own groups (announcements) and to the students
  of those groups (individual messages).

Reading is symmetric: each side sees the conversation it participates in,
with read receipts (`message_read_statuses`) tracking what is unread.
"""

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_roles
from app.models.field_of_study import FieldOfStudy
from app.models.group_membership import GroupMembership
from app.models.message import Message
from app.models.message_read_status import MessageReadStatus
from app.models.student_group import StudentGroup
from app.models.teaching_assignment import TeachingAssignment
from app.models.user import User, UserRole

from app.schemas.messages import (
    ContactsResponse,
    GroupWithMembers,
    MessageCreate,
    MessageOut,
    UserBrief,
)

router = APIRouter(prefix="/messages", tags=["messages"])


# --- shared helpers ---------------------------------------------------------
#
# Same guard conventions as the other modules: 404 missing row, 403 the
# caller may not write there.


def _teacher_ids_of_student(db: Session, student_id: int) -> list[int]:
    """Return the ids of every teacher of every subject the student takes."""
    return list(
        db.scalars(
            sa.select(TeachingAssignment.teacher_id)
            .join(GroupMembership, GroupMembership.group_id == TeachingAssignment.group_id)
            .where(GroupMembership.student_id == student_id)
            .distinct()
        )
    )


def _assignment_group_ids(db: Session, teacher_id: int) -> list[int]:
    """Return the ids of every group the teacher teaches."""
    return list(
        db.scalars(
            sa.select(TeachingAssignment.group_id).where(
                TeachingAssignment.teacher_id == teacher_id
            )
        )
    )


def _my_group_ids(db: Session, caller: User) -> list[int]:
    """Return the groups whose announcements the caller may see.

    A student's groups come from memberships, a teacher's from assignments.
    """
    if caller.role == UserRole.TEACHER:
        return _assignment_group_ids(db, caller.id)
    return list(
        db.scalars(
            sa.select(GroupMembership.group_id).where(
                GroupMembership.student_id == caller.id
            )
        )
    )


def _message_outs(
    db: Session,
    caller: User,
    where: sa.ColumnElement[bool],
) -> list[MessageOut]:
    """Flatten messages matching `where`, with names and the caller's receipts.

    Sender names come from the join; recipient/group names and the caller's
    receipts are resolved with bulk queries so a long listing never runs the
    per-row lookups an ORM-relationship walk would.
    """
    rows = db.execute(
        sa.select(
            Message,
            User.first_name.label("sender_first_name"),
            User.last_name.label("sender_last_name"),
            User.role.label("sender_role"),
        )
        .join(User, User.id == Message.sender_id)
        .where(where)
        .order_by(Message.created_at.desc(), Message.id.desc())
    ).all()

    # The caller's read receipts, keyed by message id.
    message_ids = [row[0].id for row in rows]
    read_ids: set[int] = set()
    if message_ids:
        read_ids = set(
            db.scalars(
                sa.select(MessageReadStatus.message_id).where(
                    MessageReadStatus.user_id == caller.id,
                    MessageReadStatus.message_id.in_(message_ids),
                    MessageReadStatus.read_at.isnot(None),
                )
            )
        )

    # Names for the other end of each message (recipient or group).
    recipient_ids = {row[0].recipient_id for row in rows if row[0].recipient_id}
    group_ids = {row[0].group_id for row in rows if row[0].group_id}
    recipients = {
        user.id: (user.first_name, user.last_name)
        for user in db.scalars(sa.select(User).where(User.id.in_(recipient_ids)))
    }
    groups = {
        group.id: group.name
        for group in db.scalars(
            sa.select(StudentGroup).where(StudentGroup.id.in_(group_ids))
        )
    }

    outs: list[MessageOut] = []
    for message, sender_first_name, sender_last_name, sender_role in rows:
        recipient = recipients.get(message.recipient_id) if message.recipient_id else None
        # The sender has by definition read their own message.
        read_by_caller = message.sender_id == caller.id or message.id in read_ids
        outs.append(
            MessageOut(
                id=message.id,
                sender_id=message.sender_id,
                sender_first_name=sender_first_name,
                sender_last_name=sender_last_name,
                sender_role=sender_role,
                recipient_id=message.recipient_id,
                recipient_first_name=recipient[0] if recipient else None,
                recipient_last_name=recipient[1] if recipient else None,
                group_id=message.group_id,
                group_name=groups.get(message.group_id) if message.group_id else None,
                title=message.title,
                content=message.content,
                created_at=message.created_at,
                read_by_caller=read_by_caller,
            )
        )
    return outs


def _may_write(db: Session, caller: User, body: MessageCreate) -> None:
    """Enforce the audience rules: student → own teachers, teacher → own groups."""
    # Students never announce to groups; the schema validator already made
    # sure exactly one target is present.
    if caller.role == UserRole.STUDENT:
        if body.recipient_id not in _teacher_ids_of_student(db, caller.id):
            raise HTTPException(
                status_code=403,
                detail="Możesz pisać tylko do wykładowców swoich przedmiotów",
            )
        return

    # Teacher: either an announcement to one of their groups…
    if body.group_id is not None:
        if body.group_id not in _assignment_group_ids(db, caller.id):
            raise HTTPException(
                status_code=403,
                detail="Możesz wysyłać ogłoszenia tylko do swoich grup",
            )
        return

    # …or a private message to a member of one of their groups.
    recipient = db.get(User, body.recipient_id)
    if recipient is None:
        raise HTTPException(
            status_code=404, detail=f"Nie znaleziono (odbiorca id={body.recipient_id})"
        )
    member_of = db.scalar(
        sa.select(GroupMembership.id).where(
            GroupMembership.student_id == recipient.id,
            GroupMembership.group_id.in_(_assignment_group_ids(db, caller.id)),
        )
    )
    if member_of is None:
        raise HTTPException(
            status_code=403,
            detail="Możesz pisać tylko do studentów swoich grup",
        )


# --- reads -------------------------------------------------------------------


@router.get("/contacts", response_model=ContactsResponse)
def list_contacts(
    caller: User = Depends(require_roles(UserRole.STUDENT, UserRole.TEACHER)),
    db: Session = Depends(get_db),
) -> ContactsResponse:
    """Return who the caller may write to (README S3/W4 selector data)."""
    if caller.role == UserRole.STUDENT:
        # Teachers of the student's own subjects, resolved through memberships
        # and assignments; distinct because several subjects share a teacher.
        teachers = db.scalars(
            sa.select(User)
            .where(
                User.role == UserRole.TEACHER,
                User.id.in_(_teacher_ids_of_student(db, caller.id)),
            )
            .order_by(User.last_name, User.first_name)
        ).all()
        return ContactsResponse(
            teachers=[
                UserBrief(id=t.id, first_name=t.first_name, last_name=t.last_name)
                for t in teachers
            ],
            groups=[],
        )

    # Teacher: every taught group with its member list, for the selector.
    rows = db.execute(
        sa.select(StudentGroup, FieldOfStudy)
        .join(FieldOfStudy, FieldOfStudy.id == StudentGroup.field_id)
        .where(StudentGroup.id.in_(_assignment_group_ids(db, caller.id)))
        .order_by(FieldOfStudy.name, StudentGroup.name)
    ).all()
    members_by_group: dict[int, list[UserBrief]] = {}
    for membership, user in db.execute(
        sa.select(GroupMembership, User)
        .join(User, User.id == GroupMembership.student_id)
        .where(
            GroupMembership.group_id.in_(_assignment_group_ids(db, caller.id))
        )
        .order_by(User.last_name, User.first_name)
    ).all():
        members_by_group.setdefault(membership.group_id, []).append(
            UserBrief(id=user.id, first_name=user.first_name, last_name=user.last_name)
        )
    return ContactsResponse(
        teachers=[],
        groups=[
            GroupWithMembers(
                group_id=group.id,
                group_name=group.name,
                field_name=field.name,
                students=members_by_group.get(group.id, []),
            )
            for group, field in rows
        ],
    )


@router.get("", response_model=list[MessageOut])
def list_threads(
    caller: User = Depends(require_roles(UserRole.STUDENT, UserRole.TEACHER)),
    db: Session = Depends(get_db),
) -> list[MessageOut]:
    """Return every private message the caller sent or received, newest first."""
    return _message_outs(
        db,
        caller,
        (Message.sender_id == caller.id) | (Message.recipient_id == caller.id),
    )


@router.get("/announcements", response_model=list[MessageOut])
def list_announcements(
    caller: User = Depends(require_roles(UserRole.STUDENT, UserRole.TEACHER)),
    db: Session = Depends(get_db),
) -> list[MessageOut]:
    """Return the announcements of the caller's groups (or the teacher's own)."""
    group_ids = _my_group_ids(db, caller)
    return _message_outs(db, caller, Message.group_id.in_(group_ids))


@router.get("/unread-count")
def count_unread(
    caller: User = Depends(require_roles(UserRole.STUDENT, UserRole.TEACHER)),
    db: Session = Depends(get_db),
) -> int:
    """Count the caller's unread messages (private + announcements)."""
    # Messages addressed to the caller (as recipient or as a group member),
    # excluding their own sends…
    relevant = (
        sa.select(Message.id)
        .where(
            Message.sender_id != caller.id,
            (
                (Message.recipient_id == caller.id)
                | (Message.group_id.in_(_my_group_ids(db, caller)))
            ),
        )
        .subquery()
    )
    # …minus everything the caller already has a receipt for.
    read_ids = sa.select(MessageReadStatus.message_id).where(
        MessageReadStatus.user_id == caller.id,
        MessageReadStatus.read_at.isnot(None),
    )
    return db.scalar(
        sa.select(sa.func.count()).select_from(relevant).where(
            relevant.c.id.not_in(read_ids)
        )
    )


# --- writes ------------------------------------------------------------------


@router.post("", response_model=MessageOut, status_code=201)
def send_message(
    body: MessageCreate,
    caller: User = Depends(require_roles(UserRole.STUDENT, UserRole.TEACHER)),
    db: Session = Depends(get_db),
) -> MessageOut:
    """Send one private message or publish one group announcement."""
    _may_write(db, caller, body)
    message = Message(
        sender_id=caller.id,
        recipient_id=body.recipient_id,
        group_id=body.group_id,
        title=body.title,
        content=body.content,
    )
    db.add(message)
    try:
        db.commit()
    except sa.exc.IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Nie można wysłać wiadomości")

    # One read query re-flattens the fresh row through the shared helper —
    # names and read_by_caller (own sends are read) without a second path.
    out = _message_outs(
        db,
        caller,
        Message.id == message.id,
    )
    return out[0]


@router.post("/{message_id}/read", status_code=204)
def mark_read(
    message_id: int,
    caller: User = Depends(require_roles(UserRole.STUDENT, UserRole.TEACHER)),
    db: Session = Depends(get_db),
) -> None:
    """Record the caller's read receipt for one message; idempotent."""
    message = db.get(Message, message_id)
    if message is None:
        raise HTTPException(
            status_code=404, detail=f"Nie znaleziono (wiadomość id={message_id})"
        )
    # Only the addressed reader may mark: the recipient, or a member of the
    # announcement's group (students).
    if message.recipient_id == caller.id:
        pass
    elif message.group_id is not None and caller.role == UserRole.STUDENT:
        member = db.scalar(
            sa.select(GroupMembership.id).where(
                GroupMembership.student_id == caller.id,
                GroupMembership.group_id == message.group_id,
            )
        )
        if member is None:
            raise HTTPException(
                status_code=403, detail="To ogłoszenie nie jest skierowane do Ciebie"
            )
    else:
        raise HTTPException(
            status_code=403, detail="Ta wiadomość nie jest skierowana do Ciebie"
        )

    # Idempotent: an existing receipt makes this a no-op, not a 409.
    existing = db.scalar(
        sa.select(MessageReadStatus).where(
            MessageReadStatus.message_id == message.id,
            MessageReadStatus.user_id == caller.id,
        )
    )
    if existing is None:
        db.add(
            MessageReadStatus(
                message_id=message.id,
                user_id=caller.id,
                read_at=sa.func.now(),
            )
        )
    elif existing.read_at is None:
        existing.read_at = sa.func.now()
    db.commit()