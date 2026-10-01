from __future__ import annotations

import argparse
import hashlib
import os
import stat
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path


BUNDLE_NAME = "CustomerDNA_VM3"
SCRIPT_PATH = Path(__file__).resolve()
SOURCE_DIR = SCRIPT_PATH.parent
DIST_DIR = SOURCE_DIR / "dist"
ZIP_PATH = DIST_DIR / f"{BUNDLE_NAME}.zip"

EXCLUDED_NAMES = {
    "dist",
    "runtime",
    "__pycache__",
    ".git",
    ".venv",
}
EXCLUDED_SUFFIXES = {
    ".pyc",
}


class BundleError(RuntimeError):
    """Raised when the bundle workflow cannot continue."""


@dataclass(frozen=True)
class BundleFile:
    source: Path
    relative_path: Path


CURRENT_STAGING_DIR: Path | None = None


class ProgressBar:
    def __init__(self, *, total: int, prefix: str) -> None:
        self.total = max(total, 1)
        self.prefix = prefix
        self.current = 0
        self.started_at = time.perf_counter()

    def update(self, message: str) -> None:
        self.current += 1
        ratio = min(self.current / self.total, 1.0)
        width = 32
        filled = int(width * ratio)
        bar = "#" * filled + "-" * (width - filled)
        elapsed = time.perf_counter() - self.started_at
        line = (
            f"[{self.prefix}] [{bar}] {self.current}/{self.total} "
            f"({ratio * 100:5.1f}%) | {elapsed:5.1f}s | {message}"
        )
        print(line)


def info(message: str) -> None:
    print(f"[INFO] {message}")


def success(message: str) -> None:
    print(f"[OK] {message}")


def warn(message: str) -> None:
    print(f"[WARN] {message}")


def fail(message: str) -> None:
    raise BundleError(message)


def run_command(command: list[str], *, cwd: Path | None = None, label: str) -> None:
    info(label)
    completed = subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        text=True,
    )
    if completed.returncode != 0:
        fail(f"Command failed with exit code {completed.returncode}: {' '.join(command)}")


def collect_bundle_files() -> list[BundleFile]:
    files: list[BundleFile] = []

    for path in sorted(SOURCE_DIR.rglob("*")):
        if not path.is_file():
            continue

        relative_path = path.relative_to(SOURCE_DIR)
        parts = set(relative_path.parts)
        if parts & EXCLUDED_NAMES:
            continue
        if path.suffix in EXCLUDED_SUFFIXES:
            continue

        files.append(BundleFile(source=path, relative_path=relative_path))

    return files


def _handle_remove_readonly(func: object, path: str, _: object) -> None:
    os.chmod(path, stat.S_IWRITE)
    func(path)


def remove_tree_with_retries(path: Path, *, retries: int = 8, delay_seconds: float = 0.75) -> None:
    if not path.exists():
        return

    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            shutil.rmtree(path, onerror=_handle_remove_readonly)
            return
        except FileNotFoundError:
            return
        except PermissionError as exc:
            last_error = exc
            if attempt < retries:
                warn(
                    f"Cleanup retry {attempt}/{retries} for {path.name} because a file is still locked. "
                    f"Waiting {delay_seconds:.2f}s."
                )
                time.sleep(delay_seconds)
                continue
            break
        except OSError as exc:
            last_error = exc
            if attempt < retries:
                warn(
                    f"Cleanup retry {attempt}/{retries} for {path.name} after OS error: {exc}. "
                    f"Waiting {delay_seconds:.2f}s."
                )
                time.sleep(delay_seconds)
                continue
            break

    fail(
        f"Could not remove '{path}'. A file is likely still open in Explorer, an editor, "
        f"or another process. Close anything using the dist folder and retry. Last error: {last_error}"
    )


def remove_file_with_retries(path: Path, *, retries: int = 8, delay_seconds: float = 0.5) -> None:
    if not path.exists():
        return

    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            path.unlink()
            return
        except FileNotFoundError:
            return
        except PermissionError as exc:
            last_error = exc
            if attempt < retries:
                warn(
                    f"Delete retry {attempt}/{retries} for {path.name} because it is still locked. "
                    f"Waiting {delay_seconds:.2f}s."
                )
                time.sleep(delay_seconds)
                continue
            break
        except OSError as exc:
            last_error = exc
            if attempt < retries:
                warn(
                    f"Delete retry {attempt}/{retries} for {path.name} after OS error: {exc}. "
                    f"Waiting {delay_seconds:.2f}s."
                )
                time.sleep(delay_seconds)
                continue
            break

    fail(
        f"Could not delete '{path}'. A file is likely still open in another process. "
        f"Close anything using it and retry. Last error: {last_error}"
    )


