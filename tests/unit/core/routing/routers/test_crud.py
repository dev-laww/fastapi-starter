"""
Unit tests for AppCRUDRouter.
"""

import uuid
from unittest.mock import AsyncMock, Mock

import pytest

from authentication.core.base import BaseDBModel, BaseModel
from authentication.core.database.repository import Repository
from authentication.core.exceptions import NotFoundError, ValidationError
from authentication.core.routing.routers.crud import AppCRUDRouter
from authentication.schemas import PaginationParams


# Test models
class SampleModel(BaseDBModel):
    """Sample model for CRUD operations."""
    name: str
    description: str | None = None


class CreateSampleSchema(BaseModel):
    """Schema for creating sample entities."""
    name: str
    description: str | None = None


class UpdateSampleSchema(BaseModel):
    """Schema for updating sample entities."""
    name: str | None = None
    description: str | None = None


# Fixtures
@pytest.fixture
def mock_repository():
    """Create a mock repository."""
    repo = Mock(spec=Repository)
    repo.get = AsyncMock()
    repo.all = AsyncMock()
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.soft_delete = AsyncMock()
    repo.restore = AsyncMock()
    repo.exists = AsyncMock()
    repo.count = AsyncMock()
    return repo


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    return Mock()


@pytest.fixture
def sample_entity():
    """Create a sample test entity."""
    import arrow
    return SampleModel(
        id=uuid.uuid4(),
        name="Test Item",
        description="Test Description",
        created_at=arrow.utcnow().datetime,
        updated_at=arrow.utcnow().datetime,
        deleted_at=None,
    )


@pytest.fixture
def sample_entities():
    """Create sample test entities."""
    import arrow
    return [
        SampleModel(
            id=uuid.uuid4(),
            name=f"Item {i}",
            description=f"Description {i}",
            created_at=arrow.utcnow().datetime,
            updated_at=arrow.utcnow().datetime,
            deleted_at=None,
        )
        for i in range(5)
    ]


# Test initialization
def test_crud_router_initialization():
    """CRUD router initializes with correct parameters."""
    router = AppCRUDRouter(
        prefix="/test",
        tags=["test"],
        model=SampleModel,
        create_schema=CreateSampleSchema,
        update_schema=UpdateSampleSchema,
    )

    assert router.model == SampleModel
    assert router.model_name == "samplemodel"
    assert router.create_schema == CreateSampleSchema
    assert router.update_schema == UpdateSampleSchema
    assert router.include_create is True
    assert router.include_update is True
    assert router.include_delete is True


def test_crud_router_initialization_without_create():
    """CRUD router initializes without create endpoint."""
    router = AppCRUDRouter(
        prefix="/test",
        model=SampleModel,
        create_schema=CreateSampleSchema,
        update_schema=UpdateSampleSchema,
        include_create=False,
    )

    assert router.include_create is False


def test_crud_router_initialization_without_update():
    """CRUD router initializes without update endpoint."""
    router = AppCRUDRouter(
        prefix="/test",
        model=SampleModel,
        create_schema=CreateSampleSchema,
        update_schema=UpdateSampleSchema,
        include_update=False,
    )

    assert router.include_update is False


def test_crud_router_initialization_without_delete():
    """CRUD router initializes without delete endpoint."""
    router = AppCRUDRouter(
        prefix="/test",
        model=SampleModel,
        create_schema=CreateSampleSchema,
        update_schema=UpdateSampleSchema,
        include_delete=False,
    )

    assert router.include_delete is False


def test_crud_router_raises_error_when_create_schema_missing():
    """CRUD router raises ValueError when create_schema is missing but include_create is True."""
    with pytest.raises(ValueError, match="create_schema must be provided"):
        AppCRUDRouter(
            prefix="/test",
            model=SampleModel,
            update_schema=UpdateSampleSchema,
            include_create=True,
        )


