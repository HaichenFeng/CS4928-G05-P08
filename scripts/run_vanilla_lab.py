"""D-08 local GUI runner (adapted from scripts/run_frozen_lab.py). Key stays in memory; every raw
request/response is preserved. Sends the prepared requests in outputs/requests_vanilla/ unchanged.

Differences from run_frozen_lab.py, all required by D-08:
- requests from outputs/requests_vanilla/, run folder outputs/runs/<UTC>_vanilla/;
- responses parsed with scripts/vanilla_parse.py (full recommendation list, not top-1 only);
- an unparseable response is a valid observation with zero recommendations; the run continues;
- a transport failure with no HTTP response is retried once automatically;
- an HTTP error response (401/429/5xx...) is not an observation: the run stops, the attempt is archived
  as case_<id>.attempt<n>.failed/, and "Resume" resends the same frozen request after the cause is fixed.
"""
import hashlib
import json
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from vanilla_parse import parse_raw  # noqa: E402

MODEL = 'gpt-4o-2024-05-13'
ENDPOINT = 'https://api.openai.com/v1/chat/completions'
IDS = [1, 2, 3, 5, 7, 8, 14, 15, 16, 17, 19, 21]
REQUESTS = ROOT / 'outputs/requests_vanilla'


def utc():
    return datetime.now(timezone.utc).isoformat()


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def check_prepared():
    for cid in IDS:
        folder = REQUESTS / ('case_%04d' % cid)
        record = json.loads((folder / 'input_record.json').read_text(encoding='utf-8'))
        body = (folder / 'request.json').read_bytes().replace(b'\r\n', b'\n')
        assert sha(body) == record['request_sha256'], 'prepared request changed: %d' % cid
        request = json.loads(body)
        assert request['model'] == MODEL and request['temperature'] == 0 and set(request) == {'model', 'temperature', 'messages'}