def clean_dist() -> None:
    DIST_DIR.mkdir(parents=True, exist_ok=True)


def create_staging_dir() -> Path:
    global CURRENT_STAGING_DIR

    clean_dist()
    staging_path = Path(
        tempfile.mkdtemp(
            prefix=f"{BUNDLE_NAME}_staging_",
        )
    )
    CURRENT_STAGING_DIR = staging_path
    return staging_path


def best_effort_remove_tree(path: Path) -> None:
    if not path.exists():
        return

    try:
        shutil.rmtree(path, onerror=_handle_remove_readonly)
    except OSError as exc:
        warn(f"Could not remove temporary staging folder {path.name}: {exc}")


def current_staging_dir() -> Path | None:
    if CURRENT_STAGING_DIR and CURRENT_STAGING_DIR.exists():
        return CURRENT_STAGING_DIR

    candidates = sorted(
        (
            path
            for path in DIST_DIR.glob(f"{BUNDLE_NAME}_staging_*")
            if path.is_dir()
        ),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def ensure_ssh_tool(name: str) -> None:
    if shutil.which(name) is None:
        fail(f"Required tool '{name}' is not available on PATH.")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(bundle_files: list[BundleFile], *, staging_dir: Path) -> None:
    manifest_path = staging_dir / "BUNDLE_MANIFEST.txt"
    lines = [
        f"bundle_name={BUNDLE_NAME}",
        f"generated_at={time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "files:",
    ]

    for bundle_file in bundle_files:
        target = staging_dir / bundle_file.relative_path
        lines.append(
            f"{bundle_file.relative_path.as_posix()} | size={target.stat().st_size} | sha256={sha256_file(target)}"
        )

    manifest_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_bundle() -> Path:
    info(f"Building {BUNDLE_NAME} under {DIST_DIR}")
    staging_dir = create_staging_dir()

    bundle_files = collect_bundle_files()
    if not bundle_files:
        fail("No bundle files were collected.")

    progress = ProgressBar(total=len(bundle_files) + 1, prefix="BUILD")

    for bundle_file in bundle_files:
        destination = staging_dir / bundle_file.relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(bundle_file.source, destination)
        progress.update(f"Copied {bundle_file.relative_path.as_posix()}")

    write_manifest(bundle_files, staging_dir=staging_dir)
    progress.update("Generated bundle manifest")

    success(f"Bundle staging completed: {staging_dir}")
    return staging_dir


def create_zip() -> Path:
    staging_dir = CURRENT_STAGING_DIR if CURRENT_STAGING_DIR and CURRENT_STAGING_DIR.exists() else build_bundle()

    if ZIP_PATH.exists():
        remove_file_with_retries(ZIP_PATH)

    files = sorted(path for path in staging_dir.rglob("*") if path.is_file())
    progress = ProgressBar(total=len(files), prefix="ZIP")

    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in files:
            archive.write(file_path, Path(BUNDLE_NAME) / file_path.relative_to(staging_dir))
            progress.update(f"Archived {file_path.relative_to(staging_dir).as_posix()}")

    success(f"Zip archive created: {ZIP_PATH}")
    best_effort_remove_tree(staging_dir)
    return ZIP_PATH


def remote_bundle_dir(remote_root: str) -> str:
    return f"{remote_root.rstrip('/')}/{BUNDLE_NAME}"


def resolve_remote_root(*, host: str, user: str, remote_root: str, port: int) -> str:
    ensure_ssh_tool("ssh")

    if remote_root.startswith("~/"):
        remote_root = "${HOME}/" + remote_root[2:]
    elif remote_root == "~":
        remote_root = "${HOME}"

    command = ssh_command(
        host=host,
        user=user,
        remote_command=f"printf '%s' {remote_root}",
        port=port,
    )
    completed = subprocess.run(
        command,
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.strip() or "unknown SSH error"
        fail(f"Could not resolve remote path '{remote_root}' on {user}@{host}: {stderr}")

    resolved = completed.stdout.strip()
    if not resolved:
        fail(f"Remote path '{remote_root}' resolved to an empty value on {user}@{host}.")

    return resolved.rstrip("/")


def ssh_command(
    *,
    host: str,
    user: str,
    remote_command: str,
    port: int,
) -> list[str]:
    return [
        "ssh",
        "-p",
        str(port),
        f"{user}@{host}",
        remote_command,
    ]


def scp_command(
    *,
    host: str,
    user: str,
    local_path: Path,
    remote_path: str,
    port: int,
) -> list[str]:
    return [
        "scp",
        "-P",
        str(port),
        str(local_path),
        f"{user}@{host}:{remote_path}",
    ]


def upload_bundle(*, host: str, user: str, remote_root: str, port: int) -> None:
    ensure_ssh_tool("ssh")
    ensure_ssh_tool("scp")
    if not ZIP_PATH.exists():
        create_zip()

    remote_root_clean = resolve_remote_root(
        host=host,
        user=user,
        remote_root=remote_root,
        port=port,
    )
    run_command(
        ssh_command(
            host=host,
            user=user,
            remote_command=f"mkdir -p '{remote_root_clean}'",
            port=port,
        ),
        label=f"Ensuring remote directory exists on {user}@{host}:{remote_root_clean}",
    )

    remote_zip_path = f"{remote_root_clean}/{ZIP_PATH.name}"
    run_command(
        scp_command(
            host=host,
            user=user,
            local_path=ZIP_PATH,
            remote_path=remote_zip_path,
            port=port,
        ),
        label=f"Uploading {ZIP_PATH.name} to {user}@{host}:{remote_zip_path}",
    )
    success("Upload completed")


def extract_bundle(*, host: str, user: str, remote_root: str, port: int) -> None:
    ensure_ssh_tool("ssh")

    remote_root_clean = resolve_remote_root(
        host=host,
        user=user,
        remote_root=remote_root,
        port=port,
    )
    remote_zip_path = f"{remote_root_clean}/{ZIP_PATH.name}"
    remote_bundle_path = remote_bundle_dir(remote_root_clean)

    remote_script = f"""
set -euo pipefail
mkdir -p '{remote_root_clean}'
rm -rf '{remote_bundle_path}'
python3 - <<'PY'
from pathlib import Path
import shutil
import zipfile

remote_root = Path(r"{remote_root_clean}")
zip_path = Path(r"{remote_zip_path}")
bundle_dir = Path(r"{remote_bundle_path}")

if not zip_path.exists():
    raise SystemExit(f"Missing uploaded zip: {{zip_path}}")

extract_root = remote_root / "_extract_tmp_vm3"
if extract_root.exists():
    shutil.rmtree(extract_root)
extract_root.mkdir(parents=True, exist_ok=True)

with zipfile.ZipFile(zip_path, "r") as archive:
    archive.extractall(extract_root)

source_bundle = extract_root / "{BUNDLE_NAME}"
if not source_bundle.exists():
    raise SystemExit(f"Archive does not contain expected root folder: {{source_bundle}}")

shutil.move(str(source_bundle), str(bundle_dir))
shutil.rmtree(extract_root)
zip_path.unlink()
print(bundle_dir)
PY
"""

    run_command(
        ssh_command(
            host=host,
            user=user,
            remote_command=remote_script,
            port=port,
        ),
        label=f"Extracting bundle on {user}@{host}:{remote_bundle_path}",
    )
    success("Remote extraction completed and uploaded zip removed")


def run_all(*, host: str, user: str, remote_root: str, port: int) -> None:
    build_bundle()
    create_zip()
    upload_bundle(host=host, user=user, remote_root=remote_root, port=port)
    extract_bundle(host=host, user=user, remote_root=remote_root, port=port)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build, zip, upload, and extract the isolated CustomerDNA VM3 bundle.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("build", "zip"):
        subparsers.add_parser(name)

    remote_commands = ("upload", "extract", "all")
    for name in remote_commands:
        subparser = subparsers.add_parser(name)
        subparser.add_argument("--host", required=True, help="Remote VM hostname or IP.")
        subparser.add_argument("--user", required=True, help="Remote SSH username.")
        subparser.add_argument(
            "--remote-root",
            default="~/deployments",
            help="Remote parent directory where the bundle zip and extracted folder will live.",
        )
        subparser.add_argument(
            "--port",
            type=int,
            default=22,
            help="Remote SSH port. Default: 22.",
        )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        if args.command == "build":
            build_bundle()
        elif args.command == "zip":
            create_zip()
        elif args.command == "upload":
            upload_bundle(
                host=args.host,
                user=args.user,
                remote_root=args.remote_root,
                port=args.port,
            )
        elif args.command == "extract":
            extract_bundle(
                host=args.host,
                user=args.user,
                remote_root=args.remote_root,
                port=args.port,
            )
        elif args.command == "all":
            run_all(
                host=args.host,
                user=args.user,
                remote_root=args.remote_root,
                port=args.port,
            )
        else:
            fail(f"Unsupported command: {args.command}")
    except BundleError as exc:
        print(f"[ERROR] {exc}")
        return 1
    except KeyboardInterrupt:
        print("[ERROR] Operation cancelled by user.")
        return 130

    return 0


if __name__ == "__main__":
    sys.exit(main())