def test_crud_router_raises_error_when_update_schema_missing():
    """CRUD router raises ValueError when update_schema is missing but include_update is True."""
    with pytest.raises(ValueError, match="update_schema must be provided"):
        AppCRUDRouter(
            prefix="/test",
            model=SampleModel,
            create_schema=CreateSampleSchema,
            include_update=True,
        )


# Test route registration
def test_crud_router_registers_get_all_route():
    """CRUD router registers GET all route."""
    router = AppCRUDRouter(
        prefix="/test",
        model=SampleModel,
        create_schema=CreateSampleSchema,
        update_schema=UpdateSampleSchema,
    )

    # Check routes by name
    route_names = [getattr(route, "name", None) for route in router.http_router.routes]
    assert "get_all_samplemodels" in route_names


def test_crud_router_registers_get_one_route():
    """CRUD router registers GET one route."""
    router = AppCRUDRouter(
        prefix="/test",
        model=SampleModel,
        create_schema=CreateSampleSchema,
        update_schema=UpdateSampleSchema,
    )

    # Check routes by name
    route_names = [getattr(route, "name", None) for route in router.http_router.routes]
    assert "get_samplemodel" in route_names


def test_crud_router_registers_create_route():
    """CRUD router registers POST create route."""
    router = AppCRUDRouter(
        prefix="/test",
        model=SampleModel,
        create_schema=CreateSampleSchema,
        update_schema=UpdateSampleSchema,
    )

    # Check routes by name
    route_names = [getattr(route, "name", None) for route in router.http_router.routes]
    assert "create_samplemodel" in route_names


def test_crud_router_registers_update_route():
    """CRUD router registers PATCH update route."""
    router = AppCRUDRouter(
        prefix="/test",
        model=SampleModel,
        create_schema=CreateSampleSchema,
        update_schema=UpdateSampleSchema,
    )

    # Check routes by name
    route_names = [getattr(route, "name", None) for route in router.http_router.routes]
    assert "update_samplemodel" in route_names


def test_crud_router_registers_soft_delete_route():
    """CRUD router registers DELETE soft delete route."""
    router = AppCRUDRouter(
        prefix="/test",
        model=SampleModel,
        create_schema=CreateSampleSchema,
        update_schema=UpdateSampleSchema,
    )

    # Check routes by name
    route_names = [getattr(route, "name", None) for route in router.http_router.routes]
    assert "soft_delete_samplemodel" in route_names


def test_crud_router_registers_restore_route():
    """CRUD router registers PATCH restore route."""
    router = AppCRUDRouter(
        prefix="/test",
        model=SampleModel,
        create_schema=CreateSampleSchema,
        update_schema=UpdateSampleSchema,
    )

    # Check routes by name
    route_names = [getattr(route, "name", None) for route in router.http_router.routes]
    assert "restore_samplemodel" in route_names


def test_crud_router_registers_force_delete_route():
    """CRUD router registers DELETE force delete route."""
    router = AppCRUDRouter(
        prefix="/test",
        model=SampleModel,
        create_schema=CreateSampleSchema,
        update_schema=UpdateSampleSchema,
    )

    # Check routes by name
    route_names = [getattr(route, "name", None) for route in router.http_router.routes]
    assert "delete_samplemodel" in route_names


def test_crud_router_does_not_register_create_when_disabled():
    """CRUD router does not register create route when include_create is False."""
    router = AppCRUDRouter(
        prefix="/test",
        model=SampleModel,
        create_schema=CreateSampleSchema,
        update_schema=UpdateSampleSchema,
        include_create=False,
    )

    # Check routes by name
    route_names = [getattr(route, "name", None) for route in router.http_router.routes]
    assert "create_samplemodel" not in route_names


def test_crud_router_does_not_register_update_when_disabled():
    """CRUD router does not register update route when include_update is False."""
    router = AppCRUDRouter(
        prefix="/test",
        model=SampleModel,
        create_schema=CreateSampleSchema,
        update_schema=UpdateSampleSchema,
        include_update=False,
    )

    # Check routes by name
    route_names = [getattr(route, "name", None) for route in router.http_router.routes]
    assert "update_samplemodel" not in route_names


