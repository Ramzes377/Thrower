from __future__ import annotations

from abc import ABC, abstractmethod


class Specification(ABC):
    column_name: str | None = None

    @abstractmethod
    def __call__(self, *args, **kwargs) -> dict:
        raise NotImplementedError('Specification must be undefined!')

    def __and__(self, other: Specification):
        self_filter: dict = self()
        other_filter: dict = other()
        self_filter.update(other_filter)
        return SpecificationUnion(self_filter)

    def replace_column(self, name):
        self.column_name = name


class SpecificationUnion(Specification):
    def __init__(self, specification: dict):
        self._union = specification

    def __call__(self):
        return self._union


class BaseSpecification(Specification):

    def __init__(self, id: int | str | None = None):
        self._id = id

    def __call__(self, *args, **kwargs):
        return {self.column_name: self._id}


def auto_increment(func):
    setattr(func, 'counter', 0)

    def wrap(column: str | dict):
        func.counter += 1
        return func(column, counter=func.counter)

    return wrap


@auto_increment
def specification_fabric(column: str | None = None, counter: int | None = None):
    return type(
        f'Specification_#{counter}',
        (BaseSpecification,),
        {'column_name': column}
    )
