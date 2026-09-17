import os
import subprocess
import tempfile
from pathlib import Path


with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    (root / ".config/codex-model").mkdir(parents=True)
    (root / ".config/codex-model/zai.key").write_text("test-key\n")
    fake_codex = root / "codex"
    fake_codex.write_text("#!/bin/sh\nprintf '%s\\n' \"$ZAI_API_KEY\" \"$@\"\n")
    fake_codex.chmod(0o755)
    env = {**os.environ, "HOME": directory, "PATH": f"{directory}:{os.environ['PATH']}"}
    wrapper = Path(__file__).with_name("codex-model")
    result = subprocess.run(
        [wrapper, "z.ai/GLM-5.3-Flash", "--yolo"],
        env=env, text=True, capture_output=True, check=True,
    )
    lines = result.stdout.splitlines()
    assert lines[0] == "test-key"
    assert lines[-3:] == ["-m", "glm-5.3-flash", "--yolo"]
    assert 'model_provider="zai"' in lines
    assert 'model_providers.zai.base_url="https://api.z.ai/api/v1"' in lines
    result = subprocess.run(
        [wrapper, "gpt-5.6-sol", "--version"],
        env=env, text=True, capture_output=True, check=True,
    )
    assert result.stdout.splitlines() == ["", "-m", "gpt-5.6-sol", "--version"]

print("codex-model wrapper OK")
