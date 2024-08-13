import uuid
from typing import Any, Generic, TypeVar

from sqlmodel import Session, SQLModel, delete, func, select

from app.core.security import get_password_hash, verify_password
from app.models import Item, ItemCreate, User, UserCreate, UserUpdate

T = TypeVar("T", bound=SQLModel)


class CRUD(Generic[T]):
    def __init__(self, model: type[T], session: Session):
        self.model = model
        self.session = session

    def count(self, where: dict[str, any] | None = None) -> int:
        if where is None:
            where = {}
        query = select(func.count()).select_from(self.model)
        for key, value in where.items():
            query = query.where(getattr(self.model, key) == value)
        count = self.session.exec(query).one()
        return count

    def create(self, entity: T) -> T:
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def read(self, id: int | str) -> T | None:
        item = self.session.get(self.model, id)
        return item

    def update(self, id: int | str, entity: T) -> T:
        item = self.read(id)
        item.sqlmodel_update(item, update=entity.model_dump())
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return item

    def delete(
        self,
        id: int | str | None = None,
        where: dict[str, any] | None = None,
        session: Session = None,
    ):
        if where is None:
            where = {}

        if id is None:
            query = delete(self.model)
            for key, value in where.items():
                query = query.where(getattr(self.model, key) == value)
            self.session.exec(query)
            self.session.commit()
        else:
            item = self.read(id)
            self.session.delete(item)
            self.session.commit()
        return {"ok": True}

    def select(
        self,
        where: dict[str, any] | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[T] | None:
        if where is None:
            where = {}
        query = select(self.model)
        for key, value in where.items():
            query = query.where(getattr(self.model, key) == value)
        query = query.offset(skip).limit(limit)
        results = self.session.exec(query).all()
        return results if results else None


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item
