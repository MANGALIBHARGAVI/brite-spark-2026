import pandas as pd
from datetime import datetime, time, timedelta
from collections import defaultdict
import matplotlib.pyplot as plt
from channels import send_sms, send_voice, send_email

QUIET_START = time(8, 0)
QUIET_END = time(20, 0)

def is_landline(number: str) -> bool:
    if not number: 
        return False
    try:
        return 200 <= int(str(number).split('-')[1]) <= 249
    except Exception:
        return False

class RegulatedChannelWrapper:
    def __init__(self):
        self.resident_contact_history = defaultdict(list)
        self.stats = {
            "optouts_blocked": 0,
            "quiet_hours_blocked": 0,
            "rate_limit_blocked": 0,
            "fallback_triggered": 0,
            "missing_language_fallback": 0,
            "successful_reaches": 0
        }

    def can_send_at(self, at: datetime) -> bool:
        return QUIET_START <= at.time() <= QUIET_END

    def get_contact_count_in_rolling_window(self, resident_id: str, at: datetime) -> int:
        window_start = at - timedelta(days=7)
        attempts = self.resident_contact_history[resident_id]
        return sum(1 for t in attempts if window_start <= t <= at)

    def send_safe(self, channel: str, resident: dict, body: str, at: datetime, attempt: int = 1):
        rid = resident.get("resident_id")

        if self.get_contact_count_in_rolling_window(rid, at) >= 2:
            self.stats["rate_limit_blocked"] += 1
            return {"status": "blocked", "detail": "rate_limit_exceeded"}

        if not self.can_send_at(at):
            self.stats["quiet_hours_blocked"] += 1
            return {"status": "blocked", "detail": "quiet_hours"}

        self.resident_contact_history[rid].append(at)

        if channel == "sms":
            if resident.get("sms_optout") == "Y":
                self.stats["optouts_blocked"] += 1
                return {"status": "blocked", "detail": "opted_out"}
            mobile = str(resident.get("mobile", ""))
            if is_landline(mobile):
                return {"status": "failed", "detail": "unroutable_landline_detected"}
            return send_sms(mobile, body, at, attempt)

        elif channel == "voice":
            if resident.get("voice_optout") == "Y":
                self.stats["optouts_blocked"] += 1
                return {"status": "blocked", "detail": "opted_out"}
            phone = resident.get("landline") or resident.get("mobile")
            return send_voice(str(phone) if phone else "", body, at, attempt)

        elif channel == "email":
            if resident.get("email_optout") == "Y":
                self.stats["optouts_blocked"] += 1
                return {"status": "blocked", "detail": "opted_out"}
            return send_email(resident.get("email", ""), body, at, attempt)

TEMPLATES = {
    "en": "Hello {name}, reminder for your {service} appointment on {date} at {location}."
}

def get_message_body(resident: dict, appt: dict, wrapper: RegulatedChannelWrapper) -> str:
    lang = resident.get("language", "en")
    if lang not in TEMPLATES:
        wrapper.stats["missing_language_fallback"] += 1
        lang = "en"
        
    return TEMPLATES[lang].format(
        name=resident.get('name', 'Resident'),
        service=appt.get('service_type', 'Service'),
        date=appt.get('scheduled_at', ''),
        location=appt.get('location', '')
    )

def process_reminders(contacts_df, appts_df, wrapper: RegulatedChannelWrapper):
    contacts = contacts_df.set_index('resident_id').to_dict('index')
    appts_df['appt_dt'] = pd.to_datetime(appts_df['scheduled_at'])
    appts_df = appts_df.sort_values('appt_dt')

    for idx, appt in appts_df.iterrows():
        rid = appt['resident_id']
        if rid not in contacts:
            continue
            
        resident = contacts[rid]
        resident['resident_id'] = rid
        appt_time = appt['appt_dt']
        send_time = appt_time - timedelta(days=1)
        send_time = send_time.replace(hour=10, minute=0)
        
        body = get_message_body(resident, appt, wrapper)
        
        channels = ["sms", "voice", "email"]
        for ch in channels:
            res = wrapper.send_safe(ch, resident, body, send_time)
            if res['status'] in ['delivered', 'answered']:
                wrapper.stats["successful_reaches"] += 1
                break
            if res['status'] == 'blocked' and res['detail'] == 'rate_limit_exceeded':
                break
            wrapper.stats["fallback_triggered"] += 1

def generate_visualizations(stats):
    # 1. Bar Chart: System Metrics Overview
    plt.figure(figsize=(8, 4.5))
    categories = ['Successful', 'Rate Limited', 'Opt-outs', 'Fallbacks', 'Missing Lang']
    values = [stats['successful_reaches'], stats['rate_limit_blocked'], stats['optouts_blocked'], stats['fallback_triggered'], stats['missing_language_fallback']]
    bars = plt.bar(categories, values, color=['#2ca02c', '#d62728', '#ff7f0e', '#1f77b4', '#9467bd'])
    plt.title('Brite Spark 2026 — System Delivery & Compliance Metrics')
    plt.ylabel('Count')
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 10, str(yval), ha='center', va='bottom', fontweight='bold')
    plt.tight_layout()
    plt.savefig('metrics_summary.png')
    plt.close()

    # 2. Pie Chart: Reached vs Blocked
    plt.figure(figsize=(6, 6))
    outcomes = {'Reached Successfully': stats['successful_reaches'], 'Rate Limited (CR-2026/11)': stats['rate_limit_blocked']}
    plt.pie(outcomes.values(), labels=outcomes.keys(), autopct='%1.1f%%', colors=['#2ca02c', '#d62728'], startangle=140, explode=(0.05, 0))
    plt.title('Appointment Outcome Distribution (940 Appointments)')
    plt.tight_layout()
    plt.savefig('outcomes_pie.png')
    plt.close()

def run():
    contacts_df = pd.read_csv('contacts.csv')
    appts_df = pd.read_csv('appointments.csv')
    
    wrapper = RegulatedChannelWrapper()
    process_reminders(contacts_df, appts_df, wrapper)
    generate_visualizations(wrapper.stats)
    
    print("\n--- DAY 2 EXECUTION COMPLETE ---")
    print("Regulated System Stats:")
    for key, val in wrapper.stats.items():
        print(f"  {key}: {val}")
    print("\nVisual charts generated successfully: 'metrics_summary.png' & 'outcomes_pie.png'")

if __name__ == "__main__":
    run()