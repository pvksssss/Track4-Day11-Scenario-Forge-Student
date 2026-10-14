"""Check evidence consistency and optionally package the complete submission."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import zipfile

from avsim import core, space, studio
from lab11 import estimate, policy

ROOT = Path(__file__).resolve().parent


def load(name):
    return json.loads((ROOT / "evidence" / f"{name}.json").read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", action="store_true")
    args = parser.parse_args()
    nat, seeds = space.student_variant("2A202602590")
    meta = load("meta")
    assert meta["seeds"] == seeds
    assert set(meta["steps"]) == {"world", "replay", "mc", "hunt", "estimate", "fix", "mine", "export"}
    assert all(not step["quick"] for step in meta["steps"].values())
    for name in ("meta", "world", "replay", "mc", "hunt", "estimate", "fix", "mine"):
        data = load(name)
        assert data["_run"]["mssv"] == "2A202602590"
        assert data["_run"]["town"] == "B" and not data["_run"]["quick"]
    mc = load("mc")
    assert mc["n"] == 3000 and sum(mc["modes"].values()) == mc["crashes"]
    assert (mc["lo"], mc["hi"]) == estimate.wilson_ci(mc["crashes"], mc["n"])
    fix = load("fix")
    assert fix["chosen"] == policy.choose_policy(fix["table"], fix["baseline_train"]["progress"])
    hazard = studio.load(ROOT / "hazard.json")
    assert not studio.check_space(hazard) and studio.hazard_ok(hazard["hazards"], hazard["params"])
    R = core.rollout(hazard["params"], policy=hazard["policy"], hazards=hazard["hazards"])
    mine = load("mine")
    assert [list((e["a"], e["b"], e["t"])) for e in R.events[0]] == mine["exact"]["planner"]
    assert mine["accepted"] >= 0.5
    for name in ("baseline", "chosen"):
        r = mine[name]
        assert r["avoidable"] + r["unavoidable"] + r["unattributed"] == r["crashes"]
        assert r["p"] == r["avoidable"] / r["n"]
        assert (r["lo"], r["hi"]) == estimate.wilson_ci(r["avoidable"], r["n"])
        assert r["per_trip"] == hazard["exposure"] * r["p"]
        assert r["overlap_at_start"] == 0
    report = (ROOT / "REPORT.md").read_text(encoding="utf-8")
    assert report.startswith("MSSV: 2A202602590\n")
    assert len(re.findall(r"^## [1-9]\. ", report, re.M)) == 9
    for image in re.findall(r"!\[[^]]*\]\(([^)]+)\)", report):
        p = ROOT / image
        assert p.is_file() and p.stat().st_size > 10000, f"Missing screenshot: {image}"
        assert p.read_bytes()[:2] == b"\xff\xd8", f"Not JPEG: {image}"
    assert (ROOT / "evidence" / "review.html").exists()
    files = [p for p in ROOT.rglob("*") if p.is_file()
             and not any(part in {".git", "__pycache__", ".pytest_cache", ".venv", ".agents", ".codex", ".aws"} for part in p.relative_to(ROOT).parts)
             and p.suffix != ".zip" and p.name != "manifest.json"]
    manifest = {str(p.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
    (ROOT / "evidence" / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Verified: full budgets, original MSSV/seeds, TRAIN choice, MC/mine counts and CI, exact scene, 9 report answers, 4 screenshots.")
    if args.zip:
        path = ROOT / "submission-Pham-Van-Kien-2A202602590.zip"
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for p in files + [ROOT / "evidence" / "manifest.json"]:
                archive.write(p, p.relative_to(ROOT))
        print(f"Packaged: {path.name} ({path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
