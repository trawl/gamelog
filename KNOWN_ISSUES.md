# Known issues

Problems found while writing the in-app rules sheets (see
`games/<name>/rules/`). Each entry says how sure we are, so confirm against the
official rules or your table's house rules before changing behaviour.

Status key: **Bug** = confirmed in the code and clearly wrong against the
official rules. **Check** = suspicious, but may be intentional or depend on
what a button stands for.

## Skull King (`games/skullking/`)

### 1. Zero-bid and Rascal scoring use the round number, not the cards dealt (Bug)

- **Where:** `engine.py`, `computePlayerScoreClassic` and
  `computePlayerScoreRascal` use `self.getNumRound()` for the `10 x` (zero bid)
  and `15 x` (Cannonball) values.
- **Rules:** these values are based on the **number of cards dealt** that
  round, not the round number.
- **Effect:** the two are equal only in the standard 1-10 round sequence. In
  Even Keeled, Skip to the Brawl, Skirmish, Barrage and Whirlpool the scores
  are wrong. For example, in Barrage (10 cards every round) a successful zero
  bid in round 1 scores 10 instead of 100.
- **Fix idea:** use the number of cards dealt in the current round, which the
  match already knows from the selected round mode (`roundModes` in `model.py`).

### 2. No scoring mode is offered with exactly 7 players (Bug)

- **Where:** `model.py`, `listScoringModes`. The condition
  `len(players) <= 6 or len(players) > 7 and sm != "classic_scoring"` has no
  case for exactly 7 players.
- **Intent (presumably):** Classic scoring only up to 6 players; Standard and
  Rascal for any count.
- **Effect:** with 7 players the list is empty. The constructor does switch to
  `standard_scoring` above 6 players, but the combo box has nothing to show.
- **Fix idea:** `sm != "classic_scoring" or len(players) <= 6`.

### 3. Bonus buttons only unlock on an exact bid, so Rascal's half bonus can't be entered (Bug)

- **Rules:** in Rascal scoring a bid that is off by exactly one still earns
  half of the round's value, and bonus points follow the same all, half or
  none pattern.
- **Effect:** the bonus buttons only unlock when the bid equals the tricks won
  in every scoring mode, so the half bonus for missing by one can't be recorded.
- **Where to look:** `widget.py`, button enabling in `refreshButtons`, and the
  Rascal branch of `computePlayerScoreRascal` in `engine.py`.

### 4. Bonus values may not match the official rules (Check)

`scoringModes` in `model.py`:

| Button | Value in app | Official rules |
|---|---|---|
| `skullking` | 50 (classic), 40 (standard) | Skull King captures a Pirate: 30 each. Mermaid captures the Skull King: 40. |
| `pirate` | 20, up to 6 | Pirate captures a Mermaid: 20 each. |
| `mermaid` | 20, up to 2 | Not an official bonus as such. |
| `blackfourteen` | 1 | Black 14: 20. |

The buttons' icons and tooltips don't say which capture each one stands for,
so the mapping isn't clear. `blackfourteen` at 1 looks like a mistake. Work out
what each button means first, then compare. The rules sheet deliberately does
not describe the button meanings.

### 5. Tied totals share the victory (Check)

The official rule is to play more rounds until someone is ahead. The app shares
the win instead. Probably acceptable, since sharing is a project-wide
convention (see `computeWinner`), but it is a difference.

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

### 2. Tied totals share the victory (Check)

Common rules play extra one-card hands, or break the tie on fewer bidding
errors. The app shares the win instead.

## Phase 10 Master (`games/phase10/`)

### Master reuses the standard edition's score entry checks (Check)

- **Where:** `widget.py` (around lines 226 and 591) requires round scores to be
  multiples of 5, and at least 50 for a player who did not complete their
  phase. `Phase10MasterEngine` shares this with the standard edition.
- **Possible problem:** two German reviews of the Ravensburger Master (2008)
  say cards left in hand cost a flat **1 point each**, regardless of the card.
  If that is right, Master scores like 7 or 13 are valid but the app rejects
  them.
- **To do:** confirm the scoring against the rule book in the box. If confirmed,
  relax the checks for Master only.

## Other games

### Qwirkle and Scrabble: bonus buttons only count (Info)

The bonus buttons record tallies used for statistics and tie-breaks. They do
not add points to the score. This looks by design, but is easy to misread.

### Official tie-breaks differ in several games (Info)

Phase 10 (replay phase 10), Skull King and Pocha (see above), and Scrabble
(the Mattel rules give none) differ from how the app resolves ties. The app's
shared-victory and tie-break behaviour is project-wide and is documented in each
rules sheet's "Gamelog tips".
