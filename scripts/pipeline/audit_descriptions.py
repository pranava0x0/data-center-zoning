"""Audit every public paraphrase for stock generated prose; leave source quotations verbatim."""
import json,re
from pathlib import Path
R=Path(__file__).resolve().parents[2]
patterns=[r'\bdelve\b',r'\bfoster(?:s|ing)?\b',r'\bleverage(?:s|d|ing)?\b',r'\bit(?:’|\x27)s worth noting\b',r'\bin today(?:’|\x27)s\b',r'\bgame.chang(?:er|ing)\b',r'\bseamless(?:ly)?\b',r'\brobust framework\b',r'\bcomprehensive solution\b',r'\btestament to\b',r'\bcrucial role\b',r'\bunprecedented\b',r'\bunlock(?:s|ing)?\b']
rows=json.loads((R/'output/rules.json').read_text());tc=json.loads((R/'output/telecom/release.json').read_text())
findings=[];checked=0
for row in rows+tc['provisions']:
 for field in ['summary','card_sentence']:
  value=row.get(field)
  if not value:continue
  checked+=1
  for pattern in patterns:
   if re.search(pattern,value,re.I):findings.append(dict(id=row['id'],field=field,pattern=pattern,text=value))
report=dict(passed=not findings,records=len(rows)+len(tc['provisions']),paraphrases_checked=checked,findings=findings,limit='Phrase and field checks, not proof of legal accuracy or a substitute for editorial review. Official quotations and agency work descriptions remain verbatim.')
(R/'output/description_audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
raise SystemExit(bool(findings))
