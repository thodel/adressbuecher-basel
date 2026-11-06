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
| 1841 | 202 | Fraktur | STA H 43 17 · [dls 1225921](https://dls.staatsarchiv.bs.ch/records/1225921) | _wird nach Welle 0 eingetragen_ |
| 1850 | 165 | Fraktur | STA H 43 20 · [dls 1225925](https://dls.staatsarchiv.bs.ch/records/1225925) | _wird nach Welle 0 eingetragen_ |
| 1862 | 506 | Fraktur | STA H 43 22 · [dls 1225927](https://dls.staatsarchiv.bs.ch/records/1225927) | _wird nach Welle 0 eingetragen_ |

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

### Befund Welle 1 — ATR-Probe

_wird nach der Probe eingetragen_

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
`einwohner`, `firmen` (Ragionenbuch), `behoerden`, `strassen`, `inserate`, `leer`, `sonst`.

## 4. Schritte und Abnahme

| Welle | Schritt | Inhalt | Abnahme |
|---|---|---|---|
| 0 | Setup ✅ 06.11.2026 | Repo (`~/Repos/adressbuecher-basel`), Skripte aus Aarau, Seitenbilder byteidentisch (`data/pages/`, nicht im Git), `00_volumes.csv` mit SHA-256, Signatur, Permalink | erfüllt |
| 0 | Seiten | `01_pages.csv` mit Abschnitt, gedruckter Seitenzahl, Satz, Spalten für alle 873 Seiten (Kontaktbögen à 20 Seiten durch Hilfsagenten, Grenzseiten auf der Einzelseite bestätigt) | alle Seiten klassifiziert, Abschnittsfolge im Plan |
| 1 | ATR Probe | 20 geschichtete Seiten (`data/csv/probe_pages.csv`) auf tei unter `data/nextcloud/adressbuecher-basel/probe/`; Gemini 3.8 Flash (MCP, `reasoning=low`), `qwen3-vl-30b-a3b-instruct` und `qwen3.8-27b` (GPUStack, CLI); 4 GT-Seiten; CER je Leser und Seitentyp | Befund in Abschnitt 2, Entscheid je Seitentyp |
| 1 | ATR voll | alle Seiten ausser leer/Inserate mit den zwei gewählten Lesern; Läufe `basel-<leser>-v1` | `02_lines.csv` vollständig |
| 2 | Einträge | Parser je Band (1841 Nummer-vor-Strasse, 1850 Kompaktregister, 1862 Gedankenstrich) → `04_entries.csv`; Häuserverzeichnis → `05_buildings.csv` mit alter und neuer Nummer | ≥ 95 % der GT-Einträge feldgenau; Rest in `review/` |
| 3 | Normalisierung, Identität | Berufe, Strassen (Basler Strassennamen 1841–1862 → heute), Heimatorte; Personen über die drei Bände; Gebäude über die Nummernkonkordanz 1862 | wie Aarau |
| 4 | Graph, Betrieb | Turtle mit `bestandsgraph.Build`, gemeinsam mit Aarau validiert; QLever | wie Aarau |
| 5 | Informationssystem, Karte | MCP-Server; Leaflet-Karte auf OSM mit Löffel-Plan 1862 als WMS (Vorbild DH Bern) | wie Aarau |

## 5. Repo-Struktur

Wie Aarau: `scripts/01_render_pages.py` (JPG-Ordner statt PDF), `02_atr_batch.py`,
`03_compare_readers.py`, `04_parse.py`, `05_buildings.py`, `gt_diff.py`; `prompts/`,
`data/csv`, `data/gt`, `data/atr` (Text ja, Bilder nein), `data/pages` (nicht im Git),
`docs/schema.md`, `Makefile` (`make pages`, `make atr-fetch RUN=…`, `make atr-lines`,
`make probe-fetch probe-compare`).

## 6. Entscheidungen, die noch ausstehen

1. **GitHub-Repo** `thodel/adressbuecher-basel` anlegen und pushen — erst auf Zusage der
   Projektleitung.
2. **Hausnummern-Konkordanz** 1862 (neu je Strasse ↔ alt stadtweit) als eigene Tabelle
   führen, damit 1841/1850 auf die 1862er Gebäude abgebildet werden; prüfen, ob die alten
   Nummern zwischen 1841 und 1850 stabil sind (Stichprobe in Welle 2).
3. **Lage im Raum**: Löffelscher Stadtplan 1862 (WMS des Kantons BS, von DH Bern genutzt)
   trägt vermutlich die neuen Hausnummern; mit dem Historischen Grundbuch Basel (HGB,
   `eos`-MCP, bis ca. 1700) besteht über Hausnamen («zum Rosengarten», «zur Klause») eine
   zweite Brücke.
4. **Gleichzeitige Läufe auf GPUStack**: die Aarauer Volläufe (gestartet 06.11.2026,
   ~8 h für qwen3.8) teilen sich die Karten mit den Basler Läufen; Reihenfolge festlegen.
5. **Weitere Bände** (StABS hat die Reihe bis ins 20. Jahrhundert): welche Jahre die
   Reihe sinnvoll verlängern (1844? 1847? 1856? 1870?), nach dem Befund von Welle 1.
