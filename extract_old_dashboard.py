import json
import re

transcript_path = r'C:\Users\Sabihul Islam\.gemini\antigravity\brain\1419e11b-cb80-4866-bbdd-2aa5c77613a5\.system_generated\logs\transcript_full.jsonl'
with open(transcript_path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            if 'class DashboardPage' in line and 'ui/pages/dashboard/dashboard_page.py' in line:
                match = re.search(r'class DashboardPage.*?(?=The above content shows)', line, re.DOTALL)
                if match:
                    content = match.group(0)
                    # Remove the <line_number>: prefix for each line
                    clean_content = re.sub(r'\\\\n\d+:\\s', '\\\\n', content)
                    # Save to old_dashboard_page.py
                    with open('old_dashboard_page.py', 'w', encoding='utf-8') as out:
                        # The content is string escaped in JSON, we can unescape it.
                        out.write(clean_content.encode().decode('unicode_escape'))
                    print('Saved to old_dashboard_page.py')
                    break
        except Exception as e:
            print(e)

