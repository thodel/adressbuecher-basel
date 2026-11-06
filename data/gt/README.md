# Ground Truth

Handkorrigierte Seitentexte, eine Datei je Seite: `<volume>_p<nnn>.txt`
(Schlüssel wie in `data/csv/01_pages.csv` und in den ATR-Läufen).

Konventionen (dieselben wie im ATR-Prompt `prompts/adressbuch_atr.md`):

- eine Zeile je gedruckter Zeile; Fortsetzungszeilen mit zwei Leerzeichen eingerückt
- Kolumnentitel und Seitenzahl bleiben, wo sie stehen
- zweispaltige Seiten: linke Spalte, dann eine Zeile `[spalte 2]`, dann rechte Spalte
- `*`, `—` (wiederholter Familienname), Bindestrich zwischen Allianznamen, alle
  Abkürzungen wie gedruckt; nichts aufgelöst, nichts modernisiert
- langes s als `s`, `ß` bleibt; Telefonsymbol als `[tel]`
- `[handschriftlich: …]` für Lesernotizen, `[stempel: …]` für Stempel; beides zählt
  beim Vergleich nicht (wird vor der CER-Berechnung entfernt)

Entstehung: Ausgangspunkt ist die beste maschinelle Lesung der Seite; jede Stelle, an
der zwei Leser abweichen, wird am Bild (`data/pages/`) entschieden, danach die ganze
Seite einmal gegen das Bild gelesen. In `provenance.csv` steht je Seite, wer korrigiert
hat, von welcher Lesung ausgegangen wurde und wann.
