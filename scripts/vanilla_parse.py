"""D-08 parsing rule for vanilla-prompt responses. Shared by run_vanilla_lab.py and evaluate_vanilla.py.

Strip a surrounding ``` fence; json.loads; if that fails, remove trailing commas before } or ] (the few-shot
answer itself has one) and json.loads again. A JSON list is the recommendation list (rank = position);
anything else, or text that still does not parse, is recorded as zero recommendations.
"""
import json
import re

FIELDS = ('method_name', 'method_signature', 'target_class', 'rationale')


def parse_content(content):
    text = content.strip()
    if text.startswith('```'):
        text = re.sub(r'^```[A-Za-z]*\s*|\s*```$', '', text).strip()
    status = 'json'
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        try:
            data = json.loads(re.sub(r',\s*([}\]])', r'\1', text))
            status = 'json_after_trailing_comma_removal'
        except json.JSONDecodeError as error:
            return {'parse_status': 'UNPARSEABLE', 'parse_error': str(error), 'recommendations': []}
    if not isinstance(data, list):
        return {'parse_status': 'NOT_A_LIST', 'recommendations': []}
    recs = []
    for rank, item in enumerate(data, 1):
        item = item if isinstance(item, dict) else {}
        recs.append({'rank': rank, **{k: (item.get(k).strip() if isinstance(item.get(k), str) else item.get(k)) for k in FIELDS},
                     'well_formed': isinstance(item.get('method_name'), str) and isinstance(item.get('target_class'), str)})
    return {'parse_status': status, 'recommendations': recs}


def parse_raw(raw):
    choice = raw['choices'][0]
    out = parse_content(choice['message']['content'] or '')
    out.update(finish_reason=choice.get('finish_reason'), returned_model=raw.get('model'),
               usage=raw.get('usage'), system_fingerprint=raw.get('system_fingerprint'))
    return out