class Runner:
    def __init__(self):
        check_prepared()
        self.win = tk.Tk()
        self.win.title('G05 P08 — D-08 vanilla-prompt run')
        self.win.geometry('760x430')
        self.key = tk.StringVar()
        self.status = tk.StringVar(value='Paste your OpenAI API key locally, then run the ref_id 1 pilot.')
        self.run = None
        self.secret = None
        self.pending = []
        ttk.Label(self.win, text='D-08 | model: ' + MODEL + ' | temperature: 0 | prompt: docs/prompt_vanilla.txt').pack(pady=12)
        ttk.Label(self.win, text='Key stays in memory and goes only to api.openai.com. It is never saved.').pack()
        self.entry = ttk.Entry(self.win, textvariable=self.key, show='*', width=90)
        self.entry.pack(padx=20, pady=12)
        ttk.Button(self.win, text='Paste API key', command=self.paste_key).pack(pady=2)
        for seq in ('<Control-v>', '<Control-V>', '<Shift-Insert>'):
            self.entry.bind(seq, self.paste_key)
        self.win.after(200, self.entry.focus_force)
        self.pilot = ttk.Button(self.win, text='Run ref_id 1 pilot (one API request)', command=self.begin)
        self.pilot.pack(pady=6)
        self.remaining = ttk.Button(self.win, text='Run remaining 11 cases', command=self.begin_remaining, state='disabled')
        self.remaining.pack(pady=6)
        self.resume = ttk.Button(self.win, text='Resume after an HTTP error (same frozen request)', command=self.do_resume, state='disabled')
        self.resume.pack(pady=6)
        ttk.Label(self.win, textvariable=self.status, wraplength=710).pack(padx=20, pady=15)
        ttk.Label(self.win, text='No model substitution. No reruns of valid observations. API errors are not observations.').pack()
        self.win.after(2000, self.check_gate)

    def say(self, message):
        self.win.after(0, self.status.set, message)

    def paste_key(self, event=None):
        try:
            value = self.win.clipboard_get().strip()
            if not value.startswith('sk-'):
                self.status.set('No OpenAI key on the clipboard. Copy the full key starting with sk-, then click Paste.')
            else:
                self.key.set(value)
                self.status.set('Key pasted (hidden, not saved). Click Run ref_id 1 pilot to start.')
            value = None
        except tk.TclError:
            self.status.set('Could not read text from the clipboard. Copy the full key again and click Paste, or type it in.')
        return 'break'

    def check_gate(self):
        if self.run and (self.run / 'pilot_approved.json').exists() and (self.run / 'pilot_complete.json').exists() \
                and not (self.run / 'case_0002').exists() and not self.pending:
            self.remaining.configure(state='normal')
        self.win.after(2000, self.check_gate)

    def begin(self):
        key = self.key.get().strip()
        if not key.startswith('sk-'):
            self.status.set('Enter your OpenAI secret API key (starts with sk-).')
            return
        self.secret = key
        self.key.set('')
        self.pilot.configure(state='disabled')
        self.run = ROOT / 'outputs/runs' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ') + '_vanilla')
        self.run.mkdir(parents=True)
        save(self.run / 'run_manifest.json', {
            'created_utc': utc(), 'decision': 'D-08', 'model': MODEL, 'temperature': 0, 'endpoint': ENDPOINT,
            'sample_ids': IDS, 'requests_dir': 'outputs/requests_vanilla', 'phase': 'PILOT',
            'runner_sha256': sha(Path(__file__).read_bytes()),
            'parser_sha256': sha((Path(__file__).resolve().parent / 'vanilla_parse.py').read_bytes())})
        (self.run / 'runner.py').write_bytes(Path(__file__).read_bytes())
        (self.run / 'vanilla_parse.py').write_bytes((Path(__file__).resolve().parent / 'vanilla_parse.py').read_bytes())
        self.start([1])

    def begin_remaining(self):
        self.remaining.configure(state='disabled')
        self.start(IDS[1:])

    def do_resume(self):
        self.resume.configure(state='disabled')
        self.start(self.pending)

    def start(self, ids):
        threading.Thread(target=self.execute, args=(list(ids),), daemon=True).start()

    def call(self, body):
        req = Request(ENDPOINT, data=body, headers={'Authorization': 'Bearer ' + self.secret, 'Content-Type': 'application/json'})
        with urlopen(req, timeout=180) as response:
            return response.read(), response.status, response.headers.get('x-request-id')

    def execute(self, ids):
        for n, case_id in enumerate(ids):
            folder = self.run / ('case_%04d' % case_id)
            folder.mkdir(exist_ok=False)
            body = (REQUESTS / ('case_%04d/request.json' % case_id)).read_bytes().replace(b'\r\n', b'\n')
            body = json.dumps(json.loads(body), ensure_ascii=False).encode('utf-8')
            (folder / 'request.json').write_bytes(body)
            record = {'case_id': case_id, 'started_utc': utc(), 'request_sha256': sha(body), 'transport_attempts': 0}
            self.say('Calling OpenAI for ref_id %s; please keep this window open.' % case_id)
            start = time.monotonic()
            try:
                while True:
                    record['transport_attempts'] += 1
                    try:
                        data, status, request_id = self.call(body)
                        break
                    except HTTPError:
                        raise
                    except (URLError, TimeoutError, ConnectionError) as error:  # no HTTP response at all
                        record.setdefault('transport_errors', []).append((type(error).__name__ + ': ' + str(error)).replace(self.secret, '[REDACTED]'))
                        if record['transport_attempts'] >= 2:
                            raise
                        time.sleep(5)
                record.update(http_status=status, request_id=request_id)
                (folder / 'response.raw.json').write_bytes(data)
                parsed = parse_raw(json.loads(data))
                save(folder / 'parsed.json', parsed)
                record['status'] = 'VALID_RESPONSE' if parsed['parse_status'].startswith('json') else 'VALID_RESPONSE_' + parsed['parse_status']
                record['recommendation_count'] = len(parsed['recommendations'])
            except HTTPError as error:
                text = error.read().decode('utf-8', errors='replace').replace(self.secret, '[REDACTED]')
                (folder / 'error.raw.txt').write_text(text, encoding='utf-8')
                record.update(status='API_ERROR', http_status=error.code, request_id=error.headers.get('x-request-id'))
            except Exception as error:
                record.update(status='BLOCKED', error=(type(error).__name__ + ': ' + str(error)).replace(self.secret, '[REDACTED]'))
            record.update(finished_utc=utc(), elapsed_seconds=round(time.monotonic() - start, 3))
            save(folder / 'execution.json', record)
            if not record['status'].startswith('VALID_RESPONSE'):
                attempt = 1
                while (self.run / ('case_%04d.attempt%d.failed' % (case_id, attempt))).exists():
                    attempt += 1
                folder.rename(self.run / ('case_%04d.attempt%d.failed' % (case_id, attempt)))
                self.pending = ids[n:]
                self.win.after(0, lambda: self.resume.configure(state='normal'))
                self.say('Stopped at ref_id %s: %s (HTTP %s). Archived as attempt %d. Fix the cause (key, quota), then Resume. '
                         'Do not change model, prompt or request.' % (case_id, record['status'], record.get('http_status', 'n/a'), attempt))
                return
            self.say('ref_id %s: %s, %d recommendations. Evidence: %s' % (case_id, record['status'], record['recommendation_count'], folder))
            time.sleep(1)
        self.pending = []
        done = sorted(int(p.name[5:9]) for p in self.run.glob('case_????') if p.is_dir())
        if done == [1]:
            save(self.run / 'pilot_complete.json', {'finished_utc': utc(), 'case_ids': [1]})
            self.say('Pilot done. Review case_0001, then create pilot_approved.json in the run folder to enable the remaining 11 cases.')
        elif done == IDS:
            save(self.run / 'bounded_run_complete.json', {'finished_utc': utc(), 'case_ids': IDS})
            self.say('All 12 cases done. Close this window and run scripts/evaluate_vanilla.py.')


if __name__ == '__main__':
    Runner().win.mainloop()
