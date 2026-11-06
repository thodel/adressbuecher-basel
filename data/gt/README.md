# Ground Truth

Handkorrigierte Seitentexte, eine Datei je Seite: `<volume>_p<nnn>.txt`
(Schlüssel wie in `data/csv/01_pages.csv` und in den ATR-Läufen).

Konventionen (dieselben wie im ATR-Prompt `prompts/adressbuch_basel_atr.md`, und bis auf
die Tabellenzeilen dieselben wie in Aarau):

- eine Zeile je gedruckter Zeile; Fortsetzungszeilen mit zwei Leerzeichen eingerückt;
  eingerückte Folgeeinträge (Bewohner unter einem Haus, 1850 Personen ohne wiederholten
  Familiennamen) bleiben ebenfalls eingerückte eigene Zeilen
- Kolumnentitel, Seitenzahl und die Spaltenkopfzeile («Nro.») bleiben, wo sie stehen
- zweispaltige Seiten: linke Spalte, dann eine Zeile `[spalte 2]`, dann rechte Spalte
- Tabellenseiten (Häuserverzeichnis 1862, Ragionenbuch): eine Zeile je Tabellenzeile,
  Zellen mit ` | ` getrennt, leere Zellen leer; Bewohnerzeilen in der letzten Spalte als
  eingerückte eigene Zeilen ohne Trenner; Kopfzeile der Tabelle einmal mit Trennern
- `*` (Eigentümer), `—` (wiederholter Familienname), Bindestrich zwischen Allianznamen
  (⸗ als `-`), alle Abkürzungen wie gedruckt; nichts aufgelöst, nichts modernisiert
- langes s als `s`, `ß` bleibt; J vor Vokal, I vor Konsonant
- `[handschriftlich: …]` für Lesernotizen, `[stempel: …]` für Stempel; beides zählt
  beim Vergleich nicht (wird vor der CER-Berechnung entfernt); gestrichene Einträge
  bleiben als Text, der Strich als `[handschriftlich: gestrichen]`

Entstehung: Ausgangspunkt ist die beste maschinelle Lesung der Seite; jede Stelle, an
der zwei Leser abweichen, wird am Bild (`data/pages/`) entschieden, danach die ganze
Seite einmal gegen das Bild gelesen. In `provenance.csv` steht je Seite, wer korrigiert
hat, von welcher Lesung ausgegangen wurde und wann.
