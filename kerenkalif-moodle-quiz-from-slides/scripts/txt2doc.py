"""usage: txt2doc.py bank.txt doc.xml [--en]
Converts the plain-text question bank (see SKILL.md) into the doc-XML that build.py reads.
--en writes English table headers (No./Type/Source/Question/Answer and explanation)."""
import re,sys
SRC,DST=sys.argv[1],sys.argv[2]
EN='--en' in sys.argv
HEAD=["No.","Type","Source","Question","Answer and explanation"] if EN else ["מס'","סוג","מקור","שאלה","תשובה והסבר"]
from xml.sax.saxutils import escape as x
P=lambda t,h='':'<paragraph%s><text>%s</text></paragraph>'%(' heading="2"' if h else '',x(t))
out=['<doc>'];rows=[];cur=None
def flush():
    global rows
    if cur is None: return
    out.append(P(cur,1))
    out.append('<table><row>'+''.join('<cell>%s</cell>'%P(c) for c in HEAD)+'</row>'+''.join(rows)+'</table>'); rows=[]
q=None
def endq():
    global q
    if q:
        n,t,s,Q,A=q; s=re.sub(r'(\d)-(\d)',r'\1–\2',s)
        rows.append('<row><cell>%s</cell><cell>%s</cell><cell>%s</cell><cell>%s</cell><cell>%s</cell></row>'%(P(n),P(t),P(s),''.join(P(z) for z in Q),''.join(P(z) for z in A))); q=None
for line in open(SRC,encoding='utf8').read().split('\n'):
    if line.startswith('## '): endq(); flush(); cur=line[3:].strip()
    elif line.startswith('# '):
        endq(); n,t,s=[z.strip() for z in line[2:].split('|')]; q=[n,t,s,[],[]]
    elif line.startswith('Q: '): q[3].append(line[3:])
    elif line.startswith('A: '): q[4].append(line[3:])
endq(); flush(); out.append('</doc>')
open(DST,'w',encoding='utf8').write(''.join(out))
