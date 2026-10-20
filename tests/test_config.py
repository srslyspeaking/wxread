import unittest

import config


class ReadingDurationTests(unittest.TestCase):
    def test_maximum_duration_is_180_minutes(self):
        self.assertEqual(config.read_count_from_env({"READ_MINUTES": "180"}), 360)
        with self.assertRaises(ValueError):
            config.read_count_from_env({"READ_MINUTES": "181"})

    def test_legacy_read_count_uses_the_same_limit(self):
        self.assertEqual(config.read_count_from_env({"READ_NUM": "360"}), 360)
        with self.assertRaises(ValueError):
            config.read_count_from_env({"READ_NUM": "361"})


if __name__ == "__main__":
    unittest.main()
