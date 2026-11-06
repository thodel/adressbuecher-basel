# CSV-Schema der Zwischenresultate

Alle Dateien liegen in `data/csv/`, UTF-8, Komma-getrennt, mit Kopfzeile. Jede Zeile
trägt ihre Herkunft; nichts wird überschrieben, was aus einer früheren Stufe stammt. Die
Nummer im Dateinamen ist die Stufe, die die Datei erzeugt.

## 00_volumes.csv — ein Band je Zeile

| Spalte | Inhalt |
|---|---|
| `volume` | Jahr des Bandes (`1884`, `1888`, `1892`, `1896`, `1899`); dient überall als Bandschlüssel |
| `pdf` | Dateiname der Quelle |
| `pages` | Seitenzahl des PDF |
| `sha256` | Prüfsumme des PDF, damit ein Lauf an die Quelle gebunden ist |

Geplante Ergänzung von Hand: `title`, `edition`, `editor`, `publisher`, `place`, `library_shelfmark`
(Kantonsbibliothek Aargau «Cont. 40»), `erara_url`.

## 01_pages.csv — eine Seite je Zeile (Stufe 1, Abschnitte von Hand)

| Spalte | Inhalt |
|---|---|
| `volume`, `page` | Band und PDF-Seite (1-basiert) — der Seitenschlüssel aller folgenden Dateien |
| `image` | Pfad des Seitenbildes relativ zu `data/pages/` |
| `width`, `height` | Pixelmasse des Bildes |
| `source` | `embedded` (byteidentisch aus dem PDF) oder `rendered300:<n>img` (Fallback) |
| `printed_page` | gedruckte Seitenzahl, wie sie auf der Seite steht (römisch möglich); leer, wenn nicht lesbar |
| `section` | `vorspann`, `gebaeude`, `einwohner`, `berufe`, `zeitungen`, `behoerden`, `inserate`, `leer`, `sonst` |
| `typeface` | `fraktur`, `antiqua`, `gemischt` |
| `columns` | Textspalten der Einträge (1 oder 2) |
| `note` | Zwischentitel, Besonderheiten, woran eine Abschnittsgrenze erkannt wurde |

## 02_lines.csv — eine erkannte Zeile je Leser je Zeile (Stufe 2, ATR, Langformat)

Jeder Leser segmentiert anders, darum liegt je Leser eine eigene Zeilenfolge vor; die
Wahl der Lesung und die Zusammenführung zu Einträgen passiert in Stufe 3.

| Spalte | Inhalt |
|---|---|
| `volume`, `page`, `key` | Seitenschlüssel; `key` = `<volume>_p<nnn>` wie im ATR-Lauf |
| `run_id`, `reader`, `engine` | ATR-Lauf (Verzeichnis unter `data/atr/`), Modell-Id, Engine (`kraken`, `vllm`, …) |
| `line` | Zeilennummer des Lesers (kraken: `order`; Seitenleser: Zeilenumbruch im Text) |
| `x0`, `y0`, `x1`, `y1` | Begrenzung in Bildpixeln; leer bei Seitenlesern ohne Geometrie |
| `text` | Zeilentext dieses Lesers |
| `line_confidence`, `page_confidence` | Konfidenz des Lesers, wo vorhanden |
| `truncated` | `1`, wenn der Leser am Token-Deckel abgebrochen hat |
| `quality_verdict` | Urteil von `page_quality` (`ok`, `short`, `empty`, `repetitive`, `deliberation`) |
| `timing_ms` | Dauer des Aufrufs |

Geplant für Stufe 3: `02b_lines_chosen.csv` mit der gewählten Lesung je Zeile
(`chosen_reader`, `method` ∈ `single`, `agree`, `vote`, `review`) und `column`/`indent`.

## 03_entries_raw.csv — ein Eintrag je Zeile (Stufe 3)

| Spalte | Inhalt |
|---|---|
| `entry_id` | `<volume>-<section>-<page>-<n>`; stabil, solange die Zeilen gleich bleiben |
| `volume`, `page`, `section` | Herkunft |
| `line_from`, `line_to` | erste und letzte Zeile des Eintrags in `02_lines.csv` |
| `text` | der zusammengesetzte Eintragstext, Trennstriche aufgelöst |
| `owner_flag` | `1`, wenn der Eintrag mit `*` (Hausbesitzer) beginnt |
| `dash_prefix` | `1`, wenn der Eintrag mit Gedankenstrich beginnt (Familienname wiederholt) |
| `surname_inherited` | der ergänzte Familienname bei `dash_prefix` |
| `heading` | der zuletzt gesehene Zwischentitel (Strasse im Gebäudeverzeichnis, Berufsklasse im Berufsregister) |

## 04_entries.csv — ein geparster Eintrag je Zeile (Stufe 4)

| Spalte | Inhalt |
|---|---|
| `entry_id` | wie oben |
| `surname`, `alliance_name` | Familienname und Allianzname (`Müller-Hürni` → `Müller`, `Hürni`) |
| `forename` | Vorname(n), Abkürzungen aufgelöst in `forename_expanded` |
| `title` | `Dr.`, `Dr. med.`, `Regt.`, … |
| `civil_status` | `Witwe`, `Wwe.`, `Frau`, `Fräulein`, `geb.` … wie im Text |
| `relation` | `Sohn`, `Tochter`, `geb. <Name>`; Bezug auf den vorangehenden Eintrag bei Gedankenstrich |
| `occupation_raw` | Beruf/Stand wie gedruckt (`Part.` = Partikulier, `Taglöhner`, `Fabrikant`) |
| `origin_raw`, `origin_canton` | Heimatort wie gedruckt und der Kantonszusatz in Klammern |
| `street_raw`, `building_no` | Strasse/Quartier und Gebäudenummer (mit Buchstabenzusatz, `92a`) |
| `address_role` | `wohnung`, `werkstaette`, `geschaeft`, `wohnung+geschaeft`; mehrere Adressen → mehrere Zeilen mit `address_seq` |
| `phone_flag` | `1`, wenn das Telefon-Symbol steht (ab 1899) |
| `parse_method` | `rule` oder `llm` |
| `parse_confidence` | `high`, `medium`, `low`, `review` |
| `residual` | Textrest, den der Parser nicht zuordnen konnte |

