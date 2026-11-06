# ATR batch — basel-probe-gpustack-v1

- pages: **20**
- started: 2026-11-06T13:28:45+00:00
- wall time: 43.9 min

| model | read | skipped | failed | empty | looped | arguing | cut off | chars/page | s/page | wall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `qwen3-vl-30b-a3b-instruct` | 20 | 0 | 0 | 0 | 1 | 0 | 1 | 2695 | 9.7 | 3.2 min |
| `qwen3.8-27b` | 20 | 0 | 0 | 1 | 0 | 0 | 2 | 2140 | 122.0 | 40.7 min |

**These columns are not quality.** There is no ground truth in this run, and characters per page measures how much a model wrote, not how much of it is right — a model that hallucinates fluently leads this table. Comparing the readings is the point; the numbers only say what each run cost and whether it completed. Measuring accuracy needs transcribed lines and `eval/linebench.py`.

## Readings that were cut off

- `qwen3-vl-30b-a3b-instruct`: 1 of 20 page(s)
  - 1841_p027
- `qwen3.8-27b`: 2 of 20 page(s)
  - 1841_p065
  - 1862_p025

These pages hit the model's token ceiling and stop mid-text. The request succeeded and the text is real — there is just less of it than the page has, and it reads like a model that gave up rather than one that was interrupted. Raise the ceiling — `ATR_VLLM_MAX_NEW_TOKENS` on the gateway, `GEMINI_MAX_TOKENS` for an external reader — delete the affected results and re-run: the batch re-reads only what is missing. A reasoning model spends the same ceiling on thinking before it writes a character, so lowering the thinking level buys page as surely as raising the ceiling does (#611) — check the thinking level before buying tokens.

## Pages that came back empty

- `qwen3.8-27b`: 1 of 20 page(s) (5%)
  - 1862_p025

These are successes by every signal this runner has: a 200, no error, both files on disk, and `is_complete` will skip them on every later run. **Look at the images before reading anything into the number.** A blank verso or an envelope flap is genuinely empty, and knowing how many the corpus holds is worth having before extrapolating a cost per page. A *written* page that comes back empty is a defect no other column here would ever show — the segmenter found no lines on it (gateway), or the model answered the page with nothing at all (external reader). The second is a reading the prompt refused, not a page the model could not fetch: compare the same pages under another prompt before concluding anything about the corpus.

## Pages the model padded

- `qwen3-vl-30b-a3b-instruct`: 1 of 20 page(s) (5%)
  - 1841_p027

A run of one character twenty long or half the lines repeating is not a reading of a page. **These carry text, so every average over them is wrong** — characters per page most of all. They are described, not removed: whether the page itself is a table, a ruled form or a scan the model could not hold on to is settled by looking at it.

## Readings

The texts themselves, so the comparison the table refuses to make can be made by eye. **Read to the end of each one**: a page that hit the token ceiling comes back as an ordinary success and stops mid-sentence, and it is marked here where that happened.

### `qwen3-vl-30b-a3b-instruct`

#### 1841_p027 (9138 characters — stopped at the token ceiling)

~~~text
Nro.
511 Fürstenberger-Debary, Joh. Georg, Wollenhandlung.
512 Fürstenberger-Burckhardt, Joh.
Hinter dem Spahlenthurm.
513 u. 514 Rebfaamen, Joh., Commis.
Schärer, Catharina und Margaretha, Jungfern.
515 * Wagner, Jungfer, Anna Margaretha, gehörend.
516 His-Bischer, Friedr.
Burckhardt, geb. Iselin, Wittwe.
Adelberg.
517 Falkner, Jungfer, Margaretha.
518 Link, geb. Meiry, Wittwe.
Fäsch, Susanna, Klein-Kinderschule.
519 * Magazin des Hrn. J. G. Fürstenberger-Debary.
519 a , , Isaak Dreyfus.
520 La Roche-Bischer, J. J., Banquier, Commissions- u. Spedit.-Hdlg.
La Roche-Stähelin, Benedikt, dito
521 * Gesler, Daniel, Hutmacher.
Klenk, Viktor. (Agentsgeschäfte.)
522 Gyssler-Handmann, Ludwig, Seidenfabrikant.
Aveng, Carl, Commis.
523 Erlacher, geb. Heinzgen, Wittwe. (Flachmalerei.)
524 Ederer, Phil. Heinrich, Comptorist.
525 Burckhardt-Hef, Wittwe.
Imbergäfklein.
526 * Gesler, Daniel, Hutmacher.
Georg, Achilles, Schuhmacher.
527 Scherlin, A. M., von Eberseck, Schneiderin.
528 Krull, Frau, Margaretha, geb. Strub.
529 Spörlin, J. Ulrich sel., Wittwe, geb. Wolleb.
530 Walliser, J. Fr., Fabrikarbeiter.
Müller, Jakob, am Kaufhaus.
531 u. 532 * Mende, Fr. Gottl., Kübler.
Bell, Friedrich, von Klein-Hüningen.
533 Hinterhaus von Nro. 602, Friedr. Gottl. Mende geh.
534 dito
535 dito dem Hrn. Hagenbach, Apotheker, geh.
536 dito von Nro. 594.
537 dito , 593.
538 dito , 591.
539 Thommen, Jakob, Fabrikarbeiter.
540 Hofer, Sam. Rudolf, Spezereihändler.
541 Waffermann, Jungfer, Dorothea.
542 Hegel, J. J., Ladendiener, von Klein-Hüningen.
543 Mende, Friedr. Gottl., Kübler.
544 u. 545 Obrecht, Joh., Kammacher.
[spalte 2]
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
5
~~~

