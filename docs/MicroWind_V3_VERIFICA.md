# MicroWind V1.0 — conversione di progetto in EasyEDA Pro V3

Stato: **conversione sperimentale con validazione statica; non ancora verificata tramite importazione nel client EasyEDA Pro V3.2.209**.

## Input
- Archivio: `MicroWind_V1_REVISED_V2(1).epro`
- SHA256 input: `5c6a0a9d55ca022c4b179bce252425cc8226c62513541a037e24f74b22051c63`

## Output
- File: `MicroWind_V1_EasyEDA_Pro_V3.epro2`
- SHA256 output: `e159723824ce9f2c1abb3605fead0993f2f4ec69c46667bb9cdcc9e6b10a46e2`
- Contenitore: archivio ZIP formato V3 `.epro2` con `project2.json` e stream `.epru`.

## Controlli eseguiti
- ZIP CRC: corretto
- Tutte le righe `.epru`: JSON envelope + payload validi
- Identificatori documento: 16 cifre esadecimali
- 5 SCH_PAGE, 1 PCB
- 104 componenti PCB e 305 PAD_NET
- Conservati net names, riferimenti saldature, geometria dei fori e cerchio Ø96mm
- Nessuna pista tracciata; circuito non convalidato.

## Limiti
Questo script converte i record strutturali e geometrici principali. Non può assicurare che tutti i record siano interpretati o mostrati identicamente da EasyEDA Pro.
Non sono state eseguite prove reali di apertura/importazione, ERC, DRC o confronto della netlist ricostruita nell'applicazione.
Footprint preliminari non ufficiali del produttore e sezione analogica da validare.

## Importazione nella versione 3.2.209
Dal pannello iniziale usare **Import Professional** selezionando `.epro2` e non creare prima un progetto vuoto.
Verificare la presenza dei fogli POWER, MCU, TEST, ACOUSTIC, PIEZO e della PCB. In caso di errore o schermata vuota, raccogliere log e screenshot.

## Conteggi

| Elemento | Totale |
|---|---:|
| `BOARD.META` | 1 |
| `CONFIG.META` | 1 |
| `DEVICE.META` | 105 |
| `FOOTPRINT.CANVAS` | 104 |
| `FOOTPRINT.LINE` | 130 |
| `FOOTPRINT.META` | 104 |
| `FOOTPRINT.PAD` | 330 |
| `PCB.ATTR` | 312 |
| `PCB.CANVAS` | 1 |
| `PCB.COMPONENT` | 104 |
| `PCB.LAYER` | 8 |
| `PCB.META` | 1 |
| `PCB.NET` | 74 |
| `PCB.PAD` | 12 |
| `PCB.PAD_NET` | 305 |
| `PCB.POLY` | 1 |
| `SCH.META` | 1 |
| `SCH_PAGE.ATTR` | 1140 |
| `SCH_PAGE.CANVAS` | 5 |
| `SCH_PAGE.COMPONENT` | 109 |
| `SCH_PAGE.LINE` | 305 |
| `SCH_PAGE.META` | 5 |
| `SCH_PAGE.TEXT` | 5 |
| `SCH_PAGE.WIRE` | 305 |
| `SYMBOL.ATTR` | 660 |
| `SYMBOL.CANVAS` | 105 |
| `SYMBOL.META` | 105 |
| `SYMBOL.PART` | 105 |
| `SYMBOL.PIN` | 330 |
| `SYMBOL.RECT` | 105 |
| `SYMBOL.TEXT` | 105 |
| `converted.devices` | 105 |
| `converted.footprint_pads` | 330 |
| `converted.footprints` | 104 |
| `converted.holes` | 12 |
| `converted.padnets` | 305 |
| `converted.pages` | 5 |
| `converted.pcb_components` | 104 |
| `converted.sch_components` | 109 |
| `converted.sch_wire_segments` | 305 |
| `converted.symbols` | 105 |

## Anomalie statiche

Nessuna anomalia nei riferimenti PAD_NET esaminati.

Riferimenti di formato: https://github.com/easyeda/easyeda-format-skill ; https://github.com/easyeda/easyeda-eprj3-skill/blob/main/docs/format-reference.md ; https://github.com/eggfly/easyeda-agent-skills/blob/main/spec/epro2-format.md