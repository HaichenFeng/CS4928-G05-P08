"""LLM-only recommendation for one case (D-04). Saves the full raw request and response.

Usage:
  export OPENAI_API_KEY=...            # never commit the key
  python scripts/run_llm.py --ref-id 1 [--dry-run]

Input : data/sample_ids.csv, docs/prompt_adapted.txt, host file read with `git show <newCommitHash>:<host_file>`
Output: outputs/llm_raw/<ref_id>.json  (request, raw response, parsed top-1, timestamps)
        outputs/llm_raw/<ref_id>_prompt.txt (rendered prompt, for review)
"""
import argparse, csv, datetime, json, os, re, subprocess, urllib.request

ap = argparse.ArgumentParser()
ap.add_argument("--ref-id", required=True)
ap.add_argument("--model", default="gpt-4o-2024-05-13")
ap.add_argument("--repos", default="repos", help="cache dir with project clones (same as select_sample.py)")
ap.add_argument("--dry-run", action="store_true", help="render and save the prompt only; no API call")
args = ap.parse_args()

case = next(r for r in csv.DictReader(open("data/sample_ids.csv")) if r["case_id"] == args.ref_id)
repo_dir = os.path.join(args.repos, case["project"])
if not os.path.isdir(os.path.join(repo_dir, ".git")):
    raise SystemExit(f"{repo_dir} missing: run scripts/select_sample.py --check-source first (it fetches the commit)")
subprocess.run(["git", "fetch", "-q", "--depth", "1", "origin", case["commit"]], cwd=repo_dir, check=False)
host_src = subprocess.run(["git", "show", f'{case["commit"]}:{case["host_file"]}'], cwd=repo_dir,
                          capture_output=True, text=True, check=True).stdout

# Method signature as declared in the source (dataset signature is RefactoringMiner notation).
name = re.match(r"\S+ (\w+)\(", case["method"]).group(1)
decl = re.search(r"^[ \t]*(?!return\b)((?:@\w+\s+)*(?:(?:public|protected|private|static|final|synchronized|abstract|default)\s+)*"
                 r"[\w<>\[\], ?.]+\s+" + name + r"\s*\([^)]*\))\s*(?:throws [\w., ]+)?\s*\{", host_src, re.M)
method_sig = decl.group(1).strip() if decl else case["method"]

# Parse docs/prompt_adapted.txt into chat messages.
messages, role, buf = [], None, []
for line in open("docs/prompt_adapted.txt").read().splitlines():
    m = re.fullmatch(r"\[(SYSTEM|USER|ASSISTANT)\]", line.strip())
    if m:
        if role: messages.append({"role": role, "content": "\n".join(buf).strip()})
        role, buf = m.group(1).lower(), []
    elif role and not line.startswith("# "):
        buf.append(line)
messages.append({"role": role, "content": "\n".join(buf).strip()})
for msg in messages:
    msg["content"] = msg["content"].replace("{METHOD_SIGNATURE}", method_sig).replace("{HOST_CLASS_SOURCE}", host_src)

os.makedirs("outputs/llm_raw", exist_ok=True)
with open(f"outputs/llm_raw/{args.ref_id}_prompt.txt", "w") as f:
    for msg in messages:
        f.write(f"[{msg['role'].upper()}]\n{msg['content']}\n\n")
print("method signature used:", method_sig)
if args.dry_run:
    print("dry run: prompt saved, no API call"); raise SystemExit

request = {"model": args.model, "temperature": 0, "messages": messages}
req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=json.dumps(request).encode(),
                             headers={"Content-Type": "application/json",
                                      "Authorization": "Bearer " + os.environ["OPENAI_API_KEY"]})
sent = datetime.datetime.now(datetime.timezone.utc).isoformat()
try:
    raw = json.load(urllib.request.urlopen(req, timeout=120)); error = None
except urllib.error.HTTPError as e:
    raw, error = None, f"HTTP {e.code}: {e.read().decode()[:2000]}"

top1, parse_error = None, None
if raw:
    text = raw["choices"][0]["message"]["content"]
    try:
        arr = re.search(r"\[.*\]", text, re.S).group(0)
        arr = re.sub(r",\s*([}\]])", r"\1", arr)   # tolerate trailing commas (the original few-shot JSON has one)
        top1 = json.loads(arr)[0]["target_class"]
    except Exception as e:
        parse_error = repr(e)

record = {"ref_id": args.ref_id, "project": case["project"], "commit": case["commit"], "host_file": case["host_file"],
          "method_signature_used": method_sig, "sent_utc": sent, "request": request,
          "response": raw, "error": error, "top1_target_class": top1, "parse_error": parse_error}
json.dump(record, open(f"outputs/llm_raw/{args.ref_id}.json", "w"), indent=2, ensure_ascii=False)
print("model returned:", raw and raw.get("model"), "| top-1:", top1, "| error:", error or parse_error)
