# Known issues

Problems found while writing the in-app rules sheets (see
`games/<name>/rules/`). Each entry says how sure we are, so confirm against the
official rules or your table's house rules before changing behaviour.

Status key: **Bug** = confirmed in the code and clearly wrong against the
official rules. **Check** = suspicious, but may be intentional or depend on
what a button stands for.

## Pocha (`games/pocha/`)

### 1. Points per trick differ from the published rules (Check)

- **Where:** `widget.py`, around lines 440-442. An exact bid scores
  `10 + 3 x tricks` and a miss scores `-3 x |bid - won|`.
- **Sources:** the Fournier rules, Ludoteka and Wikipedia all give
  `10 + 5 x tricks` and `-5 x difference`.
- **Why "Check":** the 3-point value may be a deliberate house rule. Decide
  which is intended. If 3 is intended, nothing is wrong and the sheet already
  says so. If it was a typo, fix it and note that existing stored rounds keep
  their old scores.
