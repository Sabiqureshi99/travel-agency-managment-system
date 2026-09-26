import json
import re

transcript_path = r'C:\Users\Sabihul Islam\.gemini\antigravity\brain\1419e11b-cb80-4866-bbdd-2aa5c77613a5\.system_generated\logs\transcript.jsonl'
with open(transcript_path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            line = line.strip()
            if not line: continue
            data = json.loads(line)
            if 'content' in data and data['content'] and 'dashboard_page.py' in data['content']:
                if 'class DashboardPage' in data['content']:
                    print(f"Step {data.get('step_index')}: {data.get('type')}")
                    print(data['content'][:500])
                    print('...')
        except Exception:
            pass

