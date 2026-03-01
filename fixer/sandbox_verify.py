"""
Sandbox verify: use Daytona credits to spin up an environment and verify the code builds before pushing the PR.
"""

import os
from typing import Optional

try:
    from daytona import Daytona, CreateSandboxFromSnapshotParams
    _DAYTONA_AVAILABLE = True
except ImportError:
    _DAYTONA_AVAILABLE = False


def _get_daytona():
    if not _DAYTONA_AVAILABLE:
        raise RuntimeError("daytona SDK is not installed. pip install daytona")
    # Daytona uses DAYTONA_API_KEY from env by default
    if not os.environ.get("DAYTONA_API_KEY"):
        raise RuntimeError("Set DAYTONA_API_KEY for sandbox verification.")
    return Daytona()


def verify_build(
    repo_url: str,
    build_command: str = "npm ci && npm run build",
    patched_file_path: Optional[str] = None,
    patched_content: Optional[str] = None,
    branch: str = "main",
    timeout_seconds: int = 300,
) -> tuple[bool, str]:
    """
    Spin up a Daytona sandbox, clone the repo, optionally apply a patched file, run the build.
    Returns (success, message) where message is build stdout/stderr or error description.
    """
    daytona = _get_daytona()
    sandbox = None
    try:
        # Use a snapshot that has Node/npm for typical frontend builds; default snapshot is often Python
        params = CreateSandboxFromSnapshotParams(
            language="typescript",  # Node/npm available in TS snapshot
            auto_stop_interval=10,
        )
        sandbox = daytona.create(params)
        sandbox.start(timeout=60)
        work_dir = sandbox.get_work_dir()

        # Clone repo (use branch)
        clone_cmd = f"git clone --depth 1 --branch {branch} {repo_url} repo"
        r = sandbox.process.exec(clone_cmd, cwd=work_dir, timeout=120)
        if r.exit_code != 0:
            return False, f"Clone failed: {r.result or r.artifacts.stdout if r.artifacts else 'no output'}"

        repo_dir = "repo"
        if patched_file_path and patched_content:
            # Remote path relative to sandbox working directory
            remote_path = f"{repo_dir}/{patched_file_path}".replace("\\", "/")
            parts = patched_file_path.replace("\\", "/").split("/")[:-1]
            if parts:
                d = "/".join([repo_dir] + parts)
                sandbox.process.exec(f"mkdir -p {d}", cwd=work_dir, timeout=10)
            # upload_file(file: bytes, remote_path: str)
            sandbox.fs.upload_file(patched_content.encode("utf-8"), remote_path)

        # Run build
        build_r = sandbox.process.exec(
            build_command,
            cwd=f"{work_dir}/{repo_dir}",
            timeout=timeout_seconds,
        )
        out = (build_r.artifacts.stdout if build_r.artifacts else build_r.result) or ""
        combined = out.strip() or f"exit_code={build_r.exit_code}"
        success = build_r.exit_code == 0
        return success, combined
    except Exception as e:
        return False, str(e)
    finally:
        if sandbox is not None:
            try:
                sandbox.stop(timeout=30)
                sandbox.delete(timeout=30)
            except Exception:
                pass
