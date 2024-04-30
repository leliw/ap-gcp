import unittest

from pydantic import BaseModel

from gcp_storage import Storage


class TC(BaseModel):
    name: str


class TestStorage(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.storage = Storage("unit tests", TC)

    def test_storage(self):
        self.storage.put("1", TC(name="test"))
        self.assertEqual(self.storage.get("1"), TC(name="test"))
        self.assertEqual(list(self.storage.keys()), ["1"])
        self.assertEqual(list(self.storage.get_all()), [TC(name="test")])
        self.storage.delete("1")
        self.assertEqual(list(self.storage.keys()), [])
        self.storage.put("2", TC(name="test2"))
        self.storage.put("3", TC(name="test3"))
        self.storage.drop()
        self.assertEqual(list(self.storage.keys()), [])


if __name__ == "__main__":
    unittest.main()