#### 1841_p046 (1427 characters)

~~~text
39
Nro.
1060 Gengenbach, Frau Elis., geb. Mieg.
1061 Benz, Friedrich, Wittwe, Uhrenmacher.
1062 Schneider, Heinrich, Sattler.
1063 Schük, Jakob, Handels-Commis.
Spitalgässlein.
1064 Ryhner, geb. Battier, Wittwe.
Beim Aefchen=Schwibogen.
1065 * Berri, Melchior, Architekt.
1066 u. 1067 Stähelin, Christoph, Handelsmann.
1068 Bogel, Franz Martin, Schneider.
Tiefe.
1069 Schaffner, J. J., Wittwe, Weinschenk.
  Wiedemann, Barthol., Handelsmann.
1070 Schloffer, Caspar, Weißbäck.
1071 Oser, J. J., Schuhmacher.
1072 Meyer, Joh., Perückenmacher.
1073 Christ, Ludwig, Schuhmacher.
1074 Frey, Daniel, alt Landjäger.
1075 Wäffler, Jakob, Feilenhauer.
  Rumpf, Eman., Bürstenbinder.
Am Bäumlein.
1076 Wettstein, Jakob Heinrich, Apotheker sel. Wittwe.
1077 von Speyr, Emil, Wundarzt.
1078 u. 1079 Gysin=Holzach, J. J., Mehlhändler.
1080 * Loz=Jäslin, J. U., Senfal.
  Christ, J. J., Notar und Statthalter.
1081 Retterer, Jos., Weinschenk.
1082 Sulzmann, Jsaak Jak., Fabrikarbeiter.
1083 Benz, Jakob Ludwig, Sohn, Uhrenmacher.
1084 Spital. — Weitnauer, Achilles, Spitalmeister.
1085 Merian=Kespinger, Balthas., Handelsmann.
1086 Wolleb, Rud., Goldschmid.
Streitgasse.
1087 * Müller, Conrad, Schuhmacher, geh.
  Kling, Elias, Glaser.
1088 Giesen, Caspar sel., Wittwe.
  Bürgin, Carl, Buchbinder.
1089 Meyer, Joh. Christoph, Zuckerbäcker.
1090 Schmid, Joh. Heinrich, Kübler.
1091 Stähelin, P. fel., Wittwe.
  Comptoir von Gebrüder Stähelin.
~~~

#### 1841_p065 (1403 characters)

~~~text
58
Nro.
Markt.
1642 Imhof-Falkner, Hieronymus, Sohn.
Imhof-Wenk, Hieronymus, Vater.
1643 Miville, Achilles, Hutmacher.
Huber, Rudolf.
Geymüller, Andreas, Polizei-Commissär.
1644 Brüderlin, Niklaus, Tuchhandlung.
Kespinger, Wittwe, geb. Bürckhardt.
1645 * von Speyr, Joh. Conrad fel., Wittwe, geh.
Brändlin, Joh. Jakob, v. Fischenthal, Schuhmacher.
1646 Ebenderfelben Wohnhaus.
1647 Huggenberger, Joh. Heinrich, Schneider.
1648 Mik, Ludwig, Knopfmacher.
Mik, Wittwe, geb. Ziegler.
1649 Basler, Johannes, Handelsmann.
Basler, Wittwe, geb. M. Elis. v. Mechel.
1650 * Zunft zu Safran.
Heusler-Braun, Lucas, Traiteur.
Nüdengäpslein.
1651 Frey, Mathias, Weinschenk.
Kindermarkt.
1652 Sirt, Lucas fel., Wittwe, geb. Weitnauer, Wirthschaft.
1653 * Ebenderfelben geh.
Keller-Zeller, Friedrich, Kaufhausangestellter.
1654 * Dem Kanton geh.
Schaub, Georg, Fabrikarbeiter.
1655 }
1656 } Kummer, Joh. Conrad, Rathsbote und Weinschenk.
1657 Krayer, Emanuel, Unterbestäter.
1658 Ewig, Joh. Georg, Gastwirth zum Schnabel.
1659 * Zunft zu Kürschner, unbewohnt.
1660 Brandmüller-Eckenstein, Heinrich, Spezereihandlung.
Wahr-Bené, Carl, Handelsmann.
Steiger, Wittwe, geb. Marg. Eckenstein.
1661 }
1662 } Baur, Johannes, Gerber.
Schneider, Emanuel, Gerichtsamtmann.
Widmer-Tis, Joh. Christ., Handels-Commis.
1663 Bohny, Niklaus, Handelsmann.
1664 Studler, Samuel, von Seengen, Hutmacher.
1665 Dreiß, Christian, Handelsmann.
~~~

