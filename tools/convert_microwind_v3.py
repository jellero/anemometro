#!/usr/bin/env python3
"""MicroWind V2 -> V3 EasyEDA Pro experimental conversion.

Targets EasyEDA Pro V3 epro2 format from public docs. Full circuit not electrically validated.
Static output only; test inside client required. Does not claim proven importability.
"""
from __future__ import annotations
import json,zipfile,hashlib,collections,datetime,re,math
from pathlib import Path

SRC=Path('/mnt/data/MicroWind_V1_REVISED_V2(1).epro')
DST=Path('/mnt/data/MicroWind_V1_EasyEDA_Pro_V3.epro2')
RPT=Path('/mnt/data/MicroWind_V3_VERIFICA.md')
JSON=lambda x:json.dumps(x,separators=(',',':'),ensure_ascii=False)
HEX=lambda s:hashlib.sha256(str(s).encode('utf8')).hexdigest()[:16]
STAMP=1794776400000 # 2026-11-15 circa, deterministic metadata
CLIENT=HEX('MicroWind-generator-2026-11-15')
MIL=1/0.0254
mm=lambda a:round(float(a)*MIL,5)
old=zipfile.ZipFile(SRC)
meta=json.loads(old.read('project.json'))
boardName=next(iter(meta['boards']))
schid=next(iter(meta['schematics']))
oldpcb=meta['boards'][boardName]['pcb']
boardid=HEX('board:'+boardName)
schuid=HEX('sch:'+schid)
pcbuid=HEX('pcb:'+oldpcb)
oldSheets=meta['schematics'][schid]['sheets']
pageids={str(sh['id']):HEX('page:'+sh['uuid']) for sh in oldSheets}
syms={k:HEX('sym:'+k) for k in meta['symbols']}
foots={k:HEX('foot:'+k) for k in meta['footprints']}
devs={k:HEX('dev:'+k) for k in meta['devices']}
records=[]; docCount=collections.Counter(); counts=collections.Counter(); errors=[]

def line(typ,body,ticket,id=None):
    h={'type':typ,'ticket':ticket}
    if id is not None: h['id']=str(id)
    return JSON(h)+'||'+JSON(body)+'|'

def start(docType,uid):
    docCount[docType]+=1
    records.append(line('DOCHEAD',{'docType':docType,'client':CLIENT,'uuid':uid,'updateTime':STAMP,'version':str(STAMP),'editVersion':'3.2.209'},1))
    return 1

def put(typ,body,id=None):
    global ticket
    ticket+=1
    if id is None:
        id=HEX(f'{currentdoc}:{ticket}:{typ}')
    records.append(line(typ,body,ticket,id)); counts[f'{currentdoc}.{typ}']+=1
    return str(id)

def doc(typ,uid):
    global ticket,currentdoc
    currentdoc=typ; ticket=start(typ,uid)

def canvas(typ):
    if typ in ('PCB','FOOTPRINT'):
        return {'originX':0,'originY':0,'unit':'mm','gridXSize':10,'gridYSize':10,'snapXSize':1,'snapYSize':1,'altSnapXSize':0.1,'altSnapYSize':0.1,'gridType':'NONE','multiGridType':'NONE','multiGridRatio':10,'highlightValue':0.5,'layerBrightness':'NORMAL'}
    return {'originX':0,'originY':0}

def addcanvas():put('CANVAS',canvas(currentdoc),'CANVAS')

def attr(parent,key,value,x=None,y=None,show=False,z=0,layer=None,aid=None):
    b={'x':x,'y':y,'rotation':0,'color':None,'fontFamily':None,'fontSize':None,'fontWeight':False,'italic':False,'underline':False,'strikeout':False,'align':'LEFT_BOTTOM' if x is not None else None,'value':value,'keyVisible':False,'valueVisible':bool(show),'key':key,'fillColor':None,'parentId':parent,'zIndex':z,'groupId':'','locked':False}
    if layer is not None:
        b['layerId']=layer
        b['angle']=b.pop('rotation')
    return put('ATTR',b,id=aid)

def symid_to_device(s):
    for k,v in meta['devices'].items():
        if v.get('attributes',{}).get('Symbol')==s:return k
    return None

def fp_format(x):
    if not isinstance(x,list):return None
    name=x[0]
    ret={'padType':{'ROUND':'ELLIPSE','RECT':'RECT','OVAL':'ELLIPSE','ELLIPSE':'ELLIPSE'}.get(name,'ELLIPSE'),'width':mm(x[1]),'height':mm(x[2])}
    if name=='RECT':ret['radius']=float(x[3]) if len(x)>3 else 0
    return ret

