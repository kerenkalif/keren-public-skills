#!/usr/bin/env python3
"""Question-bank doc XML -> Moodle XML, RTL/BiDi safe.
usage: build.py doc.xml out.xml "<root category name>" [idnumber prefix] [--ltr]
Default is right-to-left (Hebrew/Arabic) output with BiDi isolation marks.
--ltr produces plain left-to-right output (English and other LTR languages).
Table headers / question types may be Hebrew or English (see HDRS / TYPES below)."""
import xml.etree.ElementTree as ET, re, html, sys
from xml.sax.saxutils import escape as xesc
RLI,LRI,PDI=chr(0x2067),chr(0x2066),chr(0x2069)
HEB=r'֐-׿'
QUOTED=r'"[^"'+HEB+r']*[A-Za-z][^"'+HEB+r']*"'
L=r'[A-Za-z0-9_]'
TOK=L+r'+(?:[\'’.\-–/]'+L+r'+)*(?:\+\+\)?)?'
JOIN=r'(?:[ ,;:+=<>*/()\[\]{}\-–]|(?<=[A-Za-z0-9_]) ?\.\.\.)+'
RUN=re.compile(r'[A-Za-z]+ → \[[^\]]*\]|'+QUOTED+'|'+r'(?:\(?'+TOK+r'(?:'+JOIN+r'(?=\(?'+L+r')\(?'+TOK+r')*\)?)')
def ok(s): return re.search('[A-Za-z]',s) or re.fullmatch(r'\d+(?:[–\-]\d+)+',s)
def runs(text):
    pos=0
    for m in RUN.finditer(text):
        s=m.group(0)
        if not ok(s): continue
        lead=0
        while s.startswith('(') and s.count('(')>s.count(')'): s=s[1:]; lead+=1
        while s.count('(')>s.count(')'):
            i=s.rfind('('); s=s[:i].rstrip(' ,;:')
        while s.endswith(')') and s.count(')')>s.count('(') and not s.endswith('++)'): s=s[:-1]
        if not s or not ok(s): continue
        a=m.start()+lead
        if a>pos: yield (False,text[pos:a])
        yield (True,s); pos=a+len(s)
    if pos<len(text): yield (False,text[pos:])
GAP=False
RTL=True
def h(t,mode):
    if GAP: t=re.sub(r'_{3,}',chr(0xE000),t)
    if not RTL: return html.escape(t,quote=False) if mode=='html' else t
    out=''
    for ltr,s in runs(t):
        if mode=='html': out+=('<span dir="ltr">%s</span>'%html.escape(s,quote=False)) if ltr else html.escape(s,quote=False)
        else: out+=(LRI+s+PDI) if ltr else s
    return out
def rich(p):
    buf=[]
    def emit(s,bold,code=False):
        if not s: return
        x='<code dir="ltr">%s</code>'%html.escape(s,quote=False) if code else h(s,'html')
        buf.append('<strong>%s</strong>'%x if bold else x)
    for t in p.findall('text'):
        emit(t.text,False)
        for c in t:
            emit(''.join(c.itertext()),c.tag=='bold',c.tag=='code'); emit(c.tail,False)
    return ''.join(buf)
def plain(p): return ''.join(''.join(t.itertext()) for t in p.findall('text'))
isol=lambda s: (RLI+s+PDI) if RTL else s
wrap=lambda inner:('<div dir="rtl" style="direction: rtl; text-align: right;">%s</div>'%inner) if RTL else inner
cd=lambda s:'<![CDATA[%s]]>'%s.replace(']]>',']]]]><![CDATA[>')
LET='אבגד'; LETRE=re.compile(r'^\s*([אבגדA-Da-d])\.\s*')
letter_index=lambda c: LET.index(c) if c in LET else 'abcd'.index(c.lower())
strip_letter=lambda s: LETRE.sub('',s,1)
HDRS=(["מס'","סוג"],["No.","Type"],["#","Type"])
def kind(typ):
    t=typ.strip().lower()
    if typ.startswith('אמריקאית') or t.startswith('multiple'): return 'mc'
    if typ.startswith('התאמה') or t.startswith('match'): return 'match'
    if typ.startswith('השלמה') or t.startswith(('gap','fill','cloze')): return 'gap'
    return None
LABEL_MATCHES=lambda: 'ההתאמות הנכונות:' if RTL else 'Correct matches:'
def tags_for(src):
    ts=list(dict.fromkeys(re.findall(r'\b\d{2}[a-z]\d\b',src))) or [src.split(',')[0].strip()]
    m=re.search(r'(?:שקפ(?:ים|ף)|[Ss]lides?)\s*[\d–ו\- ]*\d',src)
    if m: ts.append(m.group(0).strip())
    return ts
COMB=('<correctfeedback format="html"><text></text></correctfeedback>\n<partiallycorrectfeedback format="html"><text></text></partiallycorrectfeedback>\n'
      '<incorrectfeedback format="html"><text></text></incorrectfeedback>\n<shownumcorrect/>\n')