#### 1841_p110 (2421 characters)

~~~text
27
Lichtenhahn, Carl, alt Stadtrath. 253 h St. Petersplaz.
Lichtenhahn, J. Rud., Schreiner. 910 St. Elisabethen.
Lichtenhahn, C. Chr., Rathschreiber sel., Wittwe. 851 Hintere
Steinen-Borstadt.
Lichtenhahn, Carl, Staatschreiber. 851 Hintere Steinen-Borstadt.
Liebreich, Joh. Conrad, Schneider. 1750 Schneidergasse.
Lienin, Marx, Musiklehrer. 1274 St. Alban-Thorgasse.
Lindenmeyer, Samuel, Schreiner. 269 a Neue Borstadt.
Lindenmeyer, J. J., Weißbeck. 315 Spahlen-Borstadt.
Lindenmeyer, J. G., Weinhändler. 227 Schwarze Pfahlgasse.
Lindenmeyer, Carl. 706 Hinter dem Stöcklein.
Lindenmeyer, J. J., Weinschenk. 707 u. 708 Hinter d. Stöcklein.
Lindenmeyer, Heinrich, Pergamenter. 727 Barfüsserplaz.
Lindenmeyer, B., Wachtmeister, Zollerwohnung. 858 Thorsteinen.
Linder, Emanuel, Professor. 1305 St. Alban-Thal.
Linder, Gottlieb, Mechanikus. 1698 Schnabelgässlein.
Linder, J. J., Hasner. 972 Sternengässlein.
Linder, Emanuel, Bater. 830 Blömlein.
Linder, Emanuel, Sohn. 830 Blömlein.
Linder, Eduard, Zimmermeister. 972 Sternengässlein.
Linder, Joh. Ludwig, Messerschmied. 1559 Schneidergasse.
Linder, Joh. Jakob, Bandfabrikant. 1549 Eisengasse.
Linder, Jakob Ludwig, Bandfabrikant. 149 Schwanengasse.
Linder, Johannes, Obersthelfer. 1374 Hinter dem Münster.
Linder, Jungfer, S. C. 250 St. Petersplaz.
Linder, Joh. Heinrich, Wollenspinnerei. 1275 St. Alban-Thorgasse.
Lindner-Forkart, Ed., Buchbinder. 589 Schneidergasse.
Link, Lucas, Flachmaler. 235 St. Petersgasse.
Link, geb. Meiry, Wittwe. 518 Adelberg.
Lippe, Joh. Jakob, Müller. 621 Hinter der Künlinsmühle.
Locher, Jungfrau, Kleinkinderschule. 593 Schneidergasse.
Locher, Elisabetha, geb. Keller. 494 Oberer Spahlenberg.
Lok, Christian, Schneider. 247 a Kaltkellergässlein.
Lok, Rudolf, Sattler. 18 St. Johann-Borstadt.
Lok, J. J., Küfer. 1378 Am Bäumlein.
Lok, Johannes, Meßger und Ruttler. 1684 Ruttelgässlein.
Lok, Leonhard, Sigrist der St. Peterskirche. 238 Kirchgässlein.
Lok=Spörlin, Hieronymus, Pfundzoller. 712 Barfüsserplaz.
Lok=Jäslin, Ulrich, Waaren-Senfal. 598 Unt. Spahlenberg.
Lok=Wick, Samuel, Kaufmann. 59 St. Johann-Borstadt.
Löw, Leonhard, Schuhmacher, von Benken. 506 Adelberg.
Löw, Joh. Georg, alt Landjäger, von Benken. 1748 Sattelgasse.
Löw, Abraham, Abwart des Casino. 731 bis 733 Barfüsserplaz.
Löw, Johannes, Kohliberger. 752 Kohliberg.
Löw, Johannes, Schneider. 843 Hintere Steinen-Borstadt.
Löw=Gesler, Joh., Fabrikfeger. 1008 Uefchen-Borstadt.
~~~

#### 1841_p137 (2058 characters)

