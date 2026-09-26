import re
with open('ui/pages/accounting/accounts_page.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The first one is Invoices, the second one is Quotations.
# We'll split the content.
parts = content.split('# --- Quotations Tab ---')
if len(parts) == 2:
    quot_part = parts[1]
    # Replace tab_inv -> tab_quot
    quot_part = quot_part.replace('tab_inv', 'tab_quot')
    # Replace l_inv -> l_quot
    quot_part = quot_part.replace('l_inv', 'l_quot')
    
    # Also fix inv_pagination that I missed
    quot_part = quot_part.replace('inv_pagination', 'quot_pagination')
    # Fix inv_search_row
    quot_part = quot_part.replace('inv_search_row', 'quot_search_row')
    
    content = parts[0] + '# --- Quotations Tab ---' + quot_part

with open('ui/pages/accounting/accounts_page.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed widget sharing issue.")
