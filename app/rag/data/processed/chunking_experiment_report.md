# Chunking Experiment Report

## 1. Objective

Compare baseline fixed-size chunking with structure-aware chunking and select a strategy using the supplied locked test cases.

## 2. Configurations

| Configuration | Description |
|---|---|
| Baseline | Fixed-size character chunking |
| Selected | Structure-aware chunking using paragraph boundaries where available |
| Chunk size | 500 characters |
| Overlap | 50 characters |

**Note:** These configurations use character counts, not token counts.

## 3. Locked Test Cases

| Case | Query | Expected Source | Expected Section |
|---|---|---|---|
| CH-001 | When is supervisor approval required? | KB-002 | 3. Financial Redress Thresholds |
| CH-002 | What evidence is needed for a fee complaint? | KB-003 | 2. Required Intake Fields |
| CH-003 | When should suspected account takeover be escalated? | KB-004 | 4. Security Escalation Indicators |

## 4. Experimental Results

| Test Case | Baseline Matches | Selected Matches |
|---|---:|---:|
| CH-001 | 2 | 2 |
| CH-002 | 1 | 1 |
| CH-003 | 1 | 1 |
| **Total** | **4** | **4** |

Both strategies preserved the expected source sections across all three locked cases.

## 5. Failure Analysis and Observations

- No missing expected source sections were observed in the three diagnostic checks.
- KB-002 financial redress table content was divided across two chunks.
- A phrase within the table, "System must not auto-apply," was split across a chunk boundary.
- Table content is extracted, but table row boundaries are not consistently preserved.
- The diagnostic checks establish chunk presence, not semantic retrieval ranking or answer accuracy.

## 6. Selected Strategy

**Selected output: `chunks_selected.jsonl`**

Structure-aware chunking was retained as the selected implementation because it is designed to respect paragraph boundaries where those boundaries are available.

However, the experiment did not demonstrate a measurable advantage in expected-section coverage: both strategies returned the same matching counts.

The selected strategy should therefore be treated as the implementation choice for the next indexing exercise, not as a proven retrieval-performance improvement.

## 7. Limitations and Future Improvements

1. Current chunk sizing is character-based rather than token-based.
2. Table-aware chunking should be improved to preserve complete rows and related column values.
3. Additional evaluation should measure semantic retrieval relevance, ranking, and answer accuracy.
4. More test cases should cover approval thresholds, escalation triggers, and conflicting policy conditions.

## 8. Deliverables

- `chunks_baseline.jsonl`
- `chunks_selected.jsonl`
- `chunking_experiment_report.md`

**Conclusion:** Both chunking strategies passed the three supplied chunk-presence checks. The selected structure-aware output is retained for the next exercise, with table-boundary handling and semantic retrieval evaluation documented as limitations.