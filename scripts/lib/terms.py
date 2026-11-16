"""Data-center search terms and SQL predicates for public registers."""
import re
MATCH=re.compile(r'\b(?:data[\s/-]*(?:computer\s+)?(?:cent(?:er|re)s?|halls?)|server[\s-]*farms?)\b',re.I)
def patterns(fields,fn):
    return ' OR '.join(f"{fn}({col}) LIKE '{pattern}'" for col in fields for pattern in (['%DATA%CENTER%','%DATA%CENTRE%','%DATA%HALL%','%SERVER%FARM%'] if fn=='UPPER' else ['%data%center%','%data%centre%','%data%hall%','%server%farm%']))
EX=re.compile(r'\b(?:data[\s-]*(?:processing[\s-]+)?cent(?:er|re)s?|server[\s-]+farms?)\b',re.I)
def pred(fields):return ' OR '.join("UPPER("+f+") LIKE '%"+s+"%'" for f in fields for s in ('DATA CENTER','DATA-CENTER','DATACENTER','DATA CENTRE','DATA-CENTRE','DATACENTRE','DATA PROCESSING CENT','SERVER FARM','SERVER-FARM'))
