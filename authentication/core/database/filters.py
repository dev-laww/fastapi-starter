"""
Filter utility functions for repository queries.

This module provides utility functions to create filter conditions
for use with Repository methods like all(), exists(), and count().

Example usage:
    from authentication.core.base.filters import gt, ilike, in_

    # Using filter functions
    await repo.all(
        expires_at=gt(datetime.now()),
        token=ilike("%abc%"),
        user_id=in_([uuid1, uuid2])
    )
"""

from abc import ABC, abstractmethod
from numbers import Number
from typing import Any, List, Tuple, Union

from sqlalchemy import Column


class Filter(ABC):
    """Base class for all filter conditions."""

    @abstractmethod
    def apply(self, field: Column) -> Any:
        """
        Applies the filter condition to a SQLAlchemy field.

        :param field: The SQLAlchemy field to apply the filter to.
        :return: A SQLAlchemy condition expression.
        """
        pass


class GreaterThan(Filter):
    """Filter for greater than comparison."""

    def __init__(self, value: Number):
        self.value = value

    def apply(self, field: Column) -> Any:
        return field > self.value


class GreaterThanOrEqual(Filter):
    """Filter for greater than or equal comparison."""

    def __init__(self, value: Number):
        self.value = value

    def apply(self, field: Column) -> Any:
        return field >= self.value


class LessThan(Filter):
    """Filter for less than comparison."""

    def __init__(self, value: Number):
        self.value = value

    def apply(self, field: Column) -> Any:
        return field < self.value


class LessThanOrEqual(Filter):
    """Filter for less than or equal comparison."""

    def __init__(self, value: Number):
        self.value = value

    def apply(self, field: Column) -> Any:
        return field <= self.value


class NotEqual(Filter):
    """Filter for not equal comparison."""

    def __init__(self, value: Any):
        self.value = value

    def apply(self, field: Column) -> Any:
        return field != self.value


class Like(Filter):
    """Filter for SQL LIKE pattern matching (case-sensitive)."""

    def __init__(self, pattern: str):
        self.pattern = pattern

    def apply(self, field: Column) -> Any:
        return field.like(self.pattern)


class ILike(Filter):
    """Filter for SQL ILIKE pattern matching (case-insensitive)."""

    def __init__(self, pattern: str):
        self.pattern = pattern

    def apply(self, field: Column) -> Any:
        return field.ilike(self.pattern)


class In(Filter):
    """Filter for IN clause."""

    def __init__(self, values: Union[List[Any], Tuple[Any, ...]]):
        if not isinstance(values, (list, tuple)):
            raise ValueError(f"In filter requires a list or tuple, got {type(values)}")
        self.values = values

    def apply(self, field: Column) -> Any:
        return field.in_(self.values)


class NotIn(Filter):
    """Filter for NOT IN clause."""

    def __init__(self, values: Union[List[Any], Tuple[Any, ...]]):
        if not isinstance(values, (list, tuple)):
            raise ValueError(
                f"NotIn filter requires a list or tuple, got {type(values)}"
            )
        self.values = values

    def apply(self, field: Column) -> Any:
        return ~field.in_(self.values)


class IsNull(Filter):
    """Filter for IS NULL condition."""

    def apply(self, field: Column) -> Any:
        return field.is_(None)


class IsNotNull(Filter):
    """Filter for IS NOT NULL condition."""

    def apply(self, field: Column) -> Any:
        return field.is_not(None)


# Utility functions for creating filters
def gt(value: Any) -> GreaterThan:
    """
    Creates a greater than filter.

    :param value: The value to compare against.
    :return: A GreaterThan filter instance.
    """
    return GreaterThan(value)


def gte(value: Any) -> GreaterThanOrEqual:
    """
    Creates a greater than or equal filter.

    :param value: The value to compare against.
    :return: A GreaterThanOrEqual filter instance.
    """
    return GreaterThanOrEqual(value)


def lt(value: Any) -> LessThan:
    """
    Creates a less than filter.

    :param value: The value to compare against.
    :return: A LessThan filter instance.
    """
    return LessThan(value)


def lte(value: Any) -> LessThanOrEqual:
    """
    Creates a less than or equal filter.

    :param value: The value to compare against.
    :return: A LessThanOrEqual filter instance.
    """
    return LessThanOrEqual(value)


def ne(value: Any) -> NotEqual:
    """
    Creates a not equal filter.

    :param value: The value to compare against.
    :return: A NotEqual filter instance.
    """
    return NotEqual(value)


def like(pattern: str) -> Like:
    """
    Creates a LIKE filter (case-sensitive pattern matching).

    :param pattern: The pattern to match (supports % and _ wildcards).
    :return: A Like filter instance.
    """
    return Like(pattern)


def ilike(pattern: str) -> ILike:
    """
    Creates an ILIKE filter (case-insensitive pattern matching).

    :param pattern: The pattern to match (supports % and _ wildcards).
    :return: An ILike filter instance.
    """
    return ILike(pattern)


def in_array(values: Union[List[Any], Tuple[Any, ...]]) -> In:
    """
    Creates an IN filter.

    :param values: A list or tuple of values to match against.
    :return: An In filter instance.
    """
    return In(values)


def not_in_array(values: Union[List[Any], Tuple[Any, ...]]) -> NotIn:
    """
    Creates a NOT IN filter.

    :param values: A list or tuple of values to exclude.
    :return: A NotIn filter instance.
    """
    return NotIn(values)


def is_null() -> IsNull:
    """
    Creates an IS NULL filter.

    :return: An IsNull filter instance.
    """
    return IsNull()


def is_not_null() -> IsNotNull:
    """
    Creates an IS NOT NULL filter.

    :return: An IsNotNull filter instance.
    """
    return IsNotNull()


__all__ = [
    "Filter",
    "GreaterThan",
    "GreaterThanOrEqual",
    "LessThan",
    "LessThanOrEqual",
    "NotEqual",
    "Like",
    "ILike",
    "In",
    "NotIn",
    "IsNull",
    "IsNotNull",
    "gt",
    "gte",
    "lt",
    "lte",
    "ne",
    "like",
    "ilike",
    "in_array",
    "not_in_array",
    "is_null",
    "is_not_null",
]
