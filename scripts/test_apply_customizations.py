import json
import os
import re
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from scripts.apply_customizations import main


class ApplyCustomizationsTest(unittest.TestCase):
    def test_server_settings_are_hidden_without_exposing_fixed_values(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config_rs = root / "libs" / "hbb_common" / "src" / "config.rs"
            config_rs.parent.mkdir(parents=True)
            (root / "config.json").write_text(
                json.dumps(
                    {
                        "app_name": "SampleDesk",
                        "server_ip": "server.example",
                        "server_key": "SamplePublicKey",
                    }
                ),
                encoding="utf-8",
            )
            config_rs.write_text(
                "\n".join(
                    [
                        'pub const RENDEZVOUS_SERVERS: &[&str] = &["default.example"];',
                        'pub const RS_PUB_KEY: &str = "DefaultKey";',
                        'pub static ref APP_NAME: RwLock<String> = RwLock::new("RustDesk".to_owned());',
                        "pub static ref OVERWRITE_SETTINGS: RwLock<HashMap<String, String>> = Default::default();",
                        "pub static ref BUILTIN_SETTINGS: RwLock<HashMap<String, String>> = Default::default();",
                    ]
                ),
                encoding="utf-8",
            )

            previous_dir = Path.cwd()
            output = StringIO()
            try:
                os.chdir(root)
                with redirect_stdout(output):
                    main()
            finally:
                os.chdir(previous_dir)

            generated = config_rs.read_text(encoding="utf-8")
            overwrite = re.search(
                r"pub static ref OVERWRITE_SETTINGS:.*?\n    };",
                generated,
                re.DOTALL,
            )
            builtin = re.search(
                r"pub static ref BUILTIN_SETTINGS:.*?\n    };",
                generated,
                re.DOTALL,
            )

            self.assertIsNotNone(overwrite)
            self.assertIsNotNone(builtin)
            self.assertNotIn("hide-server-settings", overwrite.group())
            self.assertIn("custom-rendezvous-server", overwrite.group())
            self.assertIn("SamplePublicKey", overwrite.group())
            self.assertIn("hide-server-settings", builtin.group())
            self.assertNotIn("server.example", output.getvalue())
            self.assertNotIn("SamplePublicKey", output.getvalue())


if __name__ == "__main__":
    unittest.main()