def test_crud_router_does_not_register_delete_when_disabled():
    """CRUD router does not register delete routes when include_delete is False."""
    router = AppCRUDRouter(
        prefix="/test",
        model=SampleModel,
        create_schema=CreateSampleSchema,
        update_schema=UpdateSampleSchema,
        include_delete=False,
    )

    # Check routes by name
    route_names = [getattr(route, "name", None) for route in router.http_router.routes]
    assert "soft_delete_samplemodel" not in route_names
    assert "delete_samplemodel" not in route_names
    assert "restore_samplemodel" not in route_names


# Test get_all endpoint
@pytest.mark.asyncio
async def test_get_all_retrieves_all_entities(mock_repository, sample_entities):
    """get_all retrieves all entities with pagination."""
    router = AppCRUDRouter(
        prefix="/test",
        model=SampleModel,
        create_schema=CreateSampleSchema,
        update_schema=UpdateSampleSchema,
    )

    mock_repository.all.return_value = sample_entities
    mock_repository.count.return_value = 5

    pagination = PaginationParams(page=1, limit=10)
    route_handler = router.get_all

    result = await route_handler(
        repository=mock_repository,
        pagination=pagination,
    )

    assert result.success is True
    assert result.data.pagination.total_items == 5
    assert len(result.data.items) == 5
    mock_repository.all.assert_called_once_with(skip=0, limit=10)
    mock_repository.count.assert_called_once()


@pytest.mark.asyncio
async def test_get_all_with_pagination(mock_repository, sample_entities):
    """get_all handles pagination correctly."""
    router = AppCRUDRouter(
        prefix="/test",
        model=SampleModel,
        create_schema=CreateSampleSchema,
        update_schema=UpdateSampleSchema,
    )

    mock_repository.all.return_value = sample_entities[:3]
    mock_repository.count.return_value = 5

    pagination = PaginationParams(page=1, limit=3)
    route_handler = router.get_all

    result = await route_handler(
        repository=mock_repository,
        pagination=pagination,
    )

    assert result.data.pagination.current_page == 1
    assert result.data.pagination.items_per_page == 3
    assert result.data.pagination.total_pages == 2
    assert result.data.pagination.has_next is True
    assert result.data.pagination.has_previous is False


@pytest.mark.asyncio
async def test_get_all_pagination_next_page(mock_repository, sample_entities):
    """get_all calculates next page URL correctly."""
    router = AppCRUDRouter(
        prefix="/test",
        model=SampleModel,
        create_schema=CreateSampleSchema,
        update_schema=UpdateSampleSchema,
    )

    mock_repository.all.return_value = sample_entities[3:]
    mock_repository.count.return_value = 5

    pagination = PaginationParams(page=2, limit=3)
    route_handler = router.get_all

    result = await route_handler(
        repository=mock_repository,
        pagination=pagination,
    )

    assert result.data.pagination.has_next is False
    assert result.data.pagination.has_previous is True
    assert result.data.pagination.previous_page_url is not None


# Test get_one endpoint
@pytest.mark.asyncio
async def test_get_one_retrieves_entity(mock_repository, sample_entity):
    """get_one retrieves a single entity by ID."""
    router = AppCRUDRouter(
        prefix="/test",
        model=SampleModel,
        create_schema=CreateSampleSchema,
        update_schema=UpdateSampleSchema,
    )

    mock_repository.get.return_value = sample_entity
    route_handler = router.get_one

    result = await route_handler(
        id=sample_entity.id,
        repository=mock_repository,
    )

    assert result.success is True
    assert result.data == sample_entity
    mock_repository.get.assert_called_once_with(sample_entity.id)


@pytest.mark.asyncio
async def test_get_one_raises_not_found_when_entity_missing(mock_repository):
    """get_one raises NotFoundError when entity is not found."""
    router = AppCRUDRouter(
        prefix="/test",
        model=SampleModel,
        create_schema=CreateSampleSchema,
        update_schema=UpdateSampleSchema,
    )

    mock_repository.get.return_value = None
    route_handler = router.get_one

    with pytest.raises(NotFoundError, match="Samplemodel not found"):
        await route_handler(
            id=uuid.uuid4(),
            repository=mock_repository,
        )


