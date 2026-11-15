#!/usr/bin/env python3
"""Estrae dati documentali da un archivio MicroWind EasyEDA Pro (.epro).
Non esegue controlli ERC/DRC e non produce file per la fabbricazione.
Uso: python3 tools/export_easyeda.py MicroWind_V1_REVISED_V2.epro exports
"""
import csv
import hashlib
import json
import math
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from xml.sax.saxutils import escape


def lines(z, path):
    return [json.loads(t) for t in z.read(path).decode("utf-8").splitlines() if t.strip()]


def csvfile(path, headers, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)


def main():
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("MicroWind_V1_REVISED_V2.epro")
    dest = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("exports")
    dest.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    with zipfile.ZipFile(source) as z:
        project = json.loads(z.read("project.json"))
        pcb_paths = [n for n in z.namelist() if n.endswith(".epcb")]
        if len(pcb_paths) != 1:
            raise ValueError("Il progetto deve contenere un solo PCB")
        pcb = lines(z, pcb_paths[0])
        counts = Counter(r[0] for r in pcb)
        comps = {r[1]: r for r in pcb if r[0] == "COMPONENT"}
        attr = defaultdict(dict)
        for r in pcb:
            if r[0] == "ATTR":
                attr[r[3]][r[5]] = r[6]
        pad_nets = [r for r in pcb if r[0] == "PAD_NET"]
        nets = sorted(r[1] for r in pcb if r[0] == "NET")
        netmap = defaultdict(list)
        by_comp = defaultdict(dict)
        pad_rows = []
        for r in pad_nets:
            _, cid, pin, net, *_ = r
            ref = attr[cid].get("Designator", cid)
            netmap[net].append((ref, str(pin)))
            by_comp[cid][str(pin)] = net
            pad_rows.append((ref, str(pin), net, cid))

        vals, sheets = {}, {}
        schematic = next(iter(project["schematics"].values()))
        sheet_names = {str(i["id"]): i["name"] for i in schematic["sheets"]}
        sheet_rows = []
        for filename in sorted(n for n in z.namelist() if n.endswith(".esch")):
            records = lines(z, filename)
            sa = defaultdict(dict)
            for r in records:
                if r[0] == "ATTR":
                    sa[r[2]][r[3]] = r[4]
            found = 0
            for r in records:
                if r[0] == "COMPONENT" and "Designator" in sa[r[1]]:
                    info = sa[r[1]]
                    ref = info["Designator"]
                    vals[ref] = info.get("Value", "")
                    sheets[ref] = sheet_names.get(Path(filename).stem, "")
                    found += 1
            sheet_rows.append((Path(filename).stem, sheet_names.get(Path(filename).stem, ""), found))

        bom, connectors, footprint_pins, cached_footprints = [], [], [], {}
        for cid, c in comps.items():
            ref = attr[cid].get("Designator", cid)
            fpid = attr[cid].get("Footprint", "")
            filename = "FOOTPRINT/" + fpid + ".efoo"
            if filename not in cached_footprints:
                cached_footprints[filename] = lines(z, filename) if filename in z.namelist() else []
            fps = [p for p in cached_footprints[filename] if p[0] == "PAD"]
            bom.append((ref, vals.get(ref, ""), sheets.get(ref, ""), c[4], c[5], c[6], fpid, len(fps), len(by_comp[cid])))
            for p in fps:
                footprint_pins.append((ref, p[5], p[4], p[6], p[7], json.dumps(p[9]), json.dumps(p[10])))
                if ref in ("JBAT", "JPV", "JP_N", "JP_E", "JP_S", "JP_W"):
                    angle = math.radians(float(c[6]))
                    x = float(c[4]) + float(p[6])*math.cos(angle) - float(p[7])*math.sin(angle)
                    y = float(c[5]) + float(p[6])*math.sin(angle) + float(p[7])*math.cos(angle)
                    connectors.append((ref, str(p[5]), by_comp[cid].get(str(p[5]), ""), round(x,3), round(y,3), json.dumps(p[9]), json.dumps(p[10])))

        holes = [(r[5], r[6], r[7], json.dumps(r[9]), json.dumps(r[10])) for r in pcb if r[0] == "PAD" and str(r[5]).startswith("MH")]
        csvfile(dest/"BOM_componenti.csv", ("Ref","Valore_da_schema","Foglio","X_mm","Y_mm","Rotazione_gradi","Footprint_ID","Pin_footprint","Pin_con_rete"), sorted(bom))
        csvfile(dest/"netlist_pads.csv", ("Ref","Pin","Rete","ID_componente_PCB"), sorted(pad_rows))
        csvfile(dest/"netlist_reti.csv", ("Rete","Numero_collegamenti","Ref_Pin"), [(n,len(netmap[n]),"; ".join("%s:%s"%a for a in sorted(netmap[n]))) for n in nets])
        csvfile(dest/"pin_footprint.csv", ("Ref","Pin","Layer","X_locale_mm","Y_locale_mm","Foro","Piazzola"), sorted(footprint_pins))
        csvfile(dest/"connettori_saldatura.csv", ("Ref","Pin","Rete","X_mm","Y_mm","Foro","Piazzola"), sorted(connectors))
        csvfile(dest/"fori_meccanici.csv", ("Ref","X_mm","Y_mm","Foro_nel_record_PAD","Piazzola_nel_record_PAD"), sorted(holes))
        csvfile(dest/"fogli_schema.csv", ("ID","Foglio","Componenti_con_designatore"), sorted(sheet_rows))

        def point(x,y):
            return 550+(float(x)-50)*10, 590+(50-float(y))*10
        svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 1180">',
               '<rect width="1100" height="1180" fill="#f5f7f8"/>',
               '<text x="550" y="50" text-anchor="middle" font-family="sans-serif" font-size="27" fill="#183e36">MicroWind V1.0 — disposizione da .epro</text>',
               '<circle cx="550" cy="590" r="480" fill="#15483b" stroke="#83b69a" stroke-width="4"/>']
        for p in pcb:
            if p[0]=="PAD" and str(p[5]).startswith("MH"):
                x,y=point(p[6],p[7])
                svg.append('<circle cx="%.2f" cy="%.2f" r="12" fill="#e7c07b"/>'%(x,y))
        for cid,c in comps.items():
            ref=attr[cid].get("Designator",cid)
            fpid=attr[cid].get("Footprint","")
            fps=cached_footprints.get("FOOTPRINT/"+fpid+".efoo", [])
            for p in fps:
                if p[0]!="PAD": continue
                angle=math.radians(float(c[6]))
                xx=float(p[6])*math.cos(angle)-float(p[7])*math.sin(angle)
                yy=float(p[6])*math.sin(angle)+float(p[7])*math.cos(angle)
                x,y=point(c[4]+xx,c[5]+yy)
                dim=p[10] if isinstance(p[10],list) else []
                size=max(2.5,min(float(dim[1])*5,14)) if len(dim)>1 and isinstance(dim[1],(float,int)) else 4
                color="#efbd73" if p[4]==12 else "#b4cec3"
                if dim and dim[0]=="RECT":
                    svg.append('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" fill="%s"/>'%(x-size/2,y-size/2,size,size,color))
                else:
                    svg.append('<circle cx="%.2f" cy="%.2f" r="%.2f" fill="%s"/>'%(x,y,size/2,color))
            if not ref.startswith(("R_","C_","D_CLAMP")):
                x,y=point(c[4],c[5])
                svg.append('<text x="%.2f" y="%.2f" text-anchor="middle" font-family="sans-serif" font-size="13" fill="white">%s</text>'%(x,y-12,escape(ref)))
        svg.append('<text x="550" y="1120" text-anchor="middle" font-family="sans-serif" font-size="19" fill="#183e36">Centri e piazzole da .epro · NON rendering CAD · NON fabbricare</text></svg>')
        (dest/"pcb_posizionamento_estratto.svg").write_text("\n".join(svg)+"\n",encoding="utf-8")

        readme = ("# Esportazioni tecniche MicroWind V1.0\n\n"
                  "Estratte automaticamente dal progetto `"+source.name+"`. SHA-256: `"+digest+"`.\n\n"
                  "**BOZZA, NON FABBRICARE.** Dati documentali, non ERC/DRC o Gerber.\n\n"
                  "- Fogli: "+", ".join(sheet_names.values())+".\n"
                  "- Componenti: "+str(len(comps))+"; reti: "+str(len(nets))+"; PAD_NET: "+str(len(pad_nets))+".\n"
                  "- Fori/pad meccanici MH: "+str(len(holes))+"; piste TRACK: "+str(counts["TRACK"])+"; via VIA: "+str(counts["VIA"])+".\n"
                  "- Profilo nominale: cerchio Ø96 mm, centro (50,50) mm.\n\n"
                  "CSV disponibili: BOM_componenti, netlist_pads, netlist_reti, pin_footprint, "
                  "connettori_saldatura, fori_meccanici, fogli_schema.\n\n"
                  "L'SVG è una visualizzazione ricostruita da coordinate e piazzole, non una vista CAD. "
                  "Quote, fori e pad devono essere verificati nell'editor EasyEDA Pro.\n")
        (dest/"LEGGIMI.md").write_text(readme,encoding="utf-8")
        print("Estratti",len(comps),"componenti,",len(nets),"reti,",len(pad_nets),"pad-rete")

if __name__=="__main__":
    main()
