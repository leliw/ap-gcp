"""A simple wrapper around Google Cloud Firestore."""

from typing import Generic, Iterator, Type
from google.cloud import firestore

from storage import T, BaseStorage


class Storage(BaseStorage[T], Generic[T]):
    """A simple wrapper around Google Cloud Firestore."""

    def __init__(
        self, collection: str, clazz: Type[T], project: str = None, database: str = None
    ):
        super().__init__(clazz)
        self._db = firestore.Client(project=project, database=database)
        self._collection = collection
        self._coll_ref = self._db.collection(self._collection)

    def put(self, key: str, data: T) -> None:
        """Put a document in the collection."""
        print(data)
        self._coll_ref.document(key).set(
            data.model_dump(by_alias=True, exclude_none=True)
        )

    def get(self, key: str) -> T:
        """Get a document from the collection."""
        return self.clazz.model_validate(self._coll_ref.document(key).get().to_dict())

    def get_all(self) -> Iterator[T]:
        """Get all documents from the collection."""
        for doc in self._coll_ref.stream():
            yield self.clazz.model_validate(doc.to_dict())

    def keys(self) -> Iterator[str]:
        """Return a list of keys in the collection."""
        for doc in self._coll_ref.stream():
            yield doc.id

    def delete(self, key: str) -> None:
        """Delete a document from the collection."""
        self._coll_ref.document(key).delete()

    def drop(self) -> None:
        """Delete all documents from the collection."""
        for doc in self._coll_ref.stream():
            doc.reference.delete()
