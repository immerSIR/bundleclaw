from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import time
import zipfile
from pathlib import Path

import typer

app = typer.Typer(help="OpenClaw state migration tool")
ENC_MAGIC = b"BCLAWENC1"

CORE_WORKSPACE_FILES = [
    "AGENTS.md",
    "SOUL.md",
    "USER.md",
    "TOOLS.md",
    "IDENTITY.md",
    "MEMORY.md",
    "HEARTBEAT.md",
]


def copy_if_exists(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        shutil.copy2(src, dst)


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return f"sha256:{h.hexdigest()}"


def _crypto():
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC  # type: ignore
        from cryptography.hazmat.primitives import hashes  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError("Encryption requested, install dependency: pip install cryptography") from e
    return AESGCM, PBKDF2HMAC, hashes


def encrypt_bytes(data: bytes, passphrase: str) -> bytes:
    AESGCM, PBKDF2HMAC, hashes = _crypto()
    salt = os.urandom(16)
    iv = os.urandom(12)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=200_000)
    key = kdf.derive(passphrase.encode("utf-8"))
    cipher = AESGCM(key)
    encrypted = cipher.encrypt(iv, data, associated_data=None)
    # cryptography AESGCM output = ciphertext || 16-byte tag
    ciphertext, tag = encrypted[:-16], encrypted[-16:]
    return ENC_MAGIC + salt + iv + tag + ciphertext


def decrypt_bytes(data: bytes, passphrase: str) -> bytes:
    if not data.startswith(ENC_MAGIC):
        return data
    AESGCM, PBKDF2HMAC, hashes = _crypto()
    salt = data[len(ENC_MAGIC): len(ENC_MAGIC) + 16]
    iv = data[len(ENC_MAGIC) + 16: len(ENC_MAGIC) + 28]
    tag = data[len(ENC_MAGIC) + 28: len(ENC_MAGIC) + 44]
    ciphertext = data[len(ENC_MAGIC) + 44:]
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=200_000)
    key = kdf.derive(passphrase.encode("utf-8"))
    cipher = AESGCM(key)
    return cipher.decrypt(iv, ciphertext + tag, associated_data=None)


