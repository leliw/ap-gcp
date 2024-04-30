from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Iterator, Type, TypeVar, Generic

T = TypeVar("T", bound=BaseModel)


class BaseStorage(ABC, Generic[T]):
    def __init__(self, clazz: Type[T], key_name: str = None):
        self.clazz = clazz
        self.key_name = key_name if key_name else "id"

    @abstractmethod
    def put(self, key: str, value: T) -> None:
        pass

    def save(self, value: T) -> None:
        key = getattr(value, self.key_name)
        self.put(key, value)
        
    @abstractmethod
    def get(self, key: str) -> T:
        pass

    @abstractmethod
    def keys(self) -> Iterator[T] | list[T]:
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        pass

    def drop(self) -> None:
        for key in self.keys():
            self.delete(key)

    def get_all(self) -> Iterator[T] | list[T]:
        for key in self.keys():
            yield self.get(key)
