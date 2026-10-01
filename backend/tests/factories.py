from sqlalchemy.orm import Session

from app.core.chinese import normalize_chinese, to_traditional
from app.core.security import create_access_token
from app.model import Manga, MangaCategory, Member, MemberManga, ReadingStatus


def auth_header(member: Member) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(str(member.id))}"}


def make_member(db: Session, username: str) -> Member:
    member = Member(username=username, password_hash="x")
    db.add(member)
    db.flush()
    return member


def make_manga(db: Session, title: str, category: MangaCategory = MangaCategory.OTHER) -> Manga:
    manga = Manga(title=to_traditional(title), normalized_title=normalize_chinese(title), category=category)
    db.add(manga)
    db.flush()
    return manga


def make_entry(
    db: Session,
    member: Member,
    manga: Manga,
    status: ReadingStatus = ReadingStatus.READING,
    current_volume: int | None = None,
    current_chapter: int | None = None,
    rating: int | None = None,
) -> MemberManga:
    entry = MemberManga(
        member_id=member.id,
        manga_id=manga.id,
        status=status,
        current_volume=current_volume,
        current_chapter=current_chapter,
        rating=rating,
    )
    db.add(entry)
    db.flush()
    return entry
