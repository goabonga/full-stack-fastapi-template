from unittest.mock import MagicMock

import pytest
from sqlmodel import Session, func, select

from app.crud import CRUD
from app.models import Item
from app.tests.utils.user import create_random_user


@pytest.fixture(name="crud")
def fixture_crud(db: Session) -> CRUD:
    return CRUD(Item, db)


@pytest.fixture(name="owner_id")
def fixture_owner_id(db: Session) -> str:
    user = create_random_user(db)
    return str(user.id)


def test_count_objects(db: Session, crud: CRUD, owner_id: str):
    entity_1 = Item(title="Item title 1", owner_id=owner_id)
    entity_2 = Item(title="Item title 2", owner_id=owner_id)
    db.add(entity_1)
    db.add(entity_2)
    db.commit()
    count = crud.count(where={"owner_id": owner_id})
    assert count == 2
    count = crud.count(where={"title": "Item title 1"})
    assert count == 1
    count = crud.count(where={"title": "Nonexistent title"})
    assert count == 0


def test_count_objects_with_none_where():
    session = MagicMock()
    clazz = CRUD(Item, session)
    clazz.count(where=None)
    expected_query = select(func.count()).select_from(Item)
    session.exec.assert_called_once()
    actual_query = session.exec.call_args[0][0]
    assert str(actual_query) == str(
        expected_query
    ), "The generated query does not match the expected query"


def test_create_object(crud: CRUD, owner_id: str):
    entity = Item(title="Item title", owner_id=owner_id)
    created_object = crud.create(entity=entity)
    assert created_object.id is not None
    assert created_object.title == "Item title"


def test_read_object(db: Session, crud: CRUD, owner_id: str):
    entity = Item(title="Item title", owner_id=owner_id)
    db.add(entity)
    db.commit()
    db.refresh(entity)
    read_object = crud.read(id=entity.id)
    assert read_object.id == entity.id
    assert read_object.title == entity.title


def test_read_non_existent_object(crud: CRUD):
    result = crud.read(id="1fc6b356-596b-11ef-8880-e34e273c4c22")
    assert result is None


def test_update_object(db: Session, crud: CRUD, owner_id: str):
    entity = Item(title="Item title", owner_id=owner_id)
    db.add(entity)
    db.commit()
    db.refresh(entity)
    entity.title = "Item title 2"
    updated_object = crud.update(id=entity.id, entity=entity)
    assert updated_object.id == entity.id
    assert updated_object.title == "Item title 2"


def test_update_object_with_none_field(db: Session, crud: CRUD, owner_id: str):
    entity = Item(title="Original title", owner_id=owner_id)
    db.add(entity)
    db.commit()
    db.refresh(entity)
    updated_data = Item(title="Original title updated", owner_id=entity.owner_id)
    updated_object = crud.update(id=entity.id, entity=updated_data)
    assert updated_object.id == entity.id
    assert updated_object.title == "Original title updated"


def test_delete_object(db: Session, crud: CRUD, owner_id: str):
    entity = Item(title="Item title", owner_id=owner_id)
    db.add(entity)
    db.commit()
    db.refresh(entity)

    response = crud.delete(id=entity.id)
    assert response == {"ok": True}
    result = crud.read(id=entity.id)
    assert result is None


def test_delete_object_with_where_clause(db: Session, crud: CRUD, owner_id: str):
    entity = Item(title="Item to delete", owner_id=owner_id)
    db.add(entity)
    db.commit()
    db.refresh(entity)
    id = entity.id  # copy id
    response = crud.delete(where={"owner_id": owner_id, "title": "Item to delete"})
    assert response == {"ok": True}
    result = crud.read(id=id)
    assert result is None


def test_select(db: Session, crud: CRUD, owner_id: str):
    entity = Item(title="Item title", owner_id=owner_id)
    db.add(entity)
    db.commit()
    db.refresh(entity)
    response = crud.select(where={"owner_id": owner_id})
    assert response is not None
    response = crud.select(where={"title": "Test"})
    assert response is None


def test_select_with_limit_and_skip(db: Session, crud: CRUD, owner_id: str):
    entity_1 = Item(title="Item title 1", owner_id=owner_id)
    entity_2 = Item(title="Item title 2", owner_id=owner_id)
    entity_3 = Item(title="Item title 3", owner_id=owner_id)
    db.add(entity_1)
    db.add(entity_2)
    db.add(entity_3)
    db.commit()
    response = crud.select(where={"owner_id": owner_id}, skip=1, limit=1)
    assert len(response) == 1
    assert response[0].title == "Item title 2"


def test_select_with_none_where():
    session = MagicMock()
    clazz = CRUD(Item, session)
    clazz.select(where=None)
    expected_query = select(clazz.model).offset(0).limit(100)
    session.exec.assert_called_once()
    actual_query = session.exec.call_args[0][0]
    assert str(actual_query) == str(
        expected_query
    ), "The generated query does not match the expected query"
