"""P08 Step 2 - select the 12-case sample (run ONLY after D-03 is committed).

Input : MM-Assist datasets.zip -> data/refminer_data/instance-methods/mm-assist-emm/*_res.json
Output: data/sample_ids.csv, data/screening_log.csv

Usage:
  python scripts/select_sample.py --data <unzipped>/data                 # rule (1) only, dry run
  python scripts/select_sample.py --data <unzipped>/data --check-source  # rules (1)+(2), writes sample
"""
import argparse, csv, glob, json, os, re, subprocess

ap = argparse.ArgumentParser()
ap.add_argument("--data", required=True, help="path to the unzipped 'data' folder of datasets.zip")
ap.add_argument("--check-source", action="store_true", help="apply rule (2) with git fetch")
ap.add_argument("--repos", default="repos", help="cache dir for shallow repo fetches")
ap.add_argument("--n", type=int, default=12)
args = ap.parse_args()

DESC = re.compile(r"in class (?P<host>\S+) & moved to class (?P<target>\S+)$")


def load_cases():
    cases = []
    for f in sorted(glob.glob(os.path.join(args.data, "refminer_data/instance-methods/mm-assist-emm/*_res.json"))):
        for r in json.load(open(f)):
            mm = r["move_method_refactoring"]
            m = DESC.search(mm["description"])
            extracted = next(l for l in mm["rightSideLocations"] if l["description"] == "extracted method declaration")
            ex = r.get("extraction_results", {})
            cases.append({
                "case_id": int(r["ref_id"]),
                "project": r["repository"].rstrip("/").removesuffix(".git").split("/")[-1],
                "repo_url": r["repository"],
                "upstream_sha1": r["sha1"],                       # developer's real commit
                "commit": ex.get("newCommitHash", ""),            # authors' pre-move state (method extracted into host)
                "extraction_ok": str(ex.get("success")).lower() == "true",
                "has_telemetry": "telemetry" in r,
                "is_static": bool(mm["isStatic"]),
                "host_class": m.group("host"),
                "host_file": mm["leftSideLocations"][0]["filePath"],
                "method": extracted["codeElement"],
                "gold_target": m.group("target"),
                "refactoring_type": mm["type"],
                "source_json": os.path.basename(f),
            })
    return cases


def source_retrievable(c):
    """Rule (2): commit fetchable from GitHub and host file exists at that commit."""
    if not c["commit"]:
        return False, "no newCommitHash"
    d = os.path.join(args.repos, c["project"])
    if not os.path.isdir(os.path.join(d, ".git")):
        os.makedirs(d, exist_ok=True)
        subprocess.run(["git", "init", "-q"], cwd=d, check=True)
        subprocess.run(["git", "remote", "add", "origin", c["repo_url"]], cwd=d, check=True)
    f = subprocess.run(["git", "fetch", "-q", "--depth", "1", "origin", c["commit"]], cwd=d, capture_output=True, text=True)
    if f.returncode != 0:
        return False, "fetch failed: " + f.stderr.strip()[:120]
    e = subprocess.run(["git", "cat-file", "-e", f'{c["commit"]}:{c["host_file"]}'], cwd=d)
    return (e.returncode == 0), ("ok" if e.returncode == 0 else "host file missing at commit")


cases = load_cases()
print(f"loaded={len(cases)}")

# Rule (1): instance method. Plus data-integrity precondition: extraction succeeded and telemetry present.
eligible = [c for c in cases if not c["is_static"] and c["extraction_ok"] and c["has_telemetry"]]
print(f"rule1 eligible={len(eligible)}  (dropped: static={sum(c['is_static'] for c in cases)}, "
      f"extraction failed/no telemetry={sum(not (c['extraction_ok'] and c['has_telemetry']) for c in cases)})")

# Order: case ID, then file path, then chronological ID (ref_id is unique, so later keys are tie-breakers only)
eligible.sort(key=lambda c: (c["case_id"], c["host_file"], c["upstream_sha1"]))

if not args.check_source:
    print("dry run: rule (2) not applied; nothing written")
    raise SystemExit

os.makedirs("data", exist_ok=True)
sample, log = [], []
for c in eligible:
    if len(sample) == args.n:
        break
    ok, why = source_retrievable(c)
    log.append({"case_id": c["case_id"], "project": c["project"], "commit": c["commit"], "included": ok, "reason": why})
    print(c["case_id"], c["project"], ok, why)
    if ok:
        sample.append(c)

cols = ["case_id", "project", "commit", "upstream_sha1", "host_class", "host_file", "method", "gold_target"]
with open("data/sample_ids.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
    w.writeheader(); w.writerows(sample)
with open("data/screening_log.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["case_id", "project", "commit", "included", "reason"])
    w.writeheader(); w.writerows(log)

skipped = [l for l in log if not l["included"]]
print(f"eligible={len(eligible)}, screened={len(log)}, sampled={len(sample)}, skipped(rule2)={len(skipped)}")
if len(sample) < args.n:
    print("WARNING: fewer than", args.n, "cases - record in D-03")
