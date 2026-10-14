"""Build an offline review page from the actual exported evidence, without file uploads.

Run after: python run_lab.py export
Open evidence/review.html; this reuses the provided viewer without modifying it.
"""
from pathlib import Path
import json

from avsim import core
from lab11 import metrics


def main():
    root = Path(__file__).resolve().parent
    evidence = root / "evidence"
    doc = json.loads((evidence / "viewer.json").read_text(encoding="utf-8"))
    hazard = json.loads((root / "hazard.json").read_text(encoding="utf-8"))
    doc["runs"].append(dict(id="G-EXACT", label="mine", outcome="crash",
                            params=hazard["params"], policy={}, hazards=hazard["hazards"]))
    # Main car = selected policy, ghost = baseline. Store an actual rescued case.
    baseline = [r for r in doc["runs"] if r.get("label") in ("bus_bypass", "crosswalk_block")]
    rescued = []
    for r in baseline:
        old = core.rollout(r["params"])
        new = core.rollout(r["params"], policy=doc["policy"])
        if metrics.ego_events(old, 0) and not metrics.ego_events(new, 0):
            rescued.append(dict(r, id="FIX-" + r["id"], policy=None, outcome="safe"))
            if len(rescued) == 2:
                break
    doc["runs"].extend(rescued)
    (evidence / "review-data.js").write_text("window.LAB_SAMPLE = " + json.dumps(doc, ensure_ascii=False) + ";\n", encoding="utf-8")
    html = (root / "viewer" / "index.html").read_text(encoding="utf-8")
    for src in ("vendor/three.min.js", "sim-core.js", "app.js"):
        html = html.replace(f'src="{src}"', f'src="../viewer/{src}"')
    html = html.replace('src="lab-sample.js"', 'src="review-data.js"')
    html = html.replace("<title>Vòng lặp mô phỏng</title>", "<title>Phạm Văn Kiên · Scenario Forge · bằng chứng</title>")
    # The original viewer calls any bundled data "teacher sample". Label this
    # supplementary page correctly while leaving the provided app.js untouched.
    source_label = """<script>
    function labelEvidence() {
      var el = document.getElementById('labSrc');
      if (el && el.textContent.includes('mẫu của giảng viên'))
        el.textContent = el.textContent.replace('mẫu của giảng viên', 'bài làm 2A202602590 · evidence/viewer.json');
    }
    new MutationObserver(labelEvidence).observe(document.body, {childList:true, subtree:true});
    labelEvidence();
    </script>"""
    html = html.replace('</html>', source_label + '\n</html>')
    (evidence / "review.html").write_text(html, encoding="utf-8")
    # Frame times and positions for screenshots are recomputed, never inferred from rounded cloud points.
    shots = []
    selected = {"G-EXACT", "B-01", "C-01"} | {r["id"] for r in rescued}
    for r in doc["runs"]:
        if r["id"] not in selected:
            continue
        pol = dict(doc["policy"], **(r.get("policy") or {}))
        # An empty pinned policy still inherits doc.policy in the viewer; explicit baseline runs
        # exported by run_all carry all baseline knobs, so G-EXACT must carry them too.
        if r["id"] == "G-EXACT":
            r["policy"] = dict(core.POLICY)
            pol = dict(core.POLICY)
        R = core.rollout(r["params"], policy=pol, hazards=r.get("hazards")) if r.get("others") != "replay" else None
        if R is not None:
            ev = metrics.ego_events(R, 0)
            ghost = core.rollout(r["params"], policy={} if r.get("policy") is None else doc["policy"], hazards=r.get("hazards"))
            ge = metrics.ego_events(ghost, 0)
            shots.append(dict(id=r["id"], label=r["label"], event=ev[0] if ev else None,
                              ghost_event=ge[0] if ge else None))
    # G-EXACT's pinned baseline policy must also be reflected in the review page.
    (evidence / "review-data.js").write_text("window.LAB_SAMPLE = " + json.dumps(doc, ensure_ascii=False) + ";\n", encoding="utf-8")
    (evidence / "review-scenes.json").write_text(json.dumps(shots, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Review ready: {len(doc['runs'])} scenarios, {len(rescued)} rescued comparisons")


if __name__ == "__main__":
    main()
