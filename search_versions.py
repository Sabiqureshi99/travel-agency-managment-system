import json
import re

transcript_path = r'C:\Users\Sabihul Islam\.gemini\antigravity\brain\1419e11b-cb80-4866-bbdd-2aa5c77613a5\.system_generated\logs\transcript_full.jsonl'
with open(transcript_path, 'r', encoding='utf-8') as f:
    versions = []
    for line in f:
        try:
            if 'class DashboardPage' in line and 'ui/pages/dashboard/dashboard_page.py' in line:
                match = re.search(r'class DashboardPage.*?(?=The above content shows)', line, re.DOTALL)
                if match:
                    versions.append(match.group(0)[:300])
        except Exception:
            pass
    print(f'Found {len(versions)} versions')
    if len(versions) > 1:
        print('FIRST VERSION:')
        print(versions[0])

