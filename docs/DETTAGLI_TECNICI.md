# MicroWind V1.0 — Dettagli tecnici verificati sul sorgente

> **STATO: PROGETTO PRELIMINARE — NON FABBRICARE.** Questo documento riporta informazioni **estratte** dall'archivio originale EasyEDA Pro, non certificazioni di funzionalità.

## File sorgente

- File: [MicroWind_V1_REVISED_V2.epro](../MicroWind_V1_REVISED_V2.epro)
- SHA-256: `5c6a0a9d55ca022c4b179bce252425cc8226c62513541a037e24f74b22051c63`
- Contenitore: ZIP EasyEDA Pro, con `project.json`, simboli `.esym`, footprint `.efoo`, schemi `.esch` e PCB `.epcb`.
- Editor indicato nell'header PCB: `2.2.48.10` (non è una verifica di compatibilità in EasyEDA).
- Fogli schema: **POWER, MCU, TEST, ACOUSTIC, PIEZO**.
- Record PCB: **104 COMPONENT, 73 NET, 305 PAD_NET, 12 PAD meccanici, 2 ARC di contorno**.
- Record PCB `TRACK` = **0**; `VIA` = **0**; nessun piano di rame/riempimento nel file PCB esaminato.

## Geometria

- Contorno: cerchio **Ø96 mm**, centro **(50, 50) mm**, definito con due archi su layer **OUTLINE** (11).
- Piazzole meccaniche nel file PCB: **MH1…MH12** sul layer **MULTI** (12).
- Il layer PCB contiene la posizione dei 104 componenti; la definizione di ogni footprint è incorporata nell'archivio.
- **Importante:** i parametri dei fori dei record PAD e gli ingombri dei footprint vanno confermati nell'editor CAD; non sono quote finali certificate per la foratura CNC.

## Blocchi funzionali e riferimenti

| Funzione | Riferimenti nel progetto | Valori/nome inseriti |
|---|---|---|
| MCU / radio | UCPU | ESP32-C6-MINI-1-N4 |
| Ricarica | UCHG | BQ25185DLHR |
| Regolatore 3,3 V | UREG | TPS63802DLAR |
| Driver TX | UDRV_A, UDRV_B | MAX3222EIPWR |
| Multiplexer RX | UMUX | SN74LV4052A |
| Amplificatore RX | UAMP | MCP6022-I/SN |
| Comparatore RX | UCMP | MCP6561 |
| Induttore | L1 | 0u47 |
| Protezioni ingresso PV | D1, D2 | SS14, SMBJ12A |
| Sensore ambiente | NTC1 | 10k_B3950_0603 |
| Trasduttori / cablaggio | JP_N, JP_E, JP_S, JP_W | PIEZO_*_SOLDER |
| Diagnostica | TP_* | 3V3, GND, EN, BOOT, PG, ADC_RX, RX_CMP, UART, USB |

I valori sono stringhe inserite nello schema; **non garantiscono l'esistenza, l'idoneità o il pinout effettivo dei componenti**.

## Cavi da saldare direttamente

| Ref | Pin | Rete nel file PCB | Funzione |
|---|---:|---|---|
| JPV | 1 | PV_RAW | pannello PV+ |
| JPV | 2 | GND | pannello PV− |
| JBAT | 1 | BAT | batteria + |
| JBAT | 2 | GND | batteria − |
| JBAT | 3 | TS_BAT | filo NTC batteria |
| JP_N | 1 / 2 | PZ_N / GND | sensore nord |
| JP_E | 1 / 2 | PZ_E / GND | sensore est |
| JP_S | 1 / 2 | PZ_S / GND | sensore sud |
| JP_W | 1 / 2 | PZ_W / GND | sensore ovest |

**Coordinate e geometrie delle singole piazzole**: vedi [`exports/connettori_saldatura.csv`](../exports/connettori_saldatura.csv) dopo l'esportazione automatica. Le coordinate sono nel riferimento nativo del progetto, non in coordinate utensile.

## Alcune reti importanti, verificate tramite PAD_NET

- `BAT` collega JBAT:1, UCHG:2, C_BAT:1 e R_BATTOP:1.
- `TS_BAT` collega JBAT:3 e UCHG:6.
- `PV_RAW` collega JPV:1 e D1:1; `PV_IN` collega D1:2, D2:2, UCHG:10, C_PVIN:1 e R_SOLTOP:1.
- `SYS` collega UCHG:1, UREG:1/10, C_SYS:1, C_REGIN:1.
- `3V3` alimenta le sezioni MCU, driver, RX e test; vedere la netlist completa.
- `USB_DP` = UCPU:18 / TP_USB_DP:1; `USB_DM` = UCPU:17 / TP_USB_DM:1.
- `UART_TX` = UCPU:31 / TP_UARTTX:1; `UART_RX` = UCPU:30 / TP_UARTRX:1.
- `PZ_N/E/S/W`: ognuna va alla propria coppia di piazzole e ai rami TX/RX corrispondenti.
- `RX_MUX`: UMUX:13 e UAMP:3; `RX_CMP`: UCMP:1, UCPU:9 e TP_CMPRX:1.

**Non confondere il numero di piazzola nel file con una conferma del pinout da datasheet.**

## Esportazioni e riproducibilità

Lo script [`tools/export_easyeda.py`](../tools/export_easyeda.py) legge l'archivio sorgente e genera automaticamente: BOM completa, netlist per piazzola, netlist per rete, geometrie dei footprint, coordinate dei connettori a saldare, piazzole MH, lista fogli e un SVG derivato dalle coordinate PCB. I risultati sono nei file della cartella [`exports/`](../exports/).

## Verifiche ancora obbligatorie

1. Validare schema e coerenza elettrica (ERC): pinout ESP32-C6, MAX3222E, BQ25185, TPS63802, amplificatore, comparatore, multiplexer.
2. Verificare funzionamento driver trasduttori e front-end analogico a 40 kHz, livelli, tempi e protezioni.
3. Tracciare piste e via; definire alimentazioni e piani massa; eseguire DRC.
4. Controllare distanze meccaniche, fori, trasduttori, riflettore, keep-out antenna e integrità RF.
5. Verificare profilo di ricarica e protezione della cella **LiFePO₄ 1S** con datasheet e misura reale; il valore nominale di alcuni componenti non basta a confermare la compatibilità.
6. Controllare correnti, sezioni dei fili e distanza di isolamento lato pannello.
7. Validare esportazione Gerber/Excellon e la distinta commerciale dei footprint prima di ordinare.

Nessuna simulazione, misura, importazione in EasyEDA, ERC o DRC è stata eseguita durante la presente estrazione.
