# Field Validation Results

Sprint 12 evaluated five repositories owned by the project maintainer. Absolute
paths, source contents, and potentially sensitive metadata are intentionally
excluded.

## Candidate baseline

- Candidate: `v1.0.0rc2`
- Repositories: 5
- Repository integrity preserved: 5 of 5
- Automatic command execution: none
- External JSON and Markdown reports: generated for every repository

## Results

| Repository | State | Outcome | Readiness | Audit | Findings | Classification |
|---|---|---:|---:|---:|---:|---|
| Agentic Git Janitor | clean | ready | 100 | 100 | 0 | Expected control |
| AI Research Assistant | clean | caution | 80 | 90 | 1 | Missing tests and validation strategy |
| Production Recommendation Engine | clean | ready | 100 | 100 | 0 | Expected supported project |
| AI Resume ATS Analyzer V2 | dirty | caution | 0 | 0 | 31 | Maintainability debt and dirty state |
| Real-Time Content Moderation | dirty | caution | 99 | 99 | 1 | Dirty state only |

## Finding review

The Research Assistant finding was a valid `TST001`: no Python tests were
present. The ATS Analyzer findings comprised five oversized Python files,
twenty-five oversized functions, and one dirty-tree information finding. These
were credible maintainability signals rather than false positives.

The field run exposed a reporting gap: an aggregate audit score of zero was
still classified as caution, while its warning mentioned only repository
cleanliness. Candidate `v1.0.0rc3` introduces explicit aggregate thresholds:
scores below 50 are blocked, scores from 50 through 79 require caution, and
scores of 80 or higher pass that individual readiness check.

## Conclusion

The evaluator preserved every repository and correctly handled clean and dirty
states. No safety regression or repository mutation was observed. The
field-discovered classification gap is covered by regression tests before the
next candidate is promoted.