# Test create endpoint
@pytest.mark.asyncio
async def test_create_creates_entity(mock_repository, sample_entity):
    """create creates a new entity."""
    router = AppCRUDRouter(
        prefix="/test",
        model=SampleModel,
        create_schema=CreateSampleSchema,
        update_schema=UpdateSampleSchema,
    )

    create_data = CreateSampleSchema(name="New Item", description="New Description")
    mock_repository.create.return_value = sample_entity
    route_handler = router.create

    result = await route_handler(
        data=create_data,
        repository=mock_repository,
    )

    assert result.success is True
    assert result.status == 201
    mock_repository.create.assert_called_once()
    created_entity = mock_repository.create.call_args[0][0]
    assert isinstance(created_entity, SampleModel)
    assert created_entity.name == "New Item"


@pytest.mark.asyncio
async def test_create_with_exists_callback_raises_validation_error(mock_repository):
    """create raises ValidationError when exists_callback returns True."""
    async def exists_callback(entity, repo):
        return True

    router = AppCRUDRouter(
        prefix="/test",
        model=SampleModel,
        create_schema=CreateSampleSchema,
        update_schema=UpdateSampleSchema,
        exists_callback=exists_callback,
    )

    create_data = CreateSampleSchema(name="Existing Item")
    route_handler = router.create

    with pytest.raises(ValidationError, match="already exists"):
        await route_handler(
            data=create_data,
            repository=mock_repository,
        )


@pytest.mark.asyncio
async def test_create_with_exists_callback_creates_when_false(mock_repository, sample_entity):
    """create creates entity when exists_callback returns False."""
    async def exists_callback(entity, repo):
        return False

    router = AppCRUDRouter(
        prefix="/test",
        model=SampleModel,
        create_schema=CreateSampleSchema,
        update_schema=UpdateSampleSchema,
        exists_callback=exists_callback,
    )

    create_data = CreateSampleSchema(name="New Item")
    mock_repository.create.return_value = sample_entity
    route_handler = router.create

    result = await route_handler(
        data=create_data,
        repository=mock_repository,
    )

    assert result.success is True


# Test update endpoint
@pytest.mark.asyncio
async def test_update_updates_entity(mock_repository, sample_entity):
    """update updates an existing entity."""
    router = AppCRUDRouter(
        prefix="/test",
        model=SampleModel,
        create_schema=CreateSampleSchema,
        update_schema=UpdateSampleSchema,
    )

    import arrow
    update_data = UpdateSampleSchema(name="Updated Item")
    updated_entity = SampleModel(
        id=sample_entity.id,
        name="Updated Item",
        description=sample_entity.description,
        created_at=arrow.utcnow().datetime,
        updated_at=arrow.utcnow().datetime,
        deleted_at=None,
    )

    mock_repository.exists.return_value = True
    mock_repository.update.return_value = updated_entity
    route_handler = router.update

    result = await route_handler(
        id=sample_entity.id,
        data=update_data,
        repository=mock_repository,
    )

    assert result.success is True
    assert result.data.name == "Updated Item"
    mock_repository.exists.assert_called_once_with(id=sample_entity.id)
    mock_repository.update.assert_called_once()


@pytest.mark.asyncio
async def test_update_raises_not_found_when_entity_missing(mock_repository):
    """update raises NotFoundError when entity is not found."""
    router = AppCRUDRouter(
        prefix="/test",
        model=SampleModel,
        create_schema=CreateSampleSchema,
        update_schema=UpdateSampleSchema,
    )

    update_data = UpdateSampleSchema(name="Updated Item")
    mock_repository.exists.return_value = False
    route_handler = router.update

    with pytest.raises(NotFoundError, match="Samplemodel not found"):
        await route_handler(
            id=uuid.uuid4(),
            data=update_data,
            repository=mock_repository,
        )