~~~text
54
Faufel, Gottl., Straßenpflasterer u. Weinschenk. 3 An der Rheinbrücke.
Feil, Susanna und Lisette, Schneiderinnen. 150 Rebgasse.
Finninger, Heinrich, Vater und Sohn, Mekger. 278 Webergasse.
Fischer, Andr. sel., Wittwe, Lohnwäscherin. 325 Badergässlein.
Fluri, Nikolaus, kathol. Vikar. 106 Am Lindenberg.
Förster, Ernst, Zimmermann. 136 Kirchgässlein.
Frey, Franz, Fabrikarbeiter. 91 Rufgässlein.
Frey, geb. Bär, Wittwe. 107 Am Lindenberg.
Frey, Phil. Carl, Lehrer. 104 Am Lindenberg.
Frey, Nikolaus, von Armenstorf, Lehrer. 132 Kirchgässlein.
Freuler, geb. Beyfelder, Barbara, Matrakenmacherin. 68 Rheingasse.
Frik, geb. Marg. Frey, Wittwe, Kostgeberin. 162 Rebgasse.
Früh, Caspar, Schuhmacher. 117 Obere Reb-gasse.
Fuchs, Jakob, Lohnwäscher. 270 Beim Bläsithor.
Furler, Joh., Stuhlschreiner. 309 Im Klingenthal.
Fussinger, Ulrich, Müller. 302 Im Klingenthal.
G.
Gasquet, Fr. Wilh., Zimmermann. 119 Obere Reb-gasse.
Gaf, Joh., Weißbeck. 150 Reb-gasse.
Gaf, Andr., Schuhmacher, von Lieftal. 232 Greifengasse.
Gengenbach-Frey, Amad., Kaufmann. 111 Rheinweg.
Gernler, Carl, Kornmesser. 148 Beim Kiehen-Thor.
Gefler, Christina, geb. Burckhardt, Wittwe. 140 Beim Kiehen-Thor.
Gefler, Joh. Rud., Gypser. 167 Reb-gasse.
Gefler, Leonhard, Müller. 265 Im Rumpel.
Gefler, Rudolf, Müller. 267 Im Rumpel.
Gefler, Andreas, Rotherger. 8 An der Rheinbrücke.
Glafer, Jakob, Zimmermann. 101 Am Lindenberg.
Glafer, Frau Barbara, geschr. Klingensuf, Trödlerin. 382 Krempergasse.
Glafer, Friedrich, Fischer. 72 Rheingasse.
Glaz, Joh. Caspar, Spengler. 393 Krempergasse.
Glunz, Geschwister, Schneider u. Matrakenmacherinnen. 173 Reb-gasse.
Gök, Nikol. Wilh., Devisenmacher. 425 Udengasse.
Gosweiler, J. U., Fabrikausseher. 336 Untere Webergasse.
Groben, Jakob, Glafer und Lohnwäscher. 283 Webergasse.
Grüblin, Joh., Wirthschaft. 291 Webergasse.
Grüblin, J. J., Posamentier, von Höllstein. 50 Rheingasse.
Grunauer, Leonhard sel., Wittwe, geb. Weiß. 295 Webergasse.
Grunauer, Sebalt., Spedition und Commission. 44 Rheingasse.
Grundeler, J. Christian, Schlosser. 94 Am Lindenberg.
~~~

#### 1841_p172 (1736 characters)

~~~text
- 19 -
* Bölmn, geb. Ränner, Kath., Wittwe. 1452 Schlüsselb.
BonBrunn-BonSpeyr, J. J., Sohn, Pfarrer. 1499
St. Martin.
Bon der Mühll, Christoph, Vart. 192 Herbergberg.
Bon der Mühll, Friedrich, Kaufmann. 1230 St. Alban-Vorst.
Bon der Mühll, Joh. und Aug. 1553 Bei der Brodlaube.
Bon der Mühll und Söhne, Seidenwaarenhandl. 1598 Eiseng.
Bon Speyr, Joh. Conr., Kaufmann. 314 Spahlen-Vst.
Bon Speyr und Comp., Bank, Commission und Spedition.
1188 Freienstraße.
Bon Speyr, Karl, J. U. Dr., Not. und Kriminalgericht-
schreiberei=Substitut. 1422 Freienstraße.
W.
Wagner, Andreas, Commis. 27 St. Joh. Vorstadt.
Wahr, Philipp, Sohn, Kaufmann. 1446 Freienstraße.
Wahr, Hieronymus, Sohn, Kaufmann. 1446 Freienstr.
Waidmann, Mar. Magd. u. Elis., Igsfr. 39 St. Joh. Vorst.
Waldner, Heinrich, Spannermeister. 635 Gerbergäklein.
Wallich, Jakob, von Lahr, Kutscher. 855 Thor-Steinen.
Weber = Karger, Joh. Georg, Ehegerichts=Amtmann. 593
Schneidergasse.
Wegmann, Jakob, von Jällanden, Kaufhausarbeiter.
1734 Beim Kornmarktbrunnen.
Weisenburger, Ulr., sel. Wittwe, geb. Schwarz, Bäckerei.
943 Ueschen=Vorstadt.
Weiß, Innocenz. 145 Blumengasse.
Weiß, Heinrich, Schneider. 1682 Ruttelgäklein.
Weiß, Wittwe, geb. Bal. Freyburger, und Töchter, Schnei-
derinnen. 840 Hintere Steinen=Vorstadt.
* Wenk, Karl. 239 St. Peters=Kirchgäklein.
Werenfels, J. J., Schreiber. 1167 Gerbergasse.
Wertenberg, Andreas, Feger. 1749 Sattelgasse.
Wertenberg-Langmesser, Abr., Sohn. 1713 Unt. Spahlenberg.
Wettstein, Wittwe, geb. Ifelin. 938 Ueschen=Vorstadt.
Wezel, Jakob, Sohn, Commis. 1317 St. Alban-Vorst.
Wiederkehr, Heinrich, Zettlermeister. 904 St. Elisabethen.
* Wielandt, Anna Maria, Igsfr. 941 Ueschen=Vorstadt.
Winkler, Heinrich, Fabrikarbeiter. 1284 St. Alban-Thal.
~~~

