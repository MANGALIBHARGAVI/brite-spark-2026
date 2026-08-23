"""
Calder County — mock messaging channels.

    from channels import send_sms, send_voice, send_email

Every call is logged to outbox.jsonl in the working directory, so you (and we)
can audit exactly what your system tried to send, to whom, and when.

Deterministic: the same (recipient, body, attempt) at the same time yields the
same outcome, so a retry is a genuine retry rather than a fresh dice roll.

These channels enforce NOTHING. They will send at four in the morning, they will
send to someone who has opted out, and they will send the same message five times.
Quiet hours, opt-outs, deduplication and stopping rules are yours to implement.
"""
import hashlib, json, os
from datetime import datetime

OUTBOX = os.environ.get('OUTBOX_PATH', 'outbox.jsonl')

def _roll(*parts):
    h = hashlib.sha256('|'.join(str(p) for p in parts).encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF

def _is_landline(number: str) -> bool:
    """Numbers in the 555-2xx block are landlines. The carrier knows this. You may not."""
    try:
        return 200 <= int(number.split('-')[1]) <= 249
    except Exception:
        return False

def _log(channel, to, body, at, result):
    rec = {'channel': channel, 'to': to, 'at': at.isoformat() if isinstance(at, datetime) else str(at),
           'body_preview': (body or '')[:60], 'status': result['status'],
           'detail': result.get('detail', '')}
    try:
        with open(OUTBOX, 'a', encoding='utf-8') as f:
            f.write(json.dumps(rec) + '\n')
    except Exception:
        pass
    return result

def send_sms(to, body, at=None, attempt=1):
    at = at or datetime.now()
    if not to:
        return _log('sms', to, body, at, {'status': 'failed', 'detail': 'no_number'})
    r = _roll('sms', to, body, attempt)
    if _is_landline(to):
        # A landline cannot receive SMS. Some carriers say so. Some accept the
        # message, charge for it, and drop it — and report success.
        if r < 0.55:
            return _log('sms', to, body, at, {'status': 'delivered', 'detail': 'accepted_by_carrier'})
        return _log('sms', to, body, at, {'status': 'failed', 'detail': 'unroutable_landline'})
    if r < 0.88:
        return _log('sms', to, body, at, {'status': 'delivered', 'detail': ''})
    if r < 0.95:
        return _log('sms', to, body, at, {'status': 'failed', 'detail': 'carrier_rejected'})
    return _log('sms', to, body, at, {'status': 'failed', 'detail': 'unknown_subscriber'})

def send_voice(to, body, at=None, attempt=1):
    at = at or datetime.now()
    if not to:
        return _log('voice', to, body, at, {'status': 'failed', 'detail': 'no_number'})
    r = _roll('voice', to, body, attempt)
    if r < 0.42:  return _log('voice', to, body, at, {'status': 'answered', 'detail': 'human'})
    if r < 0.60:  return _log('voice', to, body, at, {'status': 'answered', 'detail': 'voicemail_left'})
    if r < 0.90:  return _log('voice', to, body, at, {'status': 'no_answer', 'detail': ''})
    if r < 0.96:  return _log('voice', to, body, at, {'status': 'failed', 'detail': 'busy'})
    return _log('voice', to, body, at, {'status': 'failed', 'detail': 'number_unobtainable'})

def send_email(to, body, at=None, attempt=1):
    at = at or datetime.now()
    if not to:
        return _log('email', to, body, at, {'status': 'failed', 'detail': 'no_address'})
    r = _roll('email', to, body, attempt)
    if r < 0.78:  return _log('email', to, body, at, {'status': 'delivered', 'detail': ''})
    if r < 0.86:  return _log('email', to, body, at, {'status': 'delivered', 'detail': 'placed_in_spam'})
    if r < 0.93:  return _log('email', to, body, at, {'status': 'failed', 'detail': 'soft_bounce'})
    return _log('email', to, body, at, {'status': 'failed', 'detail': 'hard_bounce'})
