"""Local GUI runner: keep the API key in memory; preserve all raw requests/responses."""
import csv
import shutil
import hashlib
import json
import os
from pathlib import Path
import re
import threading
import time
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = list(csv.DictReader((ROOT/'data/event_a_supplement_368.csv').open(encoding='utf-8-sig')))
IDS = [int(row['case_id']) for row in SAMPLE]
assert IDS == [368]
PILOT = IDS[0]
MODEL = 'gpt-6-luna'
ENDPOINT = 'https://api.openai.com/v1/chat/completions'

def utc():
    return datetime.now(timezone.utc).isoformat()

def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def parse_result(raw):
    choice = raw['choices'][0]
    if choice.get('finish_reason') != 'stop':
        raise ValueError('Incomplete output: ' + str(choice.get('finish_reason')))
    content = choice['message']['content'].strip()
    if content.startswith('```'):
        content = re.sub(r'^```(?:json)?\s*|\s*```$', '', content).strip()
    data = json.loads(content)
    if not isinstance(data, list) or not data or not isinstance(data[0].get('target_class'), str):
        raise ValueError('Expected nonempty JSON list with target_class')
    return {'top1': data[0]['target_class'], 'rationale': data[0].get('rationale'),
            'returned_model': raw.get('model'), 'usage': raw.get('usage'),
            'system_fingerprint': raw.get('system_fingerprint')}