# SYMBOL docs
for sid,sm in meta['symbols'].items():
    raw=[json.loads(v) for v in old.read(f'SYMBOL/{sid}.esym').splitlines()]
    doc('SYMBOL',syms[sid]);
    put('META',{'title':sm['title'],'name':sm['title'],'description':sm.get('desc',''),'docType':sm.get('type',2),'type':sm.get('type',2),'tags':sm.get('custom_tags','[]'),'source':'','version':'1'},'META')
    addcanvas()
    part=next((q for q in raw if q[0]=='PART'),None)
    part_id=''
    put('PART',{'BBOX':part[2].get('BBOX',[-30,-12,30,12]) if part else [-30,-12,30,12]},part_id)
    pinmap={}
    for q in raw:
        if q[0]=='PIN':
            pid=q[1];pinmap[pid]=q
            b={'partId':part_id,'groupId':'','locked':False,'zIndex':6,'display':True,'x':float(q[4]),'y':float(q[5]),'dotX':float(q[4]),'dotY':float(q[5]),'length':float(q[6]),'rotation':float(q[7]),'color':None,'pinShape':'NONE'}
            put('PIN',b,pid)
        elif q[0]=='RECT':
            put('RECT',{'partId':part_id,'groupId':'','locked':False,'zIndex':2,'dotX1':float(q[2]),'dotY1':float(q[3]),'dotX2':float(q[4]),'dotY2':float(q[5]),'radiusX':0,'radiusY':0,'rotation':0,'strokeColor':None,'strokeStyle':'SOLID','fillColor':None,'strokeWidth':1,'fillStyle':'NONE'},q[1])
        elif q[0]=='TEXT':
            put('TEXT',{'partId':part_id,'x':float(q[2]),'y':float(q[3]),'rotation':0,'color':None,'fontFamily':None,'fontSize':6,'fontWeight':False,'italic':False,'underline':False,'align':'CENTER_MIDDLE','value':q[5],'fillColor':None,'zIndex':3,'groupId':'','locked':False},q[1])
    for q in raw:
        if q[0]=='ATTR' and q[2] in pinmap:
            key={'NAME':'Pin Name','NUMBER':'Pin Number','TYPE':'Pin Type'}.get(q[3],q[3])
            attr(q[2],key,str(q[4]),x=float(q[7]),y=float(q[8]),show=bool(q[6]),z=8,aid=q[1])
    counts['converted.symbols']+=1

# FOOTPRINT docs
for fid,fm in meta['footprints'].items():
    raw=[json.loads(v) for v in old.read(f'FOOTPRINT/{fid}.efoo').splitlines()]
    doc('FOOTPRINT',foots[fid])
    put('META',{'name':fm['title'],'title':fm['title'],'description':fm.get('desc',''),'type':4,'tags':fm.get('custom_tags','[]'),'source':'','version':'1','pcb':''},'META')
    addcanvas()
    for q in raw:
        if q[0]=='PAD':
            ptype=q[4];pnum=str(q[5]);hole=q[9]
            hh=({'holeType':'ROUND','width':mm(hole[1]),'height':mm(hole[2])} if hole else None)
            b={'groupId':0,'netName':'','layerId':int(ptype),'num':pnum,'centerX':mm(q[6]),'centerY':mm(q[7]),'padAngle':float(q[8]),'hole':hh,'defaultPad':fp_format(q[10]),'specialPad':[],'padOffsetX':0,'padOffsetY':0,'relativeAngle':0,'plated':bool(hole),'locked':False,'zIndex':-1}
            put('PAD',b,q[1]);counts['converted.footprint_pads']+=1
        elif q[0]=='LINE':
            b={'groupId':0,'netName':'','layerId':int(q[4]),'startX':mm(q[5]),'startY':mm(q[6]),'endX':mm(q[7]),'endY':mm(q[8]),'width':mm(q[9]),'locked':False,'zIndex':-1}
            put('LINE',b,q[1])
    counts['converted.footprints']+=1

# DEVICE docs
for did,dd in meta['devices'].items():
    doc('DEVICE',devs[did])
    da=dict(dd['attributes'])
    if da.get('Symbol') in syms:da['Symbol']=syms[da['Symbol']]
    if da.get('Footprint') in foots:da['Footprint']=foots[da['Footprint']]
    da.pop('symbol_uuid',None);da.pop('footprint_uuid',None)
    put('META',{'name':dd['title'],'title':dd['title'],'description':dd.get('description',''),'type':4,'tags':dd.get('custom_tags','[]'),'source':'','version':'1','attributes':da,'images':'[]'},'META')
    counts['converted.devices']+=1

