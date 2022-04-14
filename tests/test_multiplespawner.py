import unittest


class DummyTest(unittest.TestCase):
    def setUp(self) -> None:
        return super().setUp()

    def tearDown(self) -> None:
        return super().tearDown()

    def test_hello(self):
        self.assertTrue(True)