#### 1850_p046 (1456 characters)

~~~text
Steinen=Quartier. 33
751 Lichtenhan=Hagenbach, Joh. Rud., Commissions- u.
  Speditions-handlung.
A 751 Mieg, F. F., Med. et Chir. Dr. und Professor.
Kohlberggässlein.
752 Martin, Heinrich, Flachmaler.
753 Meyer, Friedrich, Thierarzt.
754 Plattner=Hoch, F., Zimmermeister.
  Spreyermann, Elias, Commis.
A 754 Häfelfinger, Joh. Rud., Bater, Commis.
  Häfelfinger, Joh. Rud., Sohn, Commis.
BC 754 Klipfel, Martin, Weinhandlung.
 D 754 Schaub, Johannes, Kaufhausarbeiter.
 E 754 (Stallung.) Plattner, Zimmermeister, geh.
 F 754 Meyer, Eml. Walter, Kaufmann.
GH 754 (Fabrik u. Wohnh.) Burgtorf-Bischoff, Andr., geh.
  Imhof=Haas, Heinrich, Fabrikaufseher.
  Fichter, Abraham, Stuhlschreiner.
Ranonen-gasse.
I 754 Hindenlang, Simon, Commis.
  Kislig, Heinrich, eidg. Beamter.
K 754 Meyer, Wittwe Salome, geb. Gykler.
  Gaf, F. F., Mezger.
  Höfl, G. F., Musiklehrer.
L 754 Hauschild, Ernst, Gesanglehrer.
  Beck, Chr., Lehrer.
  Maglin=Sendranier, Rud., Commis.
M 754 Schaub, Georg, Schreiner.
  Burckhardt, K., Hauptmann bei der Standestruppe.
  Blackwell, Jgfr. Jane, Lehrerin.
  Urech, Jgfr. Elif., Kunstmalerin.
N 754 Kespinger=Stockmeyer, Leonh., Commis.
O 754 Reiter=Bildstein, E., Musikdirektor.
  Bernard, Wittwe, Partikularin.
  Hagenbach, Wittwe, geb. Geigy, Rentière.
Alter Kohliberg.
755 Schnell, F. F., Dr. J., Civilgerichtspräsident.
  Rigggenbach, Wittwe, geb. Huber, Rentière.
  Rigggenbach, Albert, Kaufmann.
756 (Walke) Oser, Adam, Färber, geh.
~~~

#### 1850_p077 (1457 characters)

~~~text
64
St. Alban=Quartier.
1435-37 Paravicini=BonderMühl, Eml., Eisenhandlung.
Paravicini=Battier, Eml., Rentier.
1438 Tschopp=Holzach, Heinrich, Spengler.
Hug, Dan., Lifeur.
Schaub, D., Feger.
Schmucki, Lisette, Modiste.
1439 Holzach-Krauer, Frau Caroline, Glaser u. Glas-
handlung.
Krauer, Wittwe Maria, geb. Köchlin, Rentière.
1440 Meyer=Vischoff, Joh. Christ., Handelsmann.
Vischoff-Wieland, Wittwe, Balerie, Rentière.
1441 Singeisen, Jgfr. Barbara, Rentière.
1442 Ramsperger-Hug, Eml., Niederlage aller bekannten
ächten Mineralwasser, Alpen-Butter u. Spezerei-
waaren.
1442 Marfort, Wittwe, Sattler.
Weber-Marfort, Rud., Meßger.
1444 (Gasthof z. wilden Mann.)
Pfander=Carle, F. F., Major, Gastgeber.
Lüffi, F. F., Tabacchandlung.
Gessler, Jungfr., Modistes u. Schirmhandlung.
1445 (Zunft z. Himmel.)
Erzberger-Krayer, Wittwe Susanna, Zuckerbeck.
1446 Wahr, Gebrüder, Phil. u. Karl, Tuchhandlung.
1447 Albäck, F. H., Quincailleriehandlung.
1448 Kespinger=Bernoulli, Eml., Rentier.
Schlüsselberg.
1449 Spitteler, Christ. Friedr., Buchhändler.
1450 Freimaurer-Loge.
Schimpf, Geb., Abwart.
1451 Hagenbach=Paravicini, Peter, Ehegerichtspräsident.
1452 Burgdorf=Fetscherin, Friedr., Wechsel-Senfal.
1453 Burkhardt, August, Med. et Chir. Dr.
Lehmann-Berger, Julius, Privat-Töchterinstitut.
1454 Obrigkeitlich.
1455 Miville-Krug, H., Alterthümerkabinet.
1456 Wieland-Schweighauser, M. M., Wittwe, Rentière.
Münsterplatz.
1457 Riggenbach=Salger, Christ., Architekt.
~~~