# BOARD & SCH hierarchy (metadata)
doc('BOARD',boardid)
put('META',{'title':boardName,'sort':1},'META')
doc('SCH',schuid)
put('META',{'name':meta['schematics'][schid]['name'],'board':boardid,'source':'','version':'1'},'META')

# SCH_PAGE documents: preserve all original component positions and net labels
for sh in oldSheets:
    raw=[json.loads(v) for v in old.read(f'SHEET/{schid}/{sh["id"]}.esch').splitlines()]
    doc('SCH_PAGE',pageids[str(sh['id'])]);addcanvas()
    put('META',{'title':sh['name'],'name':sh['name'],'schematic':schuid,'description':'Preliminary: not electrically validated','sort':float(sh['id']),'source':'','version':'1','zIndex':1},'META')
    dattrs=collections.defaultdict(list)
    for q in raw:
        if q[0]=='ATTR':dattrs[q[2]].append(q)
    cids={}
    for q in raw:
        if q[0]=='COMPONENT':
            sid=next((r[4] for r in dattrs[q[1]] if r[3]=='Symbol'),None)
            did=next((r[4] for r in dattrs[q[1]] if r[3]=='Device'),None)
            fid=next((r[4] for r in dattrs[q[1]] if r[3]=='Footprint'),None)
            cid=HEX('schcomp:'+str(sh['id'])+':'+q[1]);cids[q[1]]=cid
            b={'partId':'pid8a0e77bacb214e','x':float(q[3]),'y':float(q[4]),'rotation':float(q[5]),'isMirror':False,'attrs':{'Footprints':'[]','Devices':'[]','DeviceName':JSON({'uuid':devs.get(did,''),'name':meta['devices'][did]['title'],'source':''}) if did in meta['devices'] else None,'FootprintName':None,'Symbols':'[]'},'zIndex':2}
            put('COMPONENT',b,cid)
            if sid in syms:attr(cid,'Symbol',syms[sid],z=1)
            if did in devs:attr(cid,'Device',devs[did],z=2)
            if fid in foots:attr(cid,'Footprint',foots[fid],z=3)
            for a in dattrs[q[1]]:
                if a[3] in ('Symbol','Device','Footprint'):continue
                attr(cid,a[3],a[4],x=float(a[7]),y=float(a[8]),show=bool(a[6]),z=5)
            counts['converted.sch_components']+=1
        elif q[0]=='WIRE':
            wcid=HEX('schwire:'+str(sh['id'])+':'+q[1]);put('WIRE',{'groupId':'','locked':False,'zIndex':40},wcid)
            for segment in q[2]:
                if len(segment)!=4:errors.append(f'Unsupported wire {q[1]}');continue
                x1,y1,x2,y2=segment
                put('LINE',{'fillColor':None,'fillStyle':None,'strokeColor':None,'strokeStyle':None,'strokeWidth':None,'startX':float(x1),'startY':float(y1),'endX':float(x2),'endY':float(y2),'lineGroup':wcid})
                counts['converted.sch_wire_segments']+=1
            attr(wcid,'Relevance','[]')
            for a in dattrs[q[1]]:
                if a[3]=='NET':attr(wcid,'NET',a[4],x=float(a[7]),y=float(a[8]),show=True,z=3)
        elif q[0]=='TEXT':
            put('TEXT',{'x':float(q[2]),'y':float(q[3]),'rotation':0,'color':None,'fontFamily':None,'fontSize':7,'fontWeight':False,'italic':False,'underline':False,'align':'LEFT_BOTTOM','value':q[5],'fillColor':None,'zIndex':1,'groupId':'','locked':False})
    counts['converted.pages']+=1

# PCB layout
raw=[json.loads(v) for v in old.read(f'PCB/{oldpcb}.epcb').splitlines()]
doc('PCB',pcbuid);addcanvas()
put('META',{'name':'MicroWind_V1_96mm_PRELIM','title':'MicroWind_V1_96mm_PRELIM','board':boardid,'description':'Preview only. Not routed. ERC and DRC not validated.','parentId':'','sort':1,'source':'','version':'1'},'META')
for q in raw:
    if q[0]=='LAYER':
        lay={'layerId':int(q[1]),'layerType':q[2],'layerName':q[3],'use':True,'show':True,'locked':False,'activeColor':q[5],'activateTransparency':1,'inactiveColor':q[5],'inactiveTransparency':1}
        put('LAYER',lay,JSON(['LAYER',q[1]]))
