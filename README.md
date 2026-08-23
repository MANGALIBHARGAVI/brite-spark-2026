# Problem 7 — The Reminder That Reaches
## Data pack

### Contents

| File | What it is |
|:--|:--|
| `appointments.csv` | 940 appointments across four weeks, 2–29 March 2026. |
| `contacts.csv` | 620 residents and how to reach them. |
| `channels/channels.py` | Mock SMS, voice and email. |
| `channels/demo.py` | Five example calls so you can see what comes back. |

Python 3 standard library only.

### `appointments.csv`

| Column | Meaning |
|:--|:--|
| `appointment_id` | Reference. |
| `resident_id` | Joins to `contacts.csv`. |
| `scheduled_at` | Local date and time, `YYYY-MM-DD HH:MM`. |
| `location` | Which district office. |
| `service_type` | What the appointment is for. |
| `status` | All `Booked`. |

### `contacts.csv`

| Column | Meaning |
|:--|:--|
| `resident_id` | Reference. |
| `name` | Synthetic. |
| `mobile` | Mobile number as recorded. |
| `landline` | Landline as recorded, where held. |
| `email` | Email as recorded, where held. |
| `language` | Preferred language: `en`, `es`, `vi`, `so`, `ru`, `zh`. |
| `sms_optout`, `voice_optout`, `email_optout` | `Y` where the resident has opted out of that channel. |
| `number_last_verified` | When the Department last confirmed the phone details with the resident. |

### The channels

```python
from channels import send_sms, send_voice, send_email
send_sms(to, body, at=datetime(...), attempt=1)
```

Each returns `{'status': ..., 'detail': ...}` and appends to `outbox.jsonl`.

**The channels enforce nothing.** They will send at four in the morning, they will send to a resident who has opted out, and they will send the same message five times without complaint. Quiet hours, opt-outs, deduplication and stopping rules are entirely your responsibility — that is the problem.

Outcomes are deterministic for a given recipient, message body and attempt number, so a retry is a real retry rather than a fresh roll of the dice.

Statuses you will see include `delivered`, `failed`, `answered`, `no_answer`. Read `detail` as well as `status`. They do not always mean what you would assume, and **a status of `delivered` is not the same thing as a resident having been reached.**

### On languages

A quarter of the appointments in this pack belong to residents whose preferred language is not English, across five languages.

**You are not expected to translate anything.** Producing real Vietnamese, Somali, Russian, Spanish or Chinese message copy is not part of this problem, and we would have no way to check it if you did. Write your templates in English, or use obvious placeholders.

What *is* part of this problem is that the selection mechanism works, that it selects per resident from the recorded preference, and that you have a defined answer for what happens when no template exists in someone's language. Falling back to English is a perfectly acceptable answer. Falling back silently, so that nobody ever finds out how many people got a message they could not read, is not — that number should come out of your system.

### What you should know before you start

The contact list has been accumulating for years. Different people built it, to different standards, and nothing has ever been cleaned out of it. You should expect:

- Records with incomplete contact details, and some with none at all.
- A mix of line types, which do not all accept the same kinds of message.
- Contact points that serve more than one resident.
- A range of language preferences.
- Recorded opt-outs, on individual channels and in combination.
- Details that have gone stale in ways the list does not flag.

That list is not exhaustive and it does not tell you how many of each. **Read the contact list properly before you design anything.** Several of the requirements in your problem document will only make sense once you have understood who is actually in it, and this is the problem in the set where careful reading beats fast building most decisively.

One question worth holding onto throughout: what would it take for this system to do harm? Not fail — harm. The answer is not hypothetical and it is in this data.

### Reminder

A change to the requirements lands on day two. You will not be told what it is.
