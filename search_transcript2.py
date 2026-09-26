import json
import re

transcript_path = r'C:\Users\Sabihul Islam\.gemini\antigravity\brain\1419e11b-cb80-4866-bbdd-2aa5c77613a5\.system_generated\logs\transcript_full.jsonl'
with open(transcript_path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            if 'class DashboardPage' in line and 'ui/pages/dashboard/dashboard_page.py' in line:
                print('MATCH FOUND:')
                match = re.search(r'class DashboardPage.*', line)
                if match:
                    print(match.group(0)[:500])
                    break
        except Exception:
            pass

