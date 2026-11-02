#!/usr/bin/env python3
"""Prepare pinned sources and runtime asset declarations, without a game disc."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

PROJECT = Path(__file__).resolve().parents[1]


def run(*args, cwd=None):
    subprocess.run([str(a) for a in args], cwd=cwd, check=True)


def git_output(path, *args):
    return subprocess.check_output(["git", "-C", str(path), *args]).decode().strip()


def fetch(path, entry):
    if not path.exists():
        path.mkdir(parents=True)
        run("git", "init", "-q", path)
        run("git", "-C", path, "remote", "add", "origin", entry["url"])
        run("git", "-C", path, "fetch", "--depth", "1", "origin", entry["commit"])
        run("git", "-C", path, "-c", "advice.detachedHead=false", "checkout", "--detach", "FETCH_HEAD")
    if git_output(path, "rev-parse", "HEAD") != entry["commit"]:
        raise RuntimeError(f"Source pin mismatch: {path}; existing checkout left unchanged")


def apply_patches(path, patches):
    signature = hashlib.sha256(b"".join(p.name.encode() + b"\0" + p.read_bytes() for p in patches)).hexdigest()
    stamp = path / ".git" / "crossover-patches.json"
    if stamp.exists():
        previous = json.loads(stamp.read_text())
        diff = git_output(path, "diff", "--binary", "HEAD")
        actual = hashlib.sha256(diff.encode()).hexdigest()
        if previous == {"signature": signature, "diff_sha256": actual}:
            print(f"Pinned patches already applied: {path.name}")
            return
        raise RuntimeError(f"Patch set or prepared source changed: {path}; use a fresh output directory")
    if git_output(path, "status", "--porcelain"):
        raise RuntimeError(f"Uncommitted source changes: {path}; refusing to overwrite")
    for patch in patches:
        run("git", "-C", path, "apply", "--check", patch)
        run("git", "-C", path, "apply", patch)
    # Include newly added files in diff verification without creating a commit.
    run("git", "-C", path, "add", "-N", ".")
    run("git", "-C", path, "diff", "--check")
    diff = git_output(path, "diff", "--binary", "HEAD")
    stamp.write_text(json.dumps({"signature": signature, "diff_sha256": hashlib.sha256(diff.encode()).hexdigest()}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--skip-uwp-deps", action="store_true")
    args = parser.parse_args()
    out = args.out.resolve()
    pins = json.loads((PROJECT / "sources.lock.json").read_text())
    for name, entry in pins.items():
        if name == "schema_version" or (name == "uwp-dep" and args.skip_uwp_deps):
            continue
        fetch(out / name, entry)
    ww = out / "windwaker"
    aurora = out / "aurora"
    apply_patches(ww, [PROJECT / "patches" / "windwaker-uwp.patch"])
    apply_patches(aurora, [PROJECT / "patches" / "aurora-uwp.patch"] +
                  sorted((ww / "native/patches/aurora").glob("*.patch")))
    assets = out / "assets/GZLE01"
    assets.mkdir(parents=True, exist_ok=True)
    shutil.copytree(out / "decomp/assets/GZLE01/res", assets / "res", dirs_exist_ok=True)
    run(sys.executable, ww / "native/tools/gen_asset_stubs.py", "--decomp", out / "decomp", "--out", assets)
    provenance = {"sources": pins, "runtime_assets": True, "game_data_bundled": False,
                  "windwaker_patch_sha256": hashlib.sha256((PROJECT / "patches/windwaker-uwp.patch").read_bytes()).hexdigest(),
                  "aurora_patch_sha256": hashlib.sha256((PROJECT / "patches/aurora-uwp.patch").read_bytes()).hexdigest()}
    (out / "source-provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(f"Prepared source tree: {out}")


if __name__ == "__main__":
    main()