#### 1850_p120 (2020 characters)

~~~text
Halter, N., Bettfedhdlg. 1526
Wittwe, Elis. 1597
Handmann, F. F. 172
Ludwig 1311A
Hanhart, F. K. 669
Hantho, Karl, Partik. *79
Häring, Aug., Schreiner 771
Joh., Condukteur 1399
Hartmann, F., Beck 863
Saml., Ferger *108
Hasler, Sebalt., Ferger 74
=vonMechel, Gottl. 118
Nikl., Beck 86
Haug, Joh., Schuhm. 726
Haupt, E., Gassenbefecker *403
Hausamman, Peter 363
Hauschild, Ernst 754L
Haufer-Euler, Karl 283
=Gürtler, David 955
=Oser, Rudolf 974
Joh., Commis 1164
=Fäsch, Frz. Kaspr. 1530
u. Steigmeyer 1542
Hecht, Jak., Zimmerm. *125
Heckel, F. F., Ladendiener 542
Heckendorf, Fr., Färber *51
Frz., Färber *408
Jgfr. Lisette 119A
Hediger, Joh. Rud. *212
Hegar, Fr., Klavierhdlg. 1B
C. Aug., Lithograph. 126
Hegnauer, F., Posam. 1504
Heidegger, Fh., Agent 127
Heim, Karl 2
Heimers, Sch. Wilh. 1336
Heimlicher, F. F., Dr. J. 1083B
=Brenner, Wittwe 1083B
Heinzgen, Jgfr., Ber. 306
Heik, A. Chr., Notar 1065
Joh. Jak., Drechsler 1565
Bernhard, Drechsler 1625
Jgfr., Ros., Modiste 1170
Heller=Spreyermann, H. 1106
Helfstern, Ant., Müller 1308
P., Maurer *241
Josef, Müller *300
Hemann, David 414
Henning, Franz W. 1112
Henz, Ogg., Huffschiud 329
Jakob, Beck 329
Euch., Wagner 351
=Bernet, Fh., Beck 351
=Fischer, Joh., Beck 354
=Schöll, Nikl., Beck 774
=Ludw., Sohn, Beck 774
F. L., Commis 1096
F. F., Thorschreiber 1276
=Dömmelin, N., Hafner *12
Eduard, Ferger *123
Herbel, Eb., Zimmerm. 965
Hergott, F. L., Lehrer 176
Hermann, Ad., Schloffer 1232
Herrmann, Sch., Ferger 454
Herr, Fidel, Gerber *353
Herrsperger, Jgfr., B. 253A
Jgfr., Elisabetha 253A
Herzog, Eml., Siegriff 272A
=Reber, Emanuel 456
B., Kutscher 476
Joh., Notar 521
Achilles, Kaufmann 973
=Wybert, Wittwe 973
Jgfr., Esther 408
Hesse, F. A., Schneider 1486
Hek, Hs., Historienmaler 27
Joh., Spitalpfarrer 557
Joh., Magazinknecht 1338
F. F., Commis 1528
=Mik, H. N., Lehrer 1648
Hekel, G. Fr., Mechan. 1679
Heukler, Friedrich 94
=Bischoff, Abr., Rektor 571
Abel, Handelsmann 1059
=Ryhiner, A., J. U. D. 1203A
=Wölflin, Christ. 1214-15
=Thurnesfen, Dan. 1274A
107
~~~

#### 1850_p132 (2088 characters)

