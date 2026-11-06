# Adressbücher Basel 1841–1862 — Projektplan

Stand 06.11.2026. Drei Bände des «Adreßbuchs der Stadt Basel» (1841, 1850, 1862;
Staatsarchiv Basel-Stadt STA H 43 17, 20, 22, gemeinfrei) werden mit derselben Methode wie
die Aarauer Adressbücher 1884–1899 (`~/Repos/adressbuecher-aarau`) zu einem
Informationssystem über Personen, Haushalte, Gebäude, Firmen und Institutionen. Die
Zwischenresultate sind CSV mit den Spalten aus `docs/schema.md` (identisch mit Aarau, plus
die Basler Hausnummern-Spalten), damit beide Korpora in einen Graphen (CIDOC-CRM 7.1.3 +
SDHSS, Vokabular-Register und Bestandsgraph-Bauer aus `agentic_historian`) zusammengeführt
werden können.

## 1. Befund: die Quellen

Lieferung: je Band ein Ordner des Digitalen Lesesaals (`BS_<jahr>_<record>-<id>/`) mit
einem JPEG je Seite (**400 dpi, RGB, ~2400×3400 px, 0,8–1,5 MB**) und einem Deckblatt
`01_Inhalt.pdf` (Signatur, Titel, Permalink, Rechtestatus). Keine PDFs, kein Textlayer.
Zusammen 873 Seiten, 1,0 GB. Die Bilder werden byteidentisch unter dem Seitenschlüssel
`<jahr>_p<nnn>` übernommen (`scripts/01_render_pages.py`); `00_volumes.csv` hält je Band
einen SHA-256 über alle Seitendateien, Signatur und Permalink. Gegenüber Aarau (120 dpi)
ist die Auflösung mehr als ausreichend; die Scans zeigen den schwarzen Scanhintergrund und
je nach Seite den Rand der Gegenseite.