netnames=set()
for q in raw:
    if q[0]=='NET':netnames.add(q[1])
put('NET',{},JSON(['NET','']))
for net in sorted(netnames):
    put('NET',{'netType':None,'specialColor':None,'retLine':True,'differentialName':None,'isPositiveNet':False,'equalLengthGroupName':None},JSON(['NET',net]))
# Closed circular PCB outline based on source 2 x 180 degree arcs, center(50,50) r=48mm
put('POLY',{'partitionId':'','groupId':0,'netName':'','layerId':11,'width':mm(0.13),'path':['CIRCLE',mm(50),mm(50),mm(48),1],'locked':False,'zIndex':-1,'polyType':'BOARD_OUTLINE'})
# old board holes: non-connected pads are retained
for q in raw:
    if q[0]=='PAD':
        hole=q[9]
        put('PAD',{'partitionId':'','groupId':0,'layerId':12,'netName':'','num':str(q[5]),'centerX':mm(q[6]),'centerY':mm(q[7]),'padAngle':float(q[8]),'hole':{'holeType':'ROUND','width':mm(hole[1]),'height':mm(hole[2])} if hole else None,'defaultPad':fp_format(q[10]),'specialPad':[],'padOffsetX':0,'padOffsetY':0,'relativeAngle':0,'plated':False,'locked':False,'zIndex':-1},q[1]);counts['converted.holes']+=1

pattrs=collections.defaultdict(list)
for q in raw:
    if q[0]=='ATTR':pattrs[q[3]].append(q)
placed={}
for q in raw:
    if q[0]=='COMPONENT':
        oldcid=q[1];cid=HEX('pcbcomp:'+oldcid);placed[oldcid]=cid
        f0=next((a[6] for a in pattrs[oldcid] if a[5]=='Footprint'),None)
        d0=next((a[6] for a in pattrs[oldcid] if a[5]=='Device'),None)
        ref=next((a[6] for a in pattrs[oldcid] if a[5]=='Designator'),None)
        did=meta['devices'].get(d0,{}).get('title','')
        b={'partitionId':'','groupId':0,'layerId':int(q[3]),'x':mm(q[4]),'y':mm(q[5]),'angle':float(q[6]),'attrs':{'Reuse Block':'','Group ID':'','Channel ID':'','Unique ID':'gge'+str(len(placed)),'DeviceName':JSON({'name':did,'source':'','uuid':devs.get(d0,'')})},'locked':False,'zIndex':-1,'pinSwap':False,'pinSwapInfo':{},'footprintPrimitives':True}
        put('COMPONENT',b,cid)
        if f0 in foots:attr(cid,'Footprint',foots[f0],layer=3,aid=cid+'e15')
        if d0 in devs:attr(cid,'Device',devs[d0],layer=3,aid=cid+'e17')
        if ref:attr(cid,'Designator',ref,x=mm(q[4]),y=mm(q[5])+mm(2.5),show=True,z=4,layer=3,aid=cid+'e16')
        counts['converted.pcb_components']+=1
for q in raw:
    if q[0]=='PAD_NET':
        oldcid,num,net,padId=q[1:5]
        cid=placed.get(oldcid)
        if cid is None:errors.append(f'PAD_NET component missing {oldcid}');continue
        if net not in netnames:errors.append(f'Unknown net {net}')
        put('PAD_NET',{'partitionId':'','padNet':net,'padLen':None,'propagationDelay':None,'attrsMap':{}},JSON(['PAD_NET',cid,str(num),padId]));counts['converted.padnets']+=1
# CONFIG controls default sheet
doc('CONFIG',HEX('config:MicroWind'))
put('META',{'name':'MicroWind_V1','default_sheet':pageids['1']},'META')

# Generate the single V3 project record stream
source='\n'.join(records)+'\n'
project2={'title':'MicroWind_V1_Pro_V3_preliminare','cbb_project':False,'editorVersion':'3.2.209','introduction':'MicroWind V1.0 anemometro ultrasonico','description':'Conversione di struttura EasyEDA Pro V2 a V3. Non testata in editor. No routing.','tags':'[]'}
with zipfile.ZipFile(DST,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as zout:
    zout.writestr('project2.json',json.dumps(project2,ensure_ascii=False,indent=2)+'\n')
    zout.writestr('MicroWind_V1_Pro_V3_preliminare.epru',source)

# Structural validation
with zipfile.ZipFile(DST) as z:
    assert z.testzip() is None
    assert 'project2.json' in z.namelist()
    data=z.read('MicroWind_V1_Pro_V3_preliminare.epru').decode('utf8')
    dhead=[]; allRecs=[]; cur=''
    for n,rawline in enumerate(data.splitlines(),1):
        assert rawline.endswith('|'),f'Missing | at line {n}'
        header,body=rawline[:-1].split('||',1)
        h=json.loads(header);b=json.loads(body);t=h['type']
        if t=='DOCHEAD':cur=b['docType'];dhead.append(b);assert re.fullmatch('[0-9a-f]{16}',b['uuid'])
        else: assert isinstance(h.get('id'),str)
        allRecs.append((cur,t,h,b))
    assert len([d for d in dhead if d['docType']=='SCH_PAGE'])==5
    assert len([d for d in dhead if d['docType']=='PCB'])==1
    assert len([r for r in allRecs if r[0]=='PCB' and r[1]=='PAD_NET'])==305
    assert len([r for r in allRecs if r[0]=='PCB' and r[1]=='COMPONENT'])==104
    assert len([r for r in allRecs if r[0]=='PCB' and r[1]=='NET'])==len(netnames)+1
    padRefs={(d[3]['num'],d[2]['id']) for d in allRecs if d[0]=='FOOTPRINT' and d[1]=='PAD'}
    for _,_,h,b in (r for r in allRecs if r[0]=='PCB' and r[1]=='PAD_NET'):
        kind,c,num,padId=json.loads(h['id'])
        if (num,padId) not in padRefs:errors.append('unmapped pad '+num+' '+padId)

log=['# MicroWind V1.0 — conversione di progetto in EasyEDA Pro V3', '',
     'Stato: **conversione sperimentale con validazione statica; non ancora verificata tramite importazione nel client EasyEDA Pro V3.2.209**.',
     '', '## Input',f'- Archivio: `{SRC.name}`',f'- SHA256 input: `{hashlib.sha256(SRC.read_bytes()).hexdigest()}`',
     '', '## Output',f'- File: `{DST.name}`',f'- SHA256 output: `{hashlib.sha256(DST.read_bytes()).hexdigest()}`',
     '- Contenitore: archivio ZIP formato V3 `.epro2` con `project2.json` e stream `.epru`.', '',
     '## Controlli eseguiti', '- ZIP CRC: corretto', '- Tutte le righe `.epru`: JSON envelope + payload validi',
     '- Identificatori documento: 16 cifre esadecimali', '- 5 SCH_PAGE, 1 PCB', '- 104 componenti PCB e 305 PAD_NET',
     '- Conservati net names, riferimenti saldature, geometria dei fori e cerchio Ø96mm',
     '- Nessuna pista tracciata; circuito non convalidato.', '',
     '## Limiti',
     'Questo script converte i record strutturali e geometrici principali. Non può assicurare che tutti i record siano interpretati o mostrati identicamente da EasyEDA Pro.',
     'Non sono state eseguite prove reali di apertura/importazione, ERC, DRC o confronto della netlist ricostruita nell\'applicazione.',
     'Footprint preliminari non ufficiali del produttore e sezione analogica da validare.',
     '', '## Importazione nella versione 3.2.209',
     'Dal pannello iniziale usare **Import Professional** selezionando `.epro2` e non creare prima un progetto vuoto.',
     'Verificare la presenza dei fogli POWER, MCU, TEST, ACOUSTIC, PIEZO e della PCB. In caso di errore o schermata vuota, raccogliere log e screenshot.',
     '', '## Conteggi', '', '| Elemento | Totale |','|---|---:|']
for k in sorted(counts): log.append(f'| `{k}` | {counts[k]} |')
log+=['','## Anomalie statiche','','\n'.join('- '+x for x in errors[:40]) if errors else 'Nessuna anomalia nei riferimenti PAD_NET esaminati.','',
'Riferimenti di formato: https://github.com/easyeda/easyeda-format-skill ; https://github.com/easyeda/easyeda-eprj3-skill/blob/main/docs/format-reference.md ; https://github.com/eggfly/easyeda-agent-skills/blob/main/spec/epro2-format.md']
RPT.write_text('\n'.join(log)+'\n')
print('CREATED',DST,'bytes',DST.stat().st_size,'sha',hashlib.sha256(DST.read_bytes()).hexdigest());print('DOC COUNTS',dict(docCount));print('ELEMENTS',dict(counts));print('WARNINGS',len(errors),errors[:15]);print('REPORT',RPT)