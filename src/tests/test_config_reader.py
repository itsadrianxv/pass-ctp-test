import tempfile
import unittest
from pathlib import Path

from src.config import reader


class ConfigReaderTests(unittest.TestCase):
    def test_save_env_rejects_multiline_values(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"
            env_path.write_text("CTP_NAME=demo\n", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "line breaks"):
                reader.save_env(str(env_path), {"CTP_NAME": "demo\nINJECTED=1"})

            self.assertEqual(env_path.read_text(encoding="utf-8"), "CTP_NAME=demo\n")

    def test_get_web_secret_key_persists_generated_value(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env"

            first = reader.get_web_secret_key(str(env_path))
            second = reader.get_web_secret_key(str(env_path))

            self.assertEqual(first, second)
            self.assertIn(f"WEB_SECRET_KEY={first}", env_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