| Band | Seiten | Satz | Signatur / Permalink | Abfolge (PDF-Seiten; vollständig in `data/csv/01_pages.csv`) |
|---|---:|---|---|---|
| 1841 | 202 | Fraktur | STA H 43 17 · [dls 1225921](https://dls.staatsarchiv.bs.ch/records/1225921) | Einband 1 · leer 2–5 · Titel/Erklärung 6–7 · **Nummernbuch 8–83** (gedr. 1–76; Grosse Stadt: St. Johann-Q. 8, Spahlen-Q. 18, Steinen-Q. 30, Aeschen-Q. 40, St. Alban-Q. 49, Stadt-Q. 60; Kleine Stadt 70: St. Bläsi-Q. 70, Riehen-Q. 71) · **Register 84–145** (gedr. 1–62; Gross-Basel 84, Klein-Basel 134) · Inserate 146–147 · Nachschrift Locher Okt. 1840 148 · Druckermarken 149, 151 · **Nachtrag März 1841** (Jenni-Erlacher): Titel 152, Berichtigungen/Häuserkäufe 153, Register 154–178 (gedr. 1–25; Klein-Basel 174), **Bänne 179–197** (gedr. 26–44: Gross-Basel-Bann 179, Bläsi-Bann 189, Riehen-Bann 193) · leer 198–201 · Einband 202 |
| 1850 | 165 | Fraktur | STA H 43 20 · [dls 1225925](https://dls.staatsarchiv.bs.ch/records/1225925) | Einband 1 · leer 2–5 · Titel 6 (hrsg. J. G. Wölfflin, Druck J. W. Baur sel. Erben) · Vorrede 8–9 · **Nummernbuch 11–108** (gedr. 1–95; unbedruckte Blätter 23, 30, 37; Grosse Stadt: St. Johann 11, Spahlen 24, Steinen 40, Aeschen 53, St. Alban 65, Stadt 80; Kleine Stadt 92: Bläsi, Riehen 93, St. Bläsy 99; S. 108 Etablissements vor den Thoren) · **Register 109–142** (gedr. 96–129, 2-spaltig) · **Ragionen-Firmen 143–157** (gedr. 130–144) · Behörden-Präsidenten 158–159 · leer 160–164 · Einband 165 |
| 1862 | 506 | Fraktur | STA H 43 22 · [dls 1225927](https://dls.staatsarchiv.bs.ch/records/1225927) | Einband 1 · leer 2–5 (Exlibris Paul Koelner) · Titel 6 (Verlag Otto Stuckert, «mit einem Plane der Stadt»; Plan fehlt im Scan) · Vorwort 7 · Inhalt 8 · **Behörden 10–39** (röm. VII–XXXVI, 2-spaltig) · **Ragionenbuch 40–58** (XXXVII–LV, Tabelle 3 Spalten) · Berichtigungen/Neubauten 59–65 (LVI–LXII) · Quartiere und Strassen 66–69 (gedr. 1–4) · **Häuserverzeichnis 70–275** (gedr. 5–210, Tabelle 5 Spalten; Grosse Stadt 70, Kleine Stadt 229) · Hausnamen-Register 276–289 (211–224) · Häuserbesitzer-Register 290–317 (225–252) · **Bürger und Einwohner 318–428** (253–363, 2-spaltig) · **Berufsarten 429–459** (364–394, 2-spaltig) · Boten/Audienzen 460 · Inserate 462–501 · leer 502–505 · Einband 506 |

Die drei Bände sind **drei verschiedene Werke** mit je eigener Eintragsgrammatik (Sichtung
06.11.2026 an Einzelseiten):

1. **1841, «Nummern- und Adreßbuch»** (Erklärung auf PDF 7): zwei Theile. Theil 1,
   das *Nummernbuch*, ist nach Hausnummern und Strassen geordnet, abgetheilt nach Grosser
   und Kleiner Stadt; je Nummer der Eigentümer (mit `*` bezeichnet; «der Stadt gehörend»,
   «dem Kanton geh.») und darunter eingerückt die Bewohner; Strassentitel als
   Zwischentitel, Spaltenkopf «Nro.». Theil 2, das *alphabetische Register*, wiederholt
   dieselben Namen mit Wohnung: `Name[-Allianz], Vorname, [Stand,] Beruf. Nummer Strasse.`
   — die Hausnummer steht **vor** der Strasse (`292 Spahlen-Vorstadt`, `754 a Kohliberg`).
   Ausserhalb der Mauern tragen Einträge einen Zusatz «U. B.» / «O. B.» (Bedeutung in
   Welle 0 zu klären; vermutlich unterer/oberer Bann oder Bezirk).
2. **1850**: *Nummernbuch* nach Quartieren (Kolumnentitel wie «St. Alban- und
   Stadt-Quartier», Nummern bis über 1600, Strassentitel, Bewohner eingerückt,
   «Obrigkeitlich», «Abgebrochen»); *alphabetisches Register* zweispaltig und kompakt:
   `Name, Vorname, Beruf` mit der Hausnummer rechtsbündig am Zeilenende, `*` vor der
   Nummer = Eigentümer, Buchstabenzusätze (`1311A`, `754L`), eingerückte Folgezeilen für
   weitere Personen desselben Familiennamens (`  Wittwe, Elis. 1597`) und `-Bernet, Jb.`
   für Allianznamen; dazu ein *Firmenverzeichnis* (`Nummer Vorname Name … Inhaber`).
3. **1862** (Vorwort «Basel im September 1862», mit beigegebenem Stadtplan): römisch
   paginierter Vorspann mit *Behörden* (Geistlichkeit, Gemeindsbehörden, Zünfte …),
   *Ragionenbuch* als dreispaltige Tabelle (Handlungsfirma | Interessenten u. Firmaführer |
   Natur des Geschäfts) und *Verzeichniß der Straßen* (S. LVI, mit Berichtigungen und
   Neubauten); dann arabisch paginiert das **tabellarische Häuserverzeichnis** nach Strassen
   (Neue Haus-Nr. | Quartier I–VIII | Alte Haus-Nro. | Name des Hauses | Hauseigenthümer
   und Bewohner) — das Jahr der **neuen Hausnummerierung je Strasse** mit Konkordanz zu den
   alten stadtweiten Nummern, also der Schlüssel, um 1841/1850 (alte Nummern) und 1862
   (neue Nummern) auf dieselben Gebäude zu bringen; dann das *Verzeichniß der Bürger und
   Einwohner* zweispaltig (`Name-Allianz, Vorname, Beruf. Strasse Nr.`, Gedankenstrich =
   wiederholter Familienname, `-Allianz` nach dem Gedankenstrich); zuletzt *Inserate* auf
   gelbem Papier (Antiqua und Fraktur gemischt).

Befund Welle 0 (06.11.2026, alle 873 Seiten klassifiziert, Grenzseiten auf der
Einzelseite bestätigt): Die gedruckten Seitenzahlen gehen auf (1862: gedruckt = PDF − 65
arabisch, PDF − 3 römisch); unbedruckte Blätter in 1850 (PDF 23, 30, 37) sind keine
Lücken. Der in 1850 und 1862 angekündigte Stadtplan fehlt in beiden Scans. Zeichen:
in 1841 bezeichnet `*` laut Berichtigung (PDF 153) die **nicht** vom Eigentümer
bewohnten Gebäude (die Erklärung auf PDF 7 sagt das Gegenteil); in 1850 bedeutet `*` vor
der Nummer im Register **Kleinbasel** (eigene Nummernfolge ab 1, Vorbemerkung PDF 109),
nicht Eigentümer; Buchstaben an Nummern (`267A`, `A 1`, `BC 9`) sind Teilhäuser ohne
gedruckte Erklärung. 1862 erklärt die Quartiere I–VIII auf PDF 66 (I St. Johann,
II Spalen, III Steinen, IV Aeschen, V St. Alban, VI Stadt, VII Bläsi, VIII Riehen) und
setzt Eigentümer in grösserer, Bewohner in kleinerer Schrift. «U. B.» / «O. B.» im
Gross-Basel-Bann 1841 ist nach Lage der Strassen Unterer/Oberer Bann. Das 1850er
Exemplar trägt viele handschriftliche Nachträge und Streichungen im Nummernbuch; 1841
ist in den Nachtragsblättern (PDF 151–153) beschädigt, aber lesbar.

Was die Verarbeitung bestimmt: alles Fraktur (die Aarauer Wahl der Leser für Fraktur ist
der Ausgangspunkt), Tabellen in 1862 (der Prompt gibt Tabellenzeilen mit ` | ` vor),
eingerückte Zeilen, die in 1850 *eigene* Einträge sind und nicht Fortsetzungen, Hausnummern
vor (1841/1850) oder nach (1862) der Strasse, und handschriftliche Streichungen und
Nachträge im Exemplar (z. B. 1850 PDF 80).

## 2. Befund: was `agentic_historian` liefert

Unverändert gegenüber Aarau (`~/Repos/adressbuecher-aarau/PLAN.md`, Abschnitt 2): Batch-ATR
über den MCP-ATR-Server auf tei (Gemini extern mit versioniertem Prompt; GPUStack-Modelle
über die CLI vom Repo-Stamm `~/agentic_historian`), `compare_readings`,
`score_ground_truth`, Vokabular-Register, Graph-Bauer, Prüfung, QLever, MCP. Neu hier ist
nur der Prompt `prompts/adressbuch_basel_atr.md` (auf tei unter
`agentic_historian/prompts/`), der von `adressbuch_atr_v2.md` ausgeht und Tabellenzeilen,
eingerückte Folgeeinträge, ⸗ als `-` sowie die Fraktur-Verwechslungen O/D, B/V, K/R, J/I
regelt. Die Aarauer Erkenntnisse gelten als Vorgabe: Gemini 3.8 Flash liest Fraktur unter
1 % CER und löst Spalten mit `[spalte 2]`; kraken bricht auf zweispaltigen Seiten;
`qwen3.8-27b` denkt mit Default-Reasoning bis zum Token-Deckel; `qwen3-vl-30b-a3b-instruct`
ist mit 3–5 % auf Fraktur der schnelle zweite Leser.

Die Basler Liegenschaften-Karte von DH Bern (`https://dhbern.github.io/basler-liegenschaften-interaktiv`,
Löffelscher Stadtplan 1862 als WMS, Polygone 1615) ist das Vorbild für die
Geovisualisierung und — weil sie dasselbe Jahr 1862 abbildet — ein möglicher Anker für
die Verortung der neuen Hausnummern.

### Befund Welle 1 — ATR-Probe (06.11.2026, 20 Seiten, `data/csv/probe_pages.csv`)

Probe: je Band geschichtet (1841: 3 Nummernbuch, 3 Register; 1850: 2 Nummernbuch,
2 Register, Firmen, Behörden; 1862: 2 Häuserverzeichnis-Tabellen, 2 Einwohner, Ragionenbuch,
Behörden, Berufsarten, Häuserbesitzer), auf tei unter
`data/nextcloud/adressbuecher-basel/probe/`. Prompt `adressbuch_basel_atr.md`
(Datei-SHA-256 `897b7ea3…`, Runner-Digest `@4d8d9365`).

**Gemini 3.8 Flash** (`basel-probe-gemini-v1`, MCP, `reasoning=low`): 20/20 Seiten, keine
abgeschnitten, 2 008 Zeichen und 9,5 s je Seite (3 min für die Probe). Das Tabellenformat
(` | ` zwischen den Zellen, Bewohner eingerückt) kommt auf dem Häuserverzeichnis 1862 und
dem Ragionenbuch sauber; zweispaltige Seiten mit `[spalte 2]`; Einrückungen des
Kompaktregisters 1850 bleiben erhalten; Streichungen als `[handschriftlich: gestrichen]`.
Systematisch: die Fraktur-Initiale «J.» wird als «I.» gelesen («I. I.» statt «J. J.»;
der Parser normalisiert das), `ß` einmal als `sz`, enge Setzung («St.Andreasplatz») wird
mit Spatium geglättet, «àWengen» ohne Accent. Sonst auf den vier GT-Seiten je 0–3 Fehler.

**GPUStack** (`basel-probe-gpustack-v1`, CLI von tei, Reasoning Modell-Default):
`qwen3-vl-30b-a3b-instruct` 20/20 in 3,2 min (6 Seiten/min), aber eine Seite (1841
PDF 27) in einer Wiederholungsschleife bis zum Token-Deckel («5 5 5 …»), zweispaltige
Seiten **zeilenweise nebeneinander** statt Spalte für Spalte, Tabellen als Markdown mit
`| | | |`-Leerzellen, Bewohnerzeilen verschoben oder weggelassen. `qwen3.8-27b` 20/20 in 40,7 min
(98,5 s je Seite), zwei Seiten am Token-Deckel (1841 PDF 65 abgeschnitten, 1862 PDF 25
Behörden leer: 8 192 Tokens Nachdenken, kein Text) — das Reasoning-Problem aus Aarau.
Dafür trennt es die Spalten korrekt (1862 PDF 355: 2,3 %) und hält das Tabellenformat
halbwegs ein (13,7 % auf der Tabelle, vor allem Zellen- und Zeilenordnung).

**Ground Truth** (`data/gt/`, 4 Seiten, `provenance.csv`): 1841 PDF 110 (Register),
1850 PDF 120 (Kompaktregister 2-spaltig), 1862 PDF 139 (Häuserverzeichnis-Tabelle), 1862
PDF 355 (Einwohner 2-spaltig). Entstanden aus der Gemini-Lesung, jede Abweichung zu
qwen3-vl am Bildstreifen entschieden, dann die Seite gegen das Bild gelesen — von vier
Hilfsagenten (Claude), nicht von einer Person; Gemini kommt dadurch zu gut weg. Von 129
Abweichungen zwischen beiden Lesern lagen 126 bei qwen, 3 bei Gemini.

Zeichenfehlerrate (CER, Levenshtein auf dem normalisierten Seitentext: ſ→s, ⸗/=→-,
`[spalte 2]` und Lesernotizen entfernt):

| Leser | 1841 PDF 110 Register | 1850 PDF 120 Register 2-sp. | 1862 PDF 139 Tabelle | 1862 PDF 355 Einwohner 2-sp. | s/Seite |
|---|---:|---:|---:|---:|---:|
| `gemini-3.8-flash` (extern) | 0,000* | 0,011* | 0,002* | 0,000* | 9,5 |
| `qwen3-vl-30b-a3b-instruct` (GPUStack) | 0,027 | 0,040 | 0,195 | 0,768 | 9,7 |
| `qwen3.8-27b` (GPUStack) | 0,023 | 0,025 | 0,137 | 0,023 | 98,5 |

\* GT geht von dieser Lesung aus, Zahl nach unten verzerrt. Die hohen Werte von
qwen3-vl auf 1862 sind Reihenfolge (Spalten nebeneinander, Tabellenzellen), nicht
Buchstaben: auf Wortebene liest es Fraktur mit 3–4 % (V/B, K/R, ß/ck, tz, ſ/f).

**Entscheid (Vorschlag, 06.11.2026):** Hauptleser für alle 798 Seiten (alles ausser
`leer` und `inserate`; `data/csv/fullrun_pages.csv`, Ordner `fraktur/` auf tei) ist
**Gemini 3.8 Flash** (Lauf `basel-gemini-v1`, MCP). Zweiter Leser wie in Aarau für
Fraktur `qwen3-vl-30b-a3b-instruct` (`basel-qwen3vl30b-v1`, CLI, nohup) — brauchbar als
Zweitmeinung zum Wortlaut auf einspaltigen Seiten (Nummernbuch 1841/1850, Register
1841), auf zweispaltigen und Tabellenseiten nur über eine zeilenweise Zuordnung. **Zur
Entscheidung der Projektleitung:** `qwen3.8-27b` wäre auf den zweispaltigen Seiten (1850
Register, 1862 Einwohner/Besitzer/Berufe: ~190 Seiten) der bessere Zweitleser (2–3 %
statt Spaltensalat), kostet aber 100 s je Seite (~5 h für diese Seiten, ~22 h für alle)
und bricht ohne Reasoning-Abschaltung auf einzelnen Seiten ab; Vorschlag: nach dem
qwen3-vl-Lauf nur die zweispaltigen Seiten mit qwen3.8 nachlesen (`basel-2sp-qwen38-v1`).
**Volllauf abgeschlossen 06.11.2026** (gestartet 14:42, Gemini MCP-Job
`20261106T134222-cb1e6c` fertig 16:55, qwen3-vl CLI fertig 16:35): Gemini 798/798 Seiten,
8,8 s und 2 078 Zeichen je Seite, keine abgeschnitten, nur die drei Einbandseiten leer;
qwen3-vl 798/798, 6,6 s je Seite, **15 Seiten in Wiederholungsschleifen am Token-Deckel**
(1841 PDF 31, 37, 49, 87, 113, 173, 195; 1850 PDF 145; 1862 PDF 50, 51, 61, 91, 102, 156,
174). `02_lines.csv`: 124 526 Zeilen beider Leser. Wichtig für den Parser: im Volllauf
rückt Gemini Folgeeinträge und Fortsetzungszeilen **nicht** mehr ein (in der Probe schon);
der Parser erkennt sie darum inhaltlich (siehe Welle 2).

**Welle 2, Volllauf** (`make fullrun-parse geo`, Gemini-Lesung aller Seiten, 06.11.2026):
`04_entries.csv` **13 828 Adresszeilen** (1841: 3 485, 1850: 2 853, 1862: 7 490) mit 98 %
«high», 263 «medium» (Firmen, unsichere Allianz-/Vornamen-Trennung im Register 1850,
Adressen ohne Nummer), 5 «review». `04_berufe.csv` 2 933 Einträge des Berufsregisters
1862 in 314 Rubriken (Unterrubriken «a) Für Bänder- und Seidewaaren» als «medium»).
`05_buildings.csv` **7 986 Gebäude** (7 958 «high»; 1841: 2 151, 1850: 2 102, 1862: 3 733
mit Grosser und Kleiner Stadt) und `05_residents.csv` 7 010 Bewohner. Neu gegenüber der
Probe: das Register 1850 lässt den Familiennamen bei Folgeeinträgen weg und die Lesung
rückt nicht ein — der Parser erkennt Folgeeinträge über Vorname/Stand/Abkürzung und
akzeptiert als neue Familiennamen nur die längste alphabetisch nicht fallende Teilfolge
der Seite (Register sind alphabetisch; 0 Brüche im Ergebnis); zwei Einträge in einer
Lesungszeile werden getrennt, «Comptoir NNN» als zweite Adresse; 1841 Stern nach der
Nummer, Hausname nach der Strasse («Freie Straße. Zunft der Hausgenossen»),
Buchstabenfolgen «561 c d», Bereiche «931—933», «sel. Wittwe», Strasse ohne Nummer,
Fortsetzungen ohne Einzug (reine Adresszeilen); Nummernbuch «No. 1 (St. Johannthor)»,
Buchstaben nach dem Stern «399 * a», ½, Komma-Reihen, Ditto-Zeilen, Bewohner ohne Einzug,
Leerseiten als Folgeseiten. 13 Gebäudenummern kommen in der Quelle doppelt vor (z. B.
1841 Nr. 404) und bleiben doppelte `building_id`.

**Welle 2, erster Stand** (`make probe-parse`, Gemini-Lesung der Probeseiten):
`scripts/04_parse.py` löst auf den neun Registerseiten 426 Adresszeilen auf, 420 «high»,
1 «medium» (Firma), 5 «review» (1850: eingerückte Folgeeinträge am Seitenanfang ohne
vorangehenden Familiennamen — in der Folge der Seiten gelöst). Grammatiken: 1841 Nummer
vor der Strasse, Bann-Zusatz `U. B.`/`O. B.`, «geb. Name» als Geburtsname, «Jungfer»;
1850 Nummer am Zeilenende, `*` = Kleinbasel, eingerückte Zeilen als eigene Einträge mit
geerbtem Familiennamen, `-Allianz`; 1862 Adresse nach dem letzten Punkt («St. »
gehört zur Adresse), Gedankenstrich, `Wb.`/`Jgfr.` als Stand. `scripts/05_buildings.py`
liest die sieben Gebäudeseiten zu 161 Gebäuden (158 «high») mit 113 Bewohnern:
Teilhaus-Buchstaben (`A 751`, `BC 754`), Nummernbereiche («513 u. 514»), Ditto-Zeichen,
Streichungen, «Siehe Nr. …»-Verweise als Notiz, und für 1862 die fünf Tabellenspalten
(`house_no_new`, `quarter`, `house_no_old`, `house_name`), Strasse aus Zwischentitel oder
Kolumnentitel, `building_id` mit Strasse (1862) beziehungsweise Stadtteil `GB`/`KB`
(1850). Offen: Ditto-Zeilen «” ” Isaak Dreyfuß» (1841 Magazine), Firmenzusätze
«u. Steigmeyer» (1850), Zusammenführung der Fortsetzungszeilen von Hausnamen in der
Tabelle. Erste Prüfung: auf den drei Register-GT-Seiten liefert der Parser aus dem
GT-Text und aus der Gemini-Lesung bei 194 von 200 Einträgen dieselben Felder (97 %); die
6 Abweichungen sind Lesefehler (I.J., Speyermann, B/V, Gassenbesezer, St.Andreasplatz),
keine Parserfehler. Die eigentliche Abnahme (≥ 95 % feldgenau gegen handgeprüfte
Einträge) steht noch aus.

## 3. Architektur der Pipeline

Wie Aarau: `01` Seitenbilder → `02` ATR (zwei Leser) → `03` Zeilen/Einträge → `04` Parser
→ `05` Gebäude → `06` Normalisierung → `07` Identität → `08` Turtle → `09` QLever/MCP;
jede Stufe liest und schreibt CSV, jede Zeile trägt ihre Herkunft (Band, Seite, Zeile,
Lauf, Prompt-Digest). CSV-Schema in `docs/schema.md`; Basler Ergänzungen: in
`05_buildings.csv` `house_no_new` (1862, je Strasse), `house_no_old` (stadtweite Nummer
1841/1850/alt 1862), `quarter` (I–VIII), `house_name` (Hausname), `city_part`
(Grosse/Kleine Stadt, Bann); in `04_entries.csv` `building_no` ist in 1841/1850 die alte
stadtweite Nummer und in 1862 die neue Nummer je Strasse — `building_no_system` sagt,
welche (`alt` / `neu`).

Abschnitte in `01_pages.csv`: `vorspann`, `gebaeude` (Nummernbuch/Häuserverzeichnis),
`einwohner` (Register, inkl. Nachtrag und Bänne 1841), `firmen` (Ragionenbuch), `behoerden`,
`strassen`, `hausnamen` (1862), `besitzer` (Häuserbesitzer-Register 1862), `berufe`
(Berufsarten 1862), `inserate`, `leer`, `sonst`.

## 4. Schritte und Abnahme

| Welle | Schritt | Inhalt | Abnahme |
|---|---|---|---|
| 0 | Setup ✅ 06.11.2026 | Repo (`~/Repos/adressbuecher-basel`), Skripte aus Aarau, Seitenbilder byteidentisch (`data/pages/`, nicht im Git), `00_volumes.csv` mit SHA-256, Signatur, Permalink | erfüllt |
| 0 | Seiten ✅ 06.11.2026 | `01_pages.csv` mit Abschnitt, gedruckter Seitenzahl, Satz, Spalten für alle 873 Seiten (Kontaktbögen à 20 Seiten durch vier Hilfsagenten, Grenzseiten auf der Einzelseite bestätigt) | erfüllt; Abschnittsfolge in Abschnitt 1 |
| 1 | ATR Probe ✅ 06.11.2026 | 20 geschichtete Seiten (`data/csv/probe_pages.csv`) auf tei unter `data/nextcloud/adressbuecher-basel/probe/`; Gemini 3.8 Flash (MCP, `reasoning=low`), `qwen3-vl-30b-a3b-instruct` und `qwen3.8-27b` (GPUStack, CLI); 4 GT-Seiten; CER je Leser und Seitentyp | Befund in Abschnitt 2, Entscheid je Seitentyp |
| 1 | ATR voll ✅ 06.11.2026 | 798 Seiten (alles ausser leer/Inserate) mit Gemini 3.8 Flash und qwen3-vl-30b; Läufe `basel-gemini-v1`, `basel-qwen3vl30b-v1` | `02_lines.csv` vollständig (124 526 Zeilen); Befund in Abschnitt 2 |
| 2 | Einträge (Volllauf ✅ 06.11.2026, Abnahme offen) | Parser je Band (1841 Nummer-vor-Strasse, 1850 Kompaktregister, 1862 Gedankenstrich) → `04_entries.csv`; Häuserverzeichnis → `05_buildings.csv` mit alter und neuer Nummer; nach dem Volllauf `make fullrun-parse` | ≥ 95 % der GT-Einträge feldgenau; Rest in `review/` |
| 3 | Normalisierung, Identität | Berufe, Strassen (Basler Strassennamen 1841–1862 → heute), Heimatorte; Personen über die drei Bände; Gebäude über die Nummernkonkordanz 1862 | wie Aarau |
| 4 | Graph, Betrieb | Turtle mit `bestandsgraph.Build`, gemeinsam mit Aarau validiert; QLever | wie Aarau |
| 5 | Informationssystem, Karte | MCP-Server; Leaflet-Karte auf OSM mit Löffel-Plan 1862 als WMS (Vorbild DH Bern); Gebäudepunkte aus `05_buildings_geo.csv` (HGB, Abschnitt 4b) | wie Aarau |

### 4b. Verortung über das Historische Grundbuch Basel (HGB)

Hinweis der Projektleitung (06.11.2026): Zenodo [10.5281/zenodo.22112366](https://doi.org/10.5281/zenodo.22112366)
(Metadaten-Skripte des Projekts «Ökonomien des Raums», Uni Basel; GitHub
[economies-of-space](https://github.com/history-unibas/economies-of-space),
[-metadata](https://github.com/history-unibas/economies-of-space-metadata),
[-database](https://github.com/history-unibas/economies-of-space-database)). Befund:

- Die **HGB-Dossiers** des Staatsarchivs (LOD, `ld.bs.ch`) sind je Liegenschaft angelegt;
  ihr Titel ist die **Adresse nach dem Adressbuch 1862** («Kanonengasse 9»), dazu die
  **alte stadtweite Hausnummer** (`oldHousenumber`, «754 L», mit «(Bann)»-Zusatz), der
  Hausname und der **Eigentümer 1862** (`owner1862`). Das ist dieselbe Konkordanz wie
  unsere 1862er Tabelle, nur von der Liegenschaft her, und für 6 057 Dossiers in 231
  Strassen-Serien.
- Das Datenbank-Repo liefert **4 353 Dossier-Standorte** als Punkt in LV95
  (`dossiergeomshifted_…csv`; Georeferenzierung durch das Grundbuch- und Vermessungsamt
  BS, im Projekt am Löffelplan 1862 geprüft und für Teilhäuser verschoben; Genauigkeit
  nach eigener Aussage «plausibel, nicht gemessen»). Der vollständige Dump (1,6 GB, CC BY
  4.0) liegt auf Zenodo [22025829](https://doi.org/10.5281/zenodo.22025829).
- Übernommen nach `data/ext/hgb/` (Quelle, Lizenz: `README.md` dort).

`scripts/10_geo_hgb.py` bildet `05_buildings.csv` darauf ab: 1862 über Strasse + neue
Nummer (Strassennamen normalisiert: Johann/Johanns, Graben/-Graben), 1841/1850 über die
alte Nummer **innerhalb des Nummernraums** (Grossbasel, Kleinbasel ab 1, Bänne ab 1 —
die Kleinbasler Strassen kommen aus unseren eigenen Zwischentiteln), Dossiers mit
mehreren Nummern oder mehrere Dossiers je Nummer als Schwerpunkt (`medium`), «Theil
von»-Dossiers nachrangig. Ergebnis `05_buildings_geo.csv` (Schema in `docs/schema.md`).
Stand 06.11.2026 auf dem vollständigen Gemini-Lauf (7 986 Gebäude):

| Band | Gebäude | eindeutig (`high`) | Schwerpunkt / Hauptnummer | Dossier ohne Standort | ohne Treffer | verortet |
|---|---:|---:|---:|---:|---:|---:|
| 1841 | 2 151 | 1 321 | 746 | 37 | 47 | **96 %** |
| 1850 | 2 102 | 1 226 | 794 | 30 | 52 | **96 %** |
| 1862 | 3 733 | 2 041 | 596 (236 Mehrfachdossiers, 360 über die alte Nummer) | 601 | 495 | **71 %** |

Prüfung der Konkordanz: bei 2 410 von 2 615 verorteten 1862er Gebäuden stimmt die alte
Nummer unserer Tabelle mit `oldHousenumber` des HGB überein (189 Abweichungen, meist
Bereichsdossiers wie «Aeschengraben 4-16» oder Teilhäuser). Die Lücke bei 1862 ist die
Geometrie des HGB (4 353 von 6 057 Dossiers haben einen Punkt) und die Strassen ausserhalb
der Mauern (Klybeck, Grenzacher-, Elsässer-, Hägenheimer-Strasse, Wege im Bann), die das
HGB kaum erfasst; dort bleibt der Rückfall auf die Strassenmitte (Nominatim) wie im
Aarauer Plan. Strassennamen werden über die Schreibvarianten der HGB-Serien
(«Freie Strasse / Freiestrasse», th/t, y/i, Genitiv-s, «St.») abgeglichen; 10 Strassen
des Bandes 1862 haben keine HGB-Serie. Damit entfällt
für Basel die Strassenmitte-Ebene aus dem Aarauer Plan weitgehend; die Karte kann
direkt auf Liegenschaften zeichnen, mit dem Löffelplan 1862 als WMS-Overlay wie bei
[basler-liegenschaften-interaktiv](https://dhbern.github.io/basler-liegenschaften-interaktiv).

## 5. Repo-Struktur

Wie Aarau: `scripts/01_render_pages.py` (JPG-Ordner statt PDF), `02_atr_batch.py`,
`03_compare_readers.py`, `04_parse.py`, `05_buildings.py`, `10_geo_hgb.py`, `gt_diff.py`; `data/ext/hgb/`
(HGB-Dossiers, -Serien, -Standorte); `prompts/`,
`data/csv`, `data/gt`, `data/atr` (Text ja, Bilder nein), `data/pages` (nicht im Git),
`docs/schema.md`, `Makefile` (`make pages`, `make atr-fetch RUN=…`, `make atr-lines`,
`make probe-fetch probe-compare`).

## 6. Entscheidungen, die noch ausstehen

1. ~~GitHub-Repo anlegen~~ — erledigt 06.11.2026: `https://github.com/thodel/adressbuecher-basel`
   (privat, wie Aarau).
2. **Hausnummern-Konkordanz** 1862 (neu je Strasse ↔ alt stadtweit) als eigene Tabelle
   führen, damit 1841/1850 auf die 1862er Gebäude abgebildet werden; prüfen, ob die alten
   Nummern zwischen 1841 und 1850 stabil sind (Stichprobe in Welle 2).
3. ~~Lage im Raum~~ — gelöst über das HGB (Abschnitt 4b, Hinweis der Projektleitung
   06.11.2026): die Dossier-Standorte des Projekts «Ökonomien des Raums» liefern
   Koordinaten je Liegenschaft; offen ist nur die Datenlizenz der Standortpunkte
   (Shapefile des Grundbuch- und Vermessungsamts, im Repo ohne Lizenzangabe; Dump auf
   Zenodo CC BY 4.0) — vor der Veröffentlichung der Karte beim Projekt nachfragen.
4. **Gleichzeitige Läufe auf GPUStack**: die Aarauer Volläufe (gestartet 06.11.2026,
   ~8 h für qwen3.8) teilen sich die Karten mit den Basler Läufen; Reihenfolge festlegen.
5. **Weitere Bände** (StABS hat die Reihe bis ins 20. Jahrhundert): welche Jahre die
   Reihe sinnvoll verlängern (1844? 1847? 1856? 1870?), nach dem Befund von Welle 1.