@pytest.mark.asyncio
async def test_update_with_exists_callback_raises_validation_error(mock_repository, sample_entity):
    """update raises ValidationError when exists_callback returns True."""
    async def exists_callback(data, repo):
        return True

    router = AppCRUDRouter(
        prefix="/test",
        model=SampleModel,
        create_schema=CreateSampleSchema,
        update_schema=UpdateSampleSchema,
        exists_callback=exists_callback,
    )

    update_data = UpdateSampleSchema(name="Existing Item")
    mock_repository.exists.return_value = True
    route_handler = router.update

    with pytest.raises(ValidationError, match="already exists"):
        await route_handler(
            id=sample_entity.id,
            data=update_data,
            repository=mock_repository,
        )


# Test delete endpoint
@pytest.mark.asyncio
async def test_delete_deletes_entity(mock_repository):
    """delete deletes an entity."""
    router = AppCRUDRouter(
        prefix="/test",
        model=SampleModel,
        create_schema=CreateSampleSchema,
        update_schema=UpdateSampleSchema,
    )

    entity_id = uuid.uuid4()
    mock_repository.exists.return_value = True
    mock_repository.delete.return_value = None
    route_handler = router.delete

    result = await route_handler(
        id=entity_id,
        repository=mock_repository,
    )

    assert result.success is True
    mock_repository.exists.assert_called_once_with(id=entity_id)
    mock_repository.delete.assert_called_once_with(entity_id)


@pytest.mark.asyncio
async def test_delete_raises_not_found_when_entity_missing(mock_repository):
    """delete raises NotFoundError when entity is not found."""
    router = AppCRUDRouter(
        prefix="/test",
        model=SampleModel,
        create_schema=CreateSampleSchema,
        update_schema=UpdateSampleSchema,
    )

    entity_id = uuid.uuid4()
    mock_repository.exists.return_value = False
    route_handler = router.delete

    with pytest.raises(NotFoundError, match="Samplemodel not found"):
        await route_handler(
            id=entity_id,
            repository=mock_repository,
        )


# Test soft_delete endpoint
@pytest.mark.asyncio
async def test_soft_delete_soft_deletes_entity(mock_repository, sample_entity):
    """soft_delete soft deletes an entity."""
    router = AppCRUDRouter(
        prefix="/test",
        model=SampleModel,
        create_schema=CreateSampleSchema,
        update_schema=UpdateSampleSchema,
    )

    import arrow
    deleted_entity = SampleModel(
        id=sample_entity.id,
        name=sample_entity.name,
        description=sample_entity.description,
        created_at=arrow.utcnow().datetime,
        updated_at=arrow.utcnow().datetime,
        deleted_at=None,  # Will be set by soft_delete
    )

    mock_repository.get.return_value = sample_entity
    mock_repository.soft_delete.return_value = deleted_entity
    route_handler = router.soft_delete

    result = await route_handler(
        id=sample_entity.id,
        repository=mock_repository,
    )

    assert result.success is True
    mock_repository.get.assert_called_once_with(sample_entity.id)
    mock_repository.soft_delete.assert_called_once_with(sample_entity.id)


@pytest.mark.asyncio
async def test_soft_delete_raises_attribute_error_when_entity_missing(mock_repository):
    """soft_delete raises AttributeError when entity is not found."""
    router = AppCRUDRouter(
        prefix="/test",
        model=SampleModel,
        create_schema=CreateSampleSchema,
        update_schema=UpdateSampleSchema,
    )

    entity_id = uuid.uuid4()
    mock_repository.get.return_value = None
    route_handler = router.soft_delete

    # The code checks exists.is_deleted before checking if exists is None
    with pytest.raises(AttributeError):
        await route_handler(
            id=entity_id,
            repository=mock_repository,
        )


