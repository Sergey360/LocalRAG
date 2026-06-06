from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
VALIDATOR_PATH = ROOT_DIR / "scripts" / "validate_observability_setup.py"


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_observability_setup", VALIDATOR_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OpsObservabilityArtifactsTest(unittest.TestCase):
    def test_setup_artifacts_validate_offline(self):
        validator = load_validator()

        report = validator.validate_all(check_gitlab_api=False)

        self.assertTrue(report["ok"], report)


if __name__ == "__main__":
    unittest.main()
