import datetime
import uuid
from typing import Literal, Any, Callable, Optional

import arrow
from pydantic import BaseModel as PydanticBaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from pydantic.main import IncEx
from sqlalchemy import Column, DateTime
from sqlmodel import SQLModel, Field


class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, extra="ignore"
    )

    def model_dump(
        self,
        *,
        mode: Literal["json", "python"] | str = "python",
        include: IncEx | None = None,
        exclude: IncEx | None = None,
        context: Any | None = None,
        by_alias: bool | None = True,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = True,
        exclude_computed_fields: bool = False,
        round_trip: bool = False,
        warnings: bool | Literal["none", "warn", "error"] = True,
        fallback: Callable[[Any], Any] | None = None,
        serialize_as_any: bool = False,
    ) -> dict[str, Any]:
        return super().model_dump(
            mode=mode,
            include=include,
            exclude=exclude,
            context=context,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            exclude_computed_fields=exclude_computed_fields,
            round_trip=round_trip,
            warnings=warnings,
            fallback=fallback,
            serialize_as_any=serialize_as_any,
        )

    def model_dump_json(
        self,
        *,
        indent: int | None = None,
        ensure_ascii: bool = False,
        include: IncEx | None = None,
        exclude: IncEx | None = None,
        context: Any | None = None,
        by_alias: bool | None = True,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = True,
        exclude_computed_fields: bool = False,
        round_trip: bool = False,
        warnings: bool | Literal["none", "warn", "error"] = True,
        fallback: Callable[[Any], Any] | None = None,
        serialize_as_any: bool = False,
    ) -> str:
        return super().model_dump_json(
            indent=indent,
            ensure_ascii=ensure_ascii,
            include=include,
            exclude=exclude,
            context=context,
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            exclude_computed_fields=exclude_computed_fields,
            round_trip=round_trip,
            warnings=warnings,
            fallback=fallback,
            serialize_as_any=serialize_as_any,
        )


class BaseDBModel(SQLModel, BaseModel, table=False):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime.datetime
    updated_at: datetime.datetime
    deleted_at: Optional[datetime.datetime]

    # Workaround on inheriting to add timestamp fields automatically as sqlalchemy does not allow Column being assigned
    # to more than one model class
    def __init_subclass__(cls, **kwargs):
        if cls.__name__ == "BaseDBModel":
            super().__init_subclass__(**kwargs)
            return

        cls.created_at = Field(
            default_factory=lambda: arrow.utcnow().datetime,
            sa_column=Column(DateTime(timezone=True)),
        )
        cls.updated_at = Field(
            default_factory=lambda: arrow.utcnow().datetime,
            sa_column=Column(
                DateTime(timezone=True), onupdate=lambda: arrow.utcnow().datetime
            ),
        )
        cls.deleted_at = Field(default=None, sa_column=Column(DateTime(timezone=True)))

        super().__init_subclass__(**kwargs)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