~~~text
Riggenbach, Alb, Kaufm. 755
=Schmid, Sped.=Hdlg. 830
Joh. 869, Comptoir 1202
=Stehlin, Fch., Bang. 983
=Stulger, Chr., Acht. 1457
Aug., Lehrer 1607
Franz, Kaufmann 1607
F. F., Ladengehilfe *90
=Huber, Wittwe 755
Rimmenesperger, Frau C. 1164
Rigiani, Chocoladefabr. 1427
Ritter, F. F., Gastgeber 1145
=Fischer, Mezger 1235
Wittwe, Marie *409
Rittmann, D., Zahnarzt 1649
Roche=Versail, Wittwe 1306
Rochow, F. F., Commis 420
Rognon=Schölln, H. F. 1044
Rohner, F. M., Wirth 1122
Joh., Beck 1316
=Imhof, M., Hdlsm. *293
Schwester 952
=Fischer, Wittwe 1106
Rohr=Schmidt, Joh. 319
Ronus=Gemuseus, Christ. 105
u. Holzach, Quinc.=Hlg. 1540
=Gemuseus, Wwe., Cl. 222
Fgfr. Katharina 956
Roschet, Hier., Cattler 140
Hier., Seiler 140
Abraham, Kürschner 1709
Fgfr. Margaretha 1084
Rosenburger-Rapp, F. 1472
Rosenfeld, Eduard 1625
Rosenmund, Joh. Jak. 1544
Rößlin, F. N., Spezierer 152
F. N., Posamenter 865
Rud., Ferger 1191
Roth, Bernh., Schuhm. 72
F. F., Postfaktor 96
Heinrich, Mezger 121
Franz, Schneider 191
=Oser, Balth., Glaser 651
Roth=Hamberger, Wwe. 724A
Peter, Flachmaler 967
Martin, Wirthschaft 1031
Martin, Fabrikmeister 1033
Rudolf, Geschirrladen 1112
Abraham, Schlosser 1401
Joh. Kasp., Spengler 1548
Joh. Peter, Müller *352
Christ., Schlosser *366
=Soein, Wittwe 99
F. F., Lohnwäscher *287
Rottwill, Fgfr. Kath. *426
Roulet, Fgfr. Georgine 1203
Rübenstahl, F., Steinmeß 769
Rublin, K., Zimmerm. 1234
Rudin, H., Fabrikarbeiter 711
Joh., Fabrikfeger 1704
Ruef, Albr., Hdlsm. 492-93
Rueff, Adolph, Hdlsm. 551
Rühlin, F. G., Lohnwäscher, *258
F. G., Nestel=Fabrik. *354
Rumpf, Dan., Wundarzt 165
Karl Chr., Commis 342
=Imhof, W., Lehrer 893B
Eml., Bürstenbinder 1074
Christ., Partikular 1516
F. W., Cand. Theol. 1516
=Bachofen, Hieron. 1630
Ruprecht, Stephan 1739
Rych=Bratsch 1734
Ryff, Wwe., Wirthsch. 458
Wwe., Sal., Wasch. *283
Rybiner=Bischoff, Sam. 64B
=Schönauer, Andr. 931-33
Karl, Bandfabrikant 940
=Bischoff, Jul. 1042
=Bischoff, K., Fabr. 1084A
=Bischer, Chr. 1084A
=Menger, Eml. 1275A
=Christ, Eml. 1377
=Werthemann, Wwe. 1043
=Streckeisen, Wittwe 1365
=Bernoulli, W. *249B
119
~~~

#### 1850_p151 (1009 characters)

~~~text
138
1404 S. u. J. J. Merian . Samuel de Joh. Jakob
Merian.
Joh. Jakob de Joh.
Jakob Merian.
912 Fn. Merian-Forcart . Johann Jakob Bischoff=
Kestner.
Eduard Merian.
Fn. Merian-Forcart,
Commanditaire.
350 Merian-Frisch-
mann Rudolf Merian-Frisch-
mann.
1614 H. Merian, Sohn . Heinrich Merian, Sohn.
*144 Meyenrock, Sohn Friedrich Meyenrock.
470 Phil. Meyer-Kinder . Phil. Meyer-Kinder.
1094 Joh. Meyer u. Sohn . Susanna Meyer, geb.
Merian.
Ludwig Meyer, Sohn.
Joh. Meyer.
638 Johannes Meyer . Johann Christian Meyer.
1440 Meyer-Bischoff . Joh. Meyri, Antiquar.
258 F. Meyri, Antiqu.
Mieg-Asal . Theophil Mieg-Asal.
Joh. Gg. Bercher, Pro-
curaträger.
1691 Hans Jak.
de Georg Müller . Frau Wittwe Anna Ca-
tharina Holzach=
Schölln.
Franz Holzach.
*17 Achilles Müller . Achilles Müller.
*36 Wittwe Müller & Cons. . Frau Wittwe Müller, geb.
Kleiling, ohne Unter-
schrift.
Albert Holzach-Werten-
berg.
Georg Lindenmeier.
August Burkhardt=Jse=
lin ppa.
Wilhelm Zentgraff, ppa.
N.
1524 G. Neufirch . J. Georg Neufirch.
~~~

#### 1850_p159 (1213 characters)

~~~text
146
Kornhaus=Inspection:
Ladenamts=Verwaltung:
Land= u. Wald=Inspection:
Land=Armen-Commission:
Lösch=Anstalten:
Markt=Amt:
Militär=Collegium:
Militärdienst=Tagat.=Commiss:
Montirungs=Kammer:
Niederlassungs=Commission:
Notariats=Commission:
Ohrmgeld=Kammer:
Petitions=Commission:
Polizei=Aufsichts=Commission:
Polizei=Gericht:
Post=Commission:
Ragionenbuch=Commission:
Rechnungs=Kammer:
Revisions=Commission:
Salz=Kammer:
Sanitäts=Collegium:
Spital=Pflegamt:
Staats=Collegium:
Stadt=Cassa=Verwaltung:
Straf=Anstalt=Commission:
Waifen=Gericht:
Waifenhaus=Inspection:
Zeughaus=Kammer:
Herr Gadtrath N. Forcard.
" Kanzlist F. A. Frey.
" Stadtrath A. Sulger.
" Nathsherr C. Stump.
" Stadtrath E. Ruhiner.
" L. Lindcr, Mefferschmied.
" Nathsh. F. F. Stehlin.
" Major Fch. Kern.
" Hauptm. Th. Kündig.
" Bürgerm. F. Burckhardt.
" Nathsh. Em. Burckhardt.
" C. Geign.
" Ch. Nonus=Gemuseus.
" Stadtrath F. Bloch.
" R. Wölfflin.
" Nathsherr B. Socin.
" Stadtrath N. I Christ.
" H. Bischoff.
" Burckhardt.
" Nathsh. F. F. Ifelin.
" M. Öswald.
" Stadtrath E. Thurneyfen.
Der Herr Amtsburgermeister.
Herr Stadtrath N. Christ.
" Nathsherr E. Burckhardt.
" Chr. Nonus=Gemuseus.
" Stadtrath D. Burckhardt.
" Major Rud. Paravicini.
~~~