Zusätzliche Spalten seit dem ersten Parser: `entry_type` (`person` / `firma`), `heading`
(Rubrik des Berufsregisters, z. B. «Hafnereien»; leer im Einwohnerverzeichnis),
`maiden_name` (Geburtsname nach «geb.»). Das Berufsregister wird mit demselben Parser
und `--section berufe` in eigene Dateien (`04_berufe_<satz>.csv`) geschrieben; dort
ist `occupation_raw` meist leer und die Rubrik trägt den Beruf.

## 05_buildings.csv — ein Gebäude je Band je Zeile (Stufe 5, `scripts/05_buildings.py`)

| Spalte | Inhalt |
|---|---|
| `building_id` | `<volume>-B-<building_no>` |
| `volume`, `page`, `line` | Herkunft |
| `building_no`, `building_nos` | erste Nummer (Schlüssel) und die gedruckte Nummernangabe («365. u. 366.») |
| `marker` | `*` Eigentümer wohnt im Haus, `†` Nebengebäude, leer sonst |
| `street_raw` | Strasse/Quartier gemäss letztem Zwischentitel (nur über direkt aufeinanderfolgende Seiten mitgeführt) |
| `owner_text` | Eigentümer wie gedruckt, Ditto («Derselbe», «„») aufgelöst |
| `owner_same_as_prev` | `1`, wenn der Eigentümer per Ditto vom vorangehenden Gebäude übernommen wurde |
| `owner_surname`, `owner_entry` | Familienname und geparste Felder des Eigentümers (JSON) |
| `building_type` | Gebäudeart (Scheune, Remise, Fabrikgebäude, Erbschaft …) |
| `phone_flag`, `parse_confidence`, `note` | wie oben; `note` sammelt unzugeordnete Zeilen |
| geplant: `street_norm`, `lat`, `lon`, `osm_way_id`, `geo_method`, `geo_confidence` | Normalisierung (06) und Geokodierung (10) |

## 05_residents.csv — ein Bewohner je Zeile (Stufe 5)

Die eingerückten Bewohnerzeilen unter einem Gebäude, geparst wie ein Einwohnereintrag
(alle Spalten von `04_entries.csv`), dazu `building_id` und `building_no`. Der
Gedankenstrich erbt hier den Familiennamen des Eigentümers. 1884 hat keine
Bewohnerzeilen (jede Nummer nennt nur den Eigentümer).

## 06_occupations.csv, 06_streets.csv, 06_origins.csv — Normalisierungstabellen (handgepflegt)

| Datei | Schlüssel | Spalten |
|---|---|---|
| `06_occupations.csv` | `occupation_raw` | `occupation_norm`, `class` (Berufsklasse aus dem Register des Bandes), `hisco` (optional), `gender_marked` |
| `06_streets.csv` | `street_raw` | `street_norm`, `quarter`, `street_today`, `wikidata`, `osm_id`, `osm_type`, `lat`, `lon`, `note` |
| `06_origins.csv` | `origin_raw` | `origin_norm`, `canton`, `country`, `hls_id`, `wikidata`, `note` |

## 07_persons.csv, 07_groups.csv, 07_roles.csv — bandübergreifende Identität (Stufe 7)

| Datei | Schlüssel | Spalten |
|---|---|---|
| `07_persons.csv` | `person_id` | `name_canonical`, `entry_ids` (`;`-getrennt, je Band höchstens einer), `first_volume`, `last_volume`, `match_score`, `match_rule`, `review` |
| `07_groups.csv` | `group_id` | `name`, `type` (`behoerde`, `verein`, `firma`, `buergergemeinde`, `anstalt`), `volume_ids`, `wikidata` |
| `07_roles.csv` | `person_id, group_id, volume` | `role` (Amt/Funktion), `source_entry_id` |

## 08_mentions.csv — Erwähnungen (Stufe 8)

| Spalte | Inhalt |
|---|---|
| `entry_id` | der erwähnende Eintrag |
| `target_type`, `target_id` | `person`, `building`, `group`, `place` und der jeweilige Schlüssel |
| `role` | `bewohner`, `eigentuemer`, `amtsinhaber`, `heimatort`, `arbeitsort` |

## 09_links_anb.csv — Verknüpfung mit e-periodica (Stufe 9)

| Spalte | Inhalt |
|---|---|
| `target_type`, `target_id` | Person oder Gebäude |
| `pid`, `chunk_id` | e-periodica-Artikel und Passage |
| `journal` | `anb-001` (Aarauer Neujahrsblätter), `arg-001` (Argovia) |
| `year_article`, `year_mention` | Erscheinungsjahr und in der Passage genanntes Jahr |
| `tier` | `strict` (Band 1910–1919) oder `dated` (Jahr im Fenster 1884–1919 in der Passage) |
| `score`, `evidence`, `url` | Matching-Score, gekürzter Beleg, Link |
| `status` | `auto`, `review`, `accepted`, `rejected` |