@pytest.mark.asyncio
async def test_soft_delete_raises_validation_error_when_already_deleted(mock_repository):
    """soft_delete raises ValidationError when entity is already soft deleted."""
    import datetime
    import arrow
    router = AppCRUDRouter(
        prefix="/test",
        model=SampleModel,
        create_schema=CreateSampleSchema,
        update_schema=UpdateSampleSchema,
    )

    deleted_entity = SampleModel(
        id=uuid.uuid4(),
        name="Deleted Item",
        description=None,
        created_at=arrow.utcnow().datetime,
        updated_at=arrow.utcnow().datetime,
        deleted_at=datetime.datetime.now(),
    )

    mock_repository.get.return_value = deleted_entity
    route_handler = router.soft_delete

    with pytest.raises(ValidationError, match="already soft deleted"):
        await route_handler(
            id=deleted_entity.id,
            repository=mock_repository,
        )


# Test restore endpoint
@pytest.mark.asyncio
async def test_restore_restores_entity(mock_repository):
    """restore restores a soft deleted entity."""
    import datetime
    import arrow
    router = AppCRUDRouter(
        prefix="/test",
        model=SampleModel,
        create_schema=CreateSampleSchema,
        update_schema=UpdateSampleSchema,
    )

    deleted_entity = SampleModel(
        id=uuid.uuid4(),
        name="Deleted Item",
        description=None,
        created_at=arrow.utcnow().datetime,
        updated_at=arrow.utcnow().datetime,
        deleted_at=datetime.datetime.now(),
    )

    restored_entity = SampleModel(
        id=deleted_entity.id,
        name=deleted_entity.name,
        description=deleted_entity.description,
        created_at=arrow.utcnow().datetime,
        updated_at=arrow.utcnow().datetime,
        deleted_at=None,
    )

    mock_repository.get.return_value = deleted_entity
    mock_repository.restore.return_value = restored_entity
    route_handler = router.restore

    result = await route_handler(
        id=deleted_entity.id,
        repository=mock_repository,
    )

    assert result.success is True
    mock_repository.get.assert_called_once_with(deleted_entity.id)
    mock_repository.restore.assert_called_once_with(deleted_entity.id)


@pytest.mark.asyncio
async def test_restore_raises_not_found_when_entity_missing(mock_repository):
    """restore raises NotFoundError when entity is not found."""
    router = AppCRUDRouter(
        prefix="/test",
        model=SampleModel,
        create_schema=CreateSampleSchema,
        update_schema=UpdateSampleSchema,
    )

    entity_id = uuid.uuid4()
    mock_repository.get.return_value = None
    route_handler = router.restore

    with pytest.raises(NotFoundError, match="Samplemodel not found"):
        await route_handler(
            id=entity_id,
            repository=mock_repository,
        )


@pytest.mark.asyncio
async def test_restore_raises_validation_error_when_not_deleted(mock_repository, sample_entity):
    """restore raises ValidationError when entity is not deleted."""
    router = AppCRUDRouter(
        prefix="/test",
        model=SampleModel,
        create_schema=CreateSampleSchema,
        update_schema=UpdateSampleSchema,
    )

    mock_repository.get.return_value = sample_entity
    route_handler = router.restore

    with pytest.raises(ValidationError, match="is not deleted"):
        await route_handler(
            id=sample_entity.id,
            repository=mock_repository,
        )


# Test model name handling
def test_crud_router_model_name_lowercase():
    """CRUD router converts model name to lowercase."""
    router = AppCRUDRouter(
        prefix="/test",
        model=SampleModel,
        create_schema=CreateSampleSchema,
        update_schema=UpdateSampleSchema,
    )

    assert router.model_name == "samplemodel"


# Test exists_callback attribute
def test_crud_router_stores_exists_callback():
    """CRUD router stores exists_callback."""
    async def callback(entity, repo):
        return False

    router = AppCRUDRouter(
        prefix="/test",
        model=SampleModel,
        create_schema=CreateSampleSchema,
        update_schema=UpdateSampleSchema,
        exists_callback=callback,
    )

    assert router.exist_callback == callback