def main(docxml,outxml,rootname,idp='Q-',ltr=False):
    global IDP,RTL; IDP=idp; RTL=not ltr
    root=ET.parse(docxml).getroot()
    kids=list(root); secs=[]; heading=None
    for e in kids:
        if e.tag=='paragraph' and e.get('heading')=='2': heading=plain(e).strip()
        elif e.tag=='table':
            hdr=[plain(c.find('paragraph')).strip() for c in e.find('row').findall('cell')]
            if hdr[:2] in HDRS: secs.append((heading,e))
    out=[];errs=[];n=0
    for sec,tb in secs:
        mc_=re.search(r'\b\d{2}[a-z]\d\b',sec)
        code=mc_[0] if mc_ else re.split(r'\s[–—-]\s',sec)[0].strip()
        cat='$course$/top/%s/%s'%(isol(rootname),isol(sec))
        out.append('<question type="category">\n<category><text>%s</text></category>\n<info format="html"><text></text></info>\n</question>\n'%xesc(cat))
        for r in tb.findall('row')[1:]:
            cs=r.findall('cell'); P=lambda c:c.findall('paragraph')
            qid=plain(P(cs[0])[0]).strip(); typ=plain(P(cs[1])[0]).strip(); src=plain(P(cs[2])[0]).strip()
            Q=P(cs[3]); A=P(cs[4])
            stem=re.sub(r'\s+',' ',plain(Q[0]).strip())[:45]
            def head(t):
                nm=isol('%s | %s | %s'%(qid,code,h(stem,'plain')))
                return '<question type="%s">\n<name><text>%s</text></name>\n'%(t,xesc(nm))
            def common(qt,fb):
                return ('<questiontext format="html"><text>%s</text></questiontext>\n<generalfeedback format="html"><text>%s</text></generalfeedback>\n'
                 '<defaultgrade>1.0000000</defaultgrade>\n<penalty>0.3333333</penalty>\n<hidden>0</hidden>\n<idnumber>%s</idnumber>\n'
                 %(cd(wrap(qt)),cd(wrap(fb)) if fb else '',xesc(IDP+qid)))
            tg=''.join('<tag><text>%s</text></tag>'%xesc(x) for x in tags_for(src))
            tagxml='<tags>%s</tags>\n'%tg if tg else ''
            global GAP
            k=kind(typ)
            if k=='mc':
                opts=Q[1:]; m=LETRE.match(plain(A[0]))
                if len(opts)!=4 or not all(LETRE.match(plain(o)) for o in opts) or not m: errs.append((qid,'mc')); continue
                ci=letter_index(m.group(1)); expl=strip_letter(plain(A[0]))
                x=head('multichoice')+common('<p>%s</p>'%rich(Q[0]),'<p>%s</p>'%h(expl,'html') if expl.strip() else '')
                x+='<single>true</single>\n<shuffleanswers>true</shuffleanswers>\n<answernumbering>none</answernumbering>\n<showstandardinstruction>0</showstandardinstruction>\n'+COMB
                for i,o in enumerate(opts):
                    ah=wrap(h(strip_letter(plain(o)).strip(),'html'))
                    x+='<answer fraction="%d" format="html"><text>%s</text><feedback format="html"><text></text></feedback></answer>\n'%(100 if i==ci else 0,cd(ah))
            elif k=='match':
                terms=[plain(p).strip() for p in Q[1:]]; pairs=[plain(p).strip() for p in A]
                if len(terms)!=len(pairs) or any('←' not in p for p in pairs) or len(terms)<2: errs.append((qid,'match')); continue
                defs=[p.split('←',1)[1].strip() for p in pairs]
                fb='<p>'+LABEL_MATCHES()+'</p><ul>%s</ul>'%''.join('<li>%s ← %s</li>'%(h(t,'html'),h(d,'html')) for t,d in zip(terms,defs))
                x=head('matching')+common('<p>%s</p>'%rich(Q[0]),fb)+'<shuffleanswers>true</shuffleanswers>\n'+COMB
                for t,d in zip(terms,defs):
                    x+='<subquestion format="html"><text>%s</text><answer><text>%s</text></answer></subquestion>\n'%(cd(wrap(h(t,'html'))),xesc(isol(h(d,'plain'))))
            elif k=='gap':
                rest=[plain(p).strip() for p in Q[1:]]; full=plain(A[0]).strip()
                if rest and rest[0].startswith(('אפשרויות','Options','options')):
                    options=rest[1:]; ci=options.index(full) if full in options else None; expl=''
                else:
                    options=[strip_letter(z) for z in rest]; m=LETRE.match(full); ci=letter_index(m.group(1)) if m else None; expl=strip_letter(full)
                if ci is None or len(re.findall(r'_{3,}',plain(Q[0])))!=1: errs.append((qid,'gap')); continue
                GAP=True; sh=rich(Q[0]); GAP=False
                sh=sh.replace(chr(0xE000),'[[%d]]'%(ci+1))
                fb='<p>%s</p>'%h(expl,'html') if expl.strip() and expl.strip()!=options[ci] else ''
                x=head('gapselect')+common('<p>%s</p>'%sh,fb)+'<shuffleanswers>1</shuffleanswers>\n'+COMB
                for o in options: x+='<selectoption><text>%s</text><group>1</group></selectoption>\n'%xesc(isol(h(o,'plain')))
            else: errs.append((qid,'type '+typ)); continue
            out.append(x+tagxml+'</question>\n'); n+=1
    open(outxml,'w',encoding='utf-8').write('<?xml version="1.0" encoding="UTF-8"?>\n<quiz>\n'+''.join(out)+'</quiz>\n')
    print('questions',n,'categories',len(secs),'errors',errs)
if __name__=='__main__':
    a=[x for x in sys.argv[1:] if x!='--ltr']
    main(*a[:4],ltr='--ltr' in sys.argv)