class Runner:
    def __init__(self):
        self.win = tk.Tk()
        self.win.title('G05 P08 — Supplementary case 368 (not a replacement)')
        self.win.geometry('760x400')
        self.key = tk.StringVar()
        self.status = tk.StringVar(value='Paste your OpenAI API key locally, then run supplementary ref_id %s.' % PILOT)
        self.run = None
        self.secret = None
        ttk.Label(self.win, text='Frozen model: ' + MODEL + ' | temperature: 0 | reasoning: none').pack(pady=12)
        ttk.Label(self.win, text='Key stays in memory and goes only to api.openai.com. It is never saved.').pack()
        self.entry = ttk.Entry(self.win, textvariable=self.key, show='*', width=90)
        self.entry.pack(padx=20, pady=12)
        ttk.Button(self.win, text='Paste API key', command=self.paste_key).pack(pady=2)
        self.entry.bind('<Control-v>', self.paste_key)
        self.entry.bind('<Control-V>', self.paste_key)
        self.entry.bind('<Shift-Insert>', self.paste_key)
        paste_menu = tk.Menu(self.win, tearoff=False)
        paste_menu.add_command(label='Paste', command=self.paste_key)
        self.entry.bind('<Button-3>', lambda event: paste_menu.tk_popup(event.x_root, event.y_root))
        self.win.after(200, self.entry.focus_force)
        self.pilot = ttk.Button(self.win, text='Run ref_id %s (one supplementary API request)' % PILOT, command=self.begin)
        self.pilot.pack(pady=6)
        self.remaining = ttk.Button(self.win, text='Run remaining frozen cases', command=self.begin_remaining, state='disabled')
        self.remaining.pack_forget()
        ttk.Label(self.win, textvariable=self.status, wraplength=710).pack(padx=20, pady=15)
        ttk.Label(self.win, text='No automatic model substitution. API failures are not hallucinations.').pack()
        # Single supplementary case: no remaining-case gate.

    def say(self, message):
        self.win.after(0, self.status.set, message)

    def paste_key(self, event=None):
        try:
            value = self.win.clipboard_get().strip()
            if not value.startswith('sk-'):
                self.status.set('No OpenAI key on the clipboard. Copy the full key starting with sk-, then click Paste.')
            else:
                self.key.set(value)
                self.status.set('Key pasted (hidden, not saved). Click Run ref_id 368 to start.')
            value = None
        except tk.TclError:
            self.status.set('Could not read text from the clipboard. Copy the full key again and click Paste, or type it in.')
        return 'break'

    def check_gate(self):
        if self.run and (self.run / 'pilot_approved.json').exists():
            self.remaining.configure(state='normal')
        # Single supplementary case: no remaining-case gate.

    def begin(self):
        key = self.key.get().strip()
        if not key.startswith('sk-'):
            self.status.set('Enter your OpenAI secret API key (starts with sk-).')
            return
        self.secret = key
        self.key.set('')
        self.pilot.configure(state='disabled')
        runs = ROOT / 'outputs/event_a_supplement_368/runs'
        if runs.exists() and any(runs.glob('*/case_*/execution.json')):
            self.status.set('An attempt already exists. Stop and review preserved evidence before any new run.')
            self.pilot.configure(state='normal')
            self.secret = None
            return
        self.run = ROOT / 'outputs/event_a_supplement_368/runs' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
        self.run.mkdir(parents=True)
        shutil.copyfile(__file__, self.run / 'runner.py')
        # Freeze the supplementary prepared input before the first network request.
        prepared = {}
        for cid in IDS:
            src = ROOT / ('outputs/event_a_supplement_368/requests/case_%04d/request.json' % cid)
            prepared[str(cid)] = hashlib.sha256(src.read_bytes()).hexdigest()
        save(self.run / 'prepared_request_hashes.json', prepared)
        shutil.copyfile(ROOT/'data/event_a_supplement_368.csv', self.run/'sample_ids.csv')
        shutil.copyfile(ROOT/'docs/event_a_preregistration.md', self.run/'preregistration.md')
        shutil.copyfile(ROOT/'docs/event_a_model_change.md', self.run/'model_change.md')
        shutil.copyfile(ROOT/'docs/event_a_supplement_368.md', self.run/'supplement_plan.md')
        shutil.copyfile(ROOT/'outputs/event_a_supplement_368/implementation_manifest.json', self.run/'implementation_manifest.json')
        save(self.run / 'run_manifest.json', {'created_utc': utc(), 'model': MODEL,
             'temperature': 0, 'reasoning_effort': 'none', 'endpoint': ENDPOINT, 'sample_ids': IDS,
             'phase': 'SINGLE_POST_PRIMARY_SUPPLEMENT', 'role': 'NOT_A_REPLACEMENT_FOR_363', 'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
        threading.Thread(target=self.execute, args=([PILOT],), daemon=True).start()

    def begin_remaining(self):
        self.remaining.configure(state='disabled')
        threading.Thread(target=self.execute, args=(IDS[1:],), daemon=True).start()

    def execute(self, ids):
        for case_id in ids:
            folder = self.run / ('case_%04d' % case_id)
            folder.mkdir(exist_ok=False)
            request = json.loads((ROOT / ('outputs/event_a_supplement_368/requests/case_%04d/request.json' % case_id)).read_text(encoding='utf-8'))
            prepared_path = ROOT / ('outputs/event_a_supplement_368/requests/case_%04d/request.json' % case_id)
            frozen_hashes = json.loads((self.run/'prepared_request_hashes.json').read_text(encoding='utf-8'))
            assert hashlib.sha256(prepared_path.read_bytes()).hexdigest() == frozen_hashes[str(case_id)], 'Prepared input changed'
            assert request['model'] == MODEL and request['temperature'] == 0 and request.get('reasoning_effort') == 'none'
            body = json.dumps(request, ensure_ascii=False).encode('utf-8')
            (folder / 'request.json').write_bytes(body)
            record = {'case_id': case_id, 'started_utc': utc(), 'request_sha256': hashlib.sha256(body).hexdigest()}
            self.say('Calling OpenAI for ref_id %s; please keep this window open.' % case_id)
            start = time.monotonic()
            try:
                req = Request(ENDPOINT, data=body, headers={'Authorization': 'Bearer ' + self.secret, 'Content-Type': 'application/json'})
                with urlopen(req, timeout=120) as response:
                    data = response.read()
                    record.update(http_status=response.status, request_id=response.headers.get('x-request-id'))
                (folder / 'response.raw.json').write_bytes(data)
                parsed = parse_result(json.loads(data))
                save(folder / 'parsed.json', parsed)
                record['status'] = 'VALID_RESPONSE'
            except HTTPError as error:
                text = error.read().decode('utf-8', errors='replace').replace(self.secret, '[REDACTED]')
                (folder / 'error.raw.txt').write_text(text, encoding='utf-8')
                record.update(status='API_ERROR', http_status=error.code, request_id=error.headers.get('x-request-id'))
            except Exception as error:
                record.update(status='BLOCKED', error=(type(error).__name__ + ': ' + str(error)).replace(self.secret, '[REDACTED]'))
            record.update(finished_utc=utc(), elapsed_seconds=round(time.monotonic()-start, 3))
            save(folder / 'execution.json', record)
            if record['status'] != 'VALID_RESPONSE':
                self.say('Stopped at ref_id %s: %s (HTTP %s). Evidence saved to %s. Do not change model or retry yet.' % (case_id,record['status'],record.get('http_status','n/a'),folder))
                return
            self.say('ref_id %s returned valid JSON. Evidence: %s. Supplementary response saved; do not rerun.' % (case_id,folder))
            time.sleep(1)
        save(self.run / ('supplement_complete.json' if ids == [PILOT] else 'bounded_run_complete.json'), {'finished_utc':utc(), 'case_ids':ids})

if __name__ == '__main__':
    Runner().win.mainloop()
