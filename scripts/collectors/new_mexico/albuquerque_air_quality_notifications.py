"""City of Albuquerque Environmental Health air quality notifications report (generator notifications), filtered to named data centers."""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # scripts/ on the import path
import datetime as dt, io, re
from pypdf import PdfReader
import collectors.new_mexico.sources as n
def rows(a,emit):
    raw,h=a.get(n.AQNS);pdf=PdfReader(io.BytesIO(raw))
    names={'3530-':'Albuquerque 10 MW Data Center','0226':'Phoenix Data Center, Albuquerque','1103':'Peraton Data Center'}
    for i,page in enumerate(pdf.pages,1):
        lines=page.extract_text(extraction_mode='layout').splitlines()
        for idx,line in enumerate(lines):
            mt=re.match(r'\s*([0-9-]+AQN[A-Z0-9-]+)\s',line)
            if not mt:continue
            no=mt[1];pref=next((p for p in names if no.startswith(p)),'')
            if not pref:continue
            # Read only the current notification row, stopping before the next identifier.
            region=[line]
            for nxt in lines[idx+1:idx+4]:
                if re.search(r'^\s*[0-9-]+AQN',nxt):break
                region.append(nxt)
            text=' '.join(' '.join(region).split())
            if not re.search(r'data center',text,re.I):continue
            if pref=='3530-' and ('Albuquerque 10 MW' not in text or 'CLOP Albuquerque' not in text):continue
            if pref=='0226' and 'PHOENIX DATA CENTER' not in text:continue
            if pref=='1103' and 'Peraton Data Center' not in text:continue
            day=dt.datetime.strptime(re.search(r'\b\d{1,2}/\d{1,2}/\d{4}\b',line)[0],'%m/%d/%Y').date().isoformat()
            emit('Albuquerque air quality notifications',no,'Albuquerque','Bernalillo County',names[pref],'Air quality notification for an emergency generator','Notification issued',day,'Notification date',n.AQNS+'#page='+str(i),h,'Air Quality Notifications Issued · page '+str(i)+' · '+no,source_url=n.AQNS)
