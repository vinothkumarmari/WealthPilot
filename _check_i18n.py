import re, os
from app.translations import TRANSLATIONS

keys_used = set()
tmpl_dir = 'app/templates'
for f in os.listdir(tmpl_dir):
    if f.endswith('.html'):
        content = open(os.path.join(tmpl_dir, f), encoding='utf-8').read()
        keys_used.update(re.findall(r"t\('([^']+)'\)", content))
        keys_used.update(re.findall(r't\("([^"]+)"\)', content))

content = open('app/routes.py', encoding='utf-8').read()
keys_used.update(re.findall(r"t\('([^']+)'\)", content))

# Filter: real display text only
SKIP = {'Done','Open','Plan','Gold','Silver','Spread','Purity','Price','Pending',
        'Select','Refresh','Change','Period','Unit','Login','Register','Insurance',
        'Calculator','Password','Currency','Country','Countries','Karat','Kilogram',
        'Ounce','Tola','Gram','Ask','Bid'}

missing = sorted([k for k in keys_used if k not in TRANSLATIONS
    and len(k) > 3
    and k[0].isupper()
    and not k.startswith('{')
    and '_' not in k
    and k not in SKIP
])
print(f'Real missing: {len(missing)}')
for k in missing:
    print(f'  {k}')