@app.command("export")
def export_cmd(
    source: Path = typer.Option(..., help="OpenClaw home path"),
    workspace: Path = typer.Option(..., help="Workspace path"),
    out: Path = typer.Option(..., help="Output .bcz path"),
    profile: str = typer.Option("full", help="full|memory-only|no-credentials"),
    encrypt_pass: str | None = typer.Option(None, "--encrypt-pass", help="Encrypt output bundle with passphrase"),
):
    source = source.expanduser().resolve()
    workspace = workspace.expanduser().resolve()
    out = out.expanduser().resolve()

    tmp = Path.cwd() / f"bundleclaw-export-{int(time.time())}"
    payload = tmp / "payload"
    payload.mkdir(parents=True, exist_ok=True)

    if profile not in {"full", "memory-only", "no-credentials"}:
        raise typer.BadParameter("profile must be one of: full, memory-only, no-credentials")

    include_openclaw = profile != "memory-only"
    include_credentials = profile == "full"
    include_identity = profile == "full"
    include_workspace_core = True
    include_workspace_memory = True
    include_workspace_config = profile != "memory-only"

    if include_openclaw:
        copy_if_exists(source / "openclaw.json", payload / "openclaw.json")
    if include_credentials:
        copy_if_exists(source / "credentials", payload / "credentials")
    if include_identity:
        copy_if_exists(source / "identity", payload / "identity")

    ws_dst = payload / "workspace"
    ws_dst.mkdir(parents=True, exist_ok=True)
    if include_workspace_core:
        for f in CORE_WORKSPACE_FILES:
            copy_if_exists(workspace / f, ws_dst / f)
    if include_workspace_memory:
        copy_if_exists(workspace / "memory", ws_dst / "memory")
    if include_workspace_config:
        copy_if_exists(workspace / "config", ws_dst / "config")

    checksums: dict[str, str] = {}
    openclaw_json = payload / "openclaw.json"
    if openclaw_json.exists():
        checksums["payload/openclaw.json"] = file_sha256(openclaw_json)

    manifest = {
        "format": "bundleclaw.v1",
        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "encrypted": bool(encrypt_pass),
        "source": {"openclawHome": str(source), "workspace": str(workspace)},
        "includes": {
            "openclawJson": openclaw_json.exists(),
            "credentials": (payload / "credentials").exists(),
            "identity": (payload / "identity").exists(),
            "workspaceCore": include_workspace_core,
            "workspaceMemory": (ws_dst / "memory").exists(),
            "workspaceConfig": (ws_dst / "config").exists(),
        },
        "checksums": checksums,
    }

    (tmp / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    out.parent.mkdir(parents=True, exist_ok=True)

    tmp_zip = out.with_suffix(out.suffix + ".tmpzip")
    with zipfile.ZipFile(tmp_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(tmp / "manifest.json", arcname="manifest.json")
        for p in payload.rglob("*"):
            if p.is_file():
                zf.write(p, arcname=str(p.relative_to(tmp)))

    data = tmp_zip.read_bytes()
    tmp_zip.unlink(missing_ok=True)
    if encrypt_pass:
        data = encrypt_bytes(data, encrypt_pass)
    out.write_bytes(data)

    shutil.rmtree(tmp, ignore_errors=True)
    typer.echo(f"Created {out}")


@app.command("import")
def import_cmd(
    bundle: Path = typer.Option(..., help="Input .bcz bundle"),
    target: Path = typer.Option(..., help="Target ~/.openclaw path"),
    encrypt_pass: str | None = typer.Option(None, "--encrypt-pass", help="Passphrase for encrypted bundles"),
):
    bundle = bundle.expanduser().resolve()
    target = target.expanduser().resolve()

    tmp = Path.cwd() / f"bundleclaw-import-{int(time.time())}"
    tmp.mkdir(parents=True, exist_ok=True)

    raw = bundle.read_bytes()
    if raw.startswith(ENC_MAGIC):
        if not encrypt_pass:
            raise typer.BadParameter("Bundle is encrypted; provide --encrypt-pass")
        raw = decrypt_bytes(raw, encrypt_pass)

    zip_path = tmp / "bundle.zip"
    zip_path.write_bytes(raw)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(tmp)

    payload = tmp / "payload"
    if target.exists():
        backup = target.parent / f"{target.name}.bundleclaw-backup-{int(time.time())}"
        shutil.copytree(target, backup, dirs_exist_ok=True)
        typer.echo(f"Backup created: {backup}")

    target.mkdir(parents=True, exist_ok=True)
    copy_if_exists(payload / "openclaw.json", target / "openclaw.json")
    copy_if_exists(payload / "credentials", target / "credentials")
    copy_if_exists(payload / "identity", target / "identity")
    copy_if_exists(payload / "workspace", target / "workspace")

    shutil.rmtree(tmp, ignore_errors=True)
    typer.echo(f"Imported into {target}")


@app.command("verify")
def verify_cmd(target: Path = typer.Option(..., help="Target ~/.openclaw path")):
    target = target.expanduser().resolve()
    checks = [
        ("openclaw.json", (target / "openclaw.json").exists()),
        ("workspace/SOUL.md", (target / "workspace" / "SOUL.md").exists()),
        ("workspace/memory", (target / "workspace" / "memory").exists()),
    ]
    failed = False
    for name, ok in checks:
        typer.echo(f"{'OK' if ok else 'MISSING'}  {name}")
        if not ok:
            failed = True
    raise typer.Exit(code=1 if failed else 0)


@app.command("transfer")
def transfer_cmd(
    bundle: Path = typer.Option(..., help="Bundle file to transfer"),
    to: str = typer.Option(..., help="scp destination, e.g. user@host:/tmp/agent-state.bcz"),
    scp_bin: str = typer.Option("scp", help="scp binary"),
):
    bundle = bundle.expanduser().resolve()
    subprocess.run([scp_bin, str(bundle), to], check=True)
    typer.echo("Transfer complete")


@app.command("bootstrap")
def bootstrap_cmd(
    bundle: Path = typer.Option(..., help="Input .bcz bundle"),
    target: Path = typer.Option(..., help="Target ~/.openclaw path"),
    encrypt_pass: str | None = typer.Option(None, "--encrypt-pass", help="Passphrase for encrypted bundles"),
    restart_cmd: str = typer.Option("openclaw gateway restart", help="Restart command"),
    skip_restart: bool = typer.Option(False, help="Skip gateway restart"),
):
    bundle = bundle.expanduser().resolve()
    target = target.expanduser().resolve()

    tmp = Path.cwd() / f"bundleclaw-bootstrap-{int(time.time())}"
    tmp.mkdir(parents=True, exist_ok=True)

    raw = bundle.read_bytes()
    if raw.startswith(ENC_MAGIC):
        if not encrypt_pass:
            raise typer.BadParameter("Bundle is encrypted; provide --encrypt-pass")
        raw = decrypt_bytes(raw, encrypt_pass)

    zip_path = tmp / "bundle.zip"
    zip_path.write_bytes(raw)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(tmp)

    payload = tmp / "payload"
    if target.exists():
        backup = target.parent / f"{target.name}.bundleclaw-backup-{int(time.time())}"
        shutil.copytree(target, backup, dirs_exist_ok=True)
        typer.echo(f"Backup created: {backup}")

    target.mkdir(parents=True, exist_ok=True)
    copy_if_exists(payload / "openclaw.json", target / "openclaw.json")
    copy_if_exists(payload / "credentials", target / "credentials")
    copy_if_exists(payload / "identity", target / "identity")
    copy_if_exists(payload / "workspace", target / "workspace")

    shutil.rmtree(tmp, ignore_errors=True)
    typer.echo(f"Imported into {target}")

    checks = [
        ("openclaw.json", (target / "openclaw.json").exists()),
        ("workspace/SOUL.md", (target / "workspace" / "SOUL.md").exists()),
        ("workspace/memory", (target / "workspace" / "memory").exists()),
    ]
    for name, ok in checks:
        typer.echo(f"{'OK' if ok else 'MISSING'}  {name}")

    if not skip_restart:
        try:
            subprocess.run(restart_cmd, shell=True, check=True)
        except Exception:
            typer.echo(f"WARN  restart failed; run manually: {restart_cmd}")

    for cmd in ["openclaw doctor --non-interactive", "openclaw status"]:
        try:
            subprocess.run(cmd, shell=True, check=True)
        except Exception:
            typer.echo(f"WARN  command failed; run manually: {cmd}")

    typer.echo("Bootstrap complete")


if __name__ == "__main__":
    app()