#### 1862_p050 (2470 characters)

~~~text
Nagionenbuch.
III XLVII
Handlungsfirma. | Interessenten u. Firmasithrer. | Natur des Geschäfts.
Linder, Joh., älter. | Jakob Ludwig Linder, allein. | Band-, Seide-, Wollen-
| | u. Merceriehandlung.
Linder, Joh. Jakob. | Joh. Jakob Linder, Bater. | Bandfabrikation.
| | Joh. Jakob Linder, Sohn.
Linder=Courvoisier. | Theophil Linder=Courvoisier, allein. | Agentur u. Commissions-
| | geschäft, hauptsächlich
| | für Rohseide.
| | Bank, Commission und
| | Spedition.
Liechtenhan u. Burck- | J. R. Liechtenhan=Hagenbach. |
| | Hieron. Burckhardt=Iselin.
| | Emanuel Schäfer, Prokuraträger.
| | F. W. de Goumois, Prokuraträger.
| | Achilles Strübin, allein.
| | Ed. Loz=Wölflin, allein.
| | Loz, Achilles, Bater.
| | Loz, Ed., et Comp.
| | Comission u. Spedit.
| | Tabak, Cigarren, Rauch-
| | requisiten u. Spazier-
| | stöcke en gros et détail.
| | Eisenhandlung u. Eisen-
| | gießerei.
| | Tabak und Cigarren.
| | Materialwaaren en gros
| | et détail.
Ludwig, Andreas. | Andr. Ludwig, allein.
Lüffi, J. J. | Joh. Jakob Lüffi. |
| | J. Schmidt=Weingen.
| | J. Jakob Lützelmann.
| | Emanuel de Peter Burckhardt.
| | Luc. Alex. Nolin, Prokuraträger.
| | Carl Hauser=Wohlich, allein.
| | Joh. Bapt. Madeux, Commanditair.
| | Franz Wohlich=Hagenbach, Com-
| | manditair.
| | Hübsch, Prokuraträger.
| | Fritz Madörin=Glaser, allein.
| | Andr. Märklin.
| | Joh. Riefer.
| | Bonneteriefabrikation.
| | Agentur u. Commission.
| | AssecuranzennebstWein-,
| | Cigarren- und Thee-
| | handlung.
| | Weinhandlung, Commis-
| | sion= und Agentur=
| | Bureau, Barfüßer-
| | gasse Nr. 3.
| | Ellenwaaren.
| | Bank, Commission und
| | Spedition.
| | Rentiers.
Madeux u. Wohlich. | Samuel Merian=Merian. |
| | J. J. Merian=Burckhardt.
| | Samuel Merian=Bischoff, Pro-
| | kuraträger.
| | Alfr. de J. J. Merian, Prokuraträg.
Madörin, F. | Fritz Madörin=Glaser, allein.
Märklin u. Riefer. | Andr. Märklin.
| | Joh. Riefer.
Magallon, H., et Comp. | Hypolite Magallon, allein.
| | Rud. Weniger=Sauerbrey, Com-
| | manditair.
Marget, J. C., Agent. | J. Emil Marget, allein.
Martin, Emil. | Emanuel Martin, allein.
Maurice, J., fils. | J. Maurice fils, allein.
Mende, J. G. | J. G. Mende, allein.
Merian=Forcart, J. | J. J. Bischoff=Kestner.
| | Gustav Christ.
| | Susanna Merian, Commanditaire.
| | Ulr. Wohnfiedel, Prokuraträger.
Merian, Sam. u. J. J. | Samuel Merian=Merian. |
| | J. J. Merian=Burckhardt.
| | Samuel Merian=Bischoff, Pro-
| | kuraträger.
| | Alfr. de J. J. Merian, Prokuraträg.
~~~

### `qwen3.8-27b`

#### 1862_p025 (0 characters — stopped at the token ceiling)

~~~text
(empty)
~~~

*26 page(s) omitted here for length — all of them are in `/home/dh/agentic_historian/agentic_historian/data/vlm_test/basel-probe-gpustack-v1`.*
