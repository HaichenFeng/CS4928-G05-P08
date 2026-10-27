"""Terminal entry point for Event A; inherits the unchanged M2 request/parser execution."""
import getpass,hashlib,json,shutil,time
from pathlib import Path
from datetime import datetime,timezone
from run_event_a import Runner,ROOT,MODEL,ENDPOINT,IDS,PILOT,save,utc
class TerminalRunner(Runner):
    def __init__(self):
        self.run=None;self.secret=None
    def say(self,message):
        print(message,flush=True)
def main():
    runs=ROOT/'outputs/event_a_gpt6_luna/runs'
    if runs.exists() and any(runs.glob('*/case_*/execution.json')):
        raise SystemExit('An Event A attempt already exists. Preserve it; review before any new run.')
    print('G05 P08 - Event A frozen six-case run',flush=True)
    print('Model: '+MODEL+' | temperature: 0 | case IDs: '+str(IDS),flush=True)
    print('The API key stays in memory and is sent only to api.openai.com. It is never saved.',flush=True)
    key=getpass.getpass('OpenAI API key (hidden; paste, then press Enter): ').strip()
    if not key.startswith('sk-'):raise SystemExit('No valid key entered. No request sent.')
    runner=TerminalRunner();runner.secret=key;key=None
    runner.run=runs/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ_terminal')
    runner.run.mkdir(parents=True)
    for name in ['run_event_a_terminal.py','run_event_a.py','run_frozen_lab.py']:
        shutil.copyfile(ROOT/'scripts'/name,runner.run/name)
    hashes={str(cid):hashlib.sha256((ROOT/('outputs/event_a_gpt6_luna/requests/case_%04d/request.json'%cid)).read_bytes()).hexdigest() for cid in IDS}
    save(runner.run/'prepared_request_hashes.json',hashes)
    for src,dest in [(ROOT/'data/event_a_sample_ids.csv','sample_ids.csv'),(ROOT/'docs/Decisions.md','preregistration.md'),(ROOT/'outputs/event_a_gpt6_luna/implementation_manifest.json','implementation_manifest.json')]:
        shutil.copyfile(src,runner.run/dest)
    shutil.copyfile(ROOT/'docs/event_a_model_change.md',runner.run/'model_change.md')
    save(runner.run/'run_manifest.json',{'created_utc':utc(),'model':MODEL,'temperature':0,'reasoning_effort':'none','endpoint':ENDPOINT,'sample_ids':IDS,
        'phase':'PILOT','entry_point':'terminal','runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()})
    print('Evidence folder: '+str(runner.run),flush=True)
    runner.execute([PILOT])
    if not (runner.run/'pilot_complete.json').exists():return
    print('Pilot saved. Waiting for input/response-integrity review; keep this terminal open.',flush=True)
    print('No request, model or decision rule will be changed after the pilot.',flush=True)
    while not (runner.run/'pilot_approved.json').exists():time.sleep(1)
    print('Integrity review passed. Running remaining five frozen requests.',flush=True)
    runner.execute(IDS[1:]);runner.secret=None
    if (runner.run/'bounded_run_complete.json').exists():
        print('All six observations saved. Evaluation is the next step.',flush=True)
if __name__=='__main__':
    try:main()
    except KeyboardInterrupt:print('\nStopped by user. Preserved any existing evidence.',flush=True)