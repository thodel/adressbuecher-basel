# ATR batch — basel-qwen3vl30b-v1

- pages: **798**
- started: 2026-11-06T13:42:32+00:00
- wall time: 102.4 min

| model | read | skipped | failed | empty | looped | arguing | cut off | chars/page | s/page | wall |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `qwen3-vl-30b-a3b-instruct` | 798 | 0 | 0 | 0 | 17 | 0 | 15 | 2492 | 7.7 | 102.4 min |

**These columns are not quality.** There is no ground truth in this run, and characters per page measures how much a model wrote, not how much of it is right — a model that hallucinates fluently leads this table. Comparing the readings is the point; the numbers only say what each run cost and whether it completed. Measuring accuracy needs transcribed lines and `eval/linebench.py`.

## Readings that were cut off

- `qwen3-vl-30b-a3b-instruct`: 15 of 798 page(s)
  - 1841_p031
  - 1841_p037
  - 1841_p049
  - 1841_p087
  - 1841_p113
  - 1841_p173
  - 1841_p195
  - 1850_p145
  - 1862_p050
  - 1862_p051
  - 1862_p061
  - 1862_p091
  - 1862_p102
  - 1862_p156
  - 1862_p174

These pages hit the model's token ceiling and stop mid-text. The request succeeded and the text is real — there is just less of it than the page has, and it reads like a model that gave up rather than one that was interrupted. Raise the ceiling — `ATR_VLLM_MAX_NEW_TOKENS` on the gateway, `GEMINI_MAX_TOKENS` for an external reader — delete the affected results and re-run: the batch re-reads only what is missing. A reasoning model spends the same ceiling on thinking before it writes a character, so lowering the thinking level buys page as surely as raising the ceiling does (#611) — check the thinking level before buying tokens.

## Pages the model padded

- `qwen3-vl-30b-a3b-instruct`: 17 of 798 page(s) (2%)
  - 1841_p031
  - 1841_p037
  - 1841_p049
  - 1841_p087
  - 1841_p173
  - 1841_p195
  - 1862_p008
  - 1862_p050
  - 1862_p051
  - 1862_p061
  - 1862_p064
  - 1862_p091
  - 1862_p139
  - 1862_p191
  - 1862_p195
  - 1862_p201
  - 1862_p242

A run of one character twenty long or half the lines repeating is not a reading of a page. **These carry text, so every average over them is wrong** — characters per page most of all. They are described, not removed: whether the page itself is a table, a ruled form or a scan the model could not hold on to is settled by looking at it.

## Readings

798 page(s) per model — too many to put in one file. The transcriptions are in `/home/dh/agentic_historian/agentic_historian/data/vlm_test/basel-qwen3vl30b-v1`, one `.txt` per page per model.
