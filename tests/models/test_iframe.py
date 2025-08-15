import unittest

from app.models.iframe import Iframe


class TestIframe(unittest.TestCase):
    def test_iframe_sets_src(self):
        widget = {"src": "http://example", "name": "iframe1"}
        iframe = Iframe(widget)
        self.assertEqual(iframe.src, "http://example")


if __name__ == "__main__":
    unittest.main()
