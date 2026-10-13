# Azul — quick reference

*A summary for settling disputes at the table, not a replacement for the
official rule book. Base game, 2–4 players, both sides of the player board:
the coloured side (standard) and the grey side (variant).*

## Goal

Have the most points when the game ends. The game ends right after the round in
which **at least one player completes a horizontal row of 5 tiles** on their wall.

| End-of-game bonus | Points |
|---|:---:|
| Each complete horizontal row | 2 |
| Each complete vertical column | 7 |
| Each colour with all 5 tiles on the wall | 10 |

## Setup

1. Everyone takes a board and puts their marker on 0. Agree before starting
   which side you play: **coloured** (standard) or **grey** (variant). See
   *Coloured side or grey side* below.
2. Factory displays: **5** for 2 players, **7** for 3, **9** for 4.
3. The bag holds 100 tiles (20 of each of 5 colours). Each factory gets 4 tiles.
4. One player holds the starting-player marker.

## A round

A round has three phases.

### 1. Factory offer

On your turn, take **all tiles of one colour** from either:

- **a factory:** the tiles you did not take slide to the centre; or
- **the centre:** the first player each round to take from the centre also takes
  the **starting-player marker**, which goes on the leftmost free space of their
  floor line and counts as a floor tile.

Then put the tiles in **one** of your five pattern lines (capacities 1 to 5):

- A pattern line holds one colour only.
- You may not use a pattern line if that row of your wall **already has that
  colour**.
- Tiles that do not fit, or that you cannot or do not want to place, go to the
  **floor line**. You may always send a whole pick to the floor.
- If the floor line is full, further tiles go back in the box lid.

The phase ends when the factories and the centre are all empty.

### 2. Wall-tiling

Going top to bottom, for each **full** pattern line, move its rightmost tile to
the wall and score it at once. The other tiles of that line go to the lid.
Incomplete lines stay for next round.

- **Coloured side:** the tile goes on the one space of that colour in its row.
- **Grey side:** you choose the space; see *Coloured side or grey side*.

**Scoring a placed tile:**

- No neighbour above, below, left or right: **1 point**.
- Otherwise count the connected horizontal group (including the new tile) if
  there is one, **plus** the connected vertical group (including the new tile)
  if there is one. A tile with neighbours both ways scores both groups, so it
  counts twice.

**Floor line:** each floor tile costs points, left to right:

| Space | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Penalty | -1 | -1 | -2 | -2 | -2 | -3 | -3 |

Your score **can never drop below 0** (the penalty stops at 0). Floor tiles go to the lid, but the
starting-player marker stays with its owner, who starts the next round.

### 3. Next round

If nobody has completed a row, the marker holder refills each factory with 4 tiles.
If the bag runs out, refill it from the lid. If it runs out again with the lid
empty, start the round anyway with partly filled factories.

## Coloured side or grey side

Everything else in this sheet is the same on both sides: setup, factory offer,
scoring a placed tile, floor penalties, the end of the game and the end-of-game
bonuses. The only difference is **where a tile may go on the wall**.

| | Coloured side | Grey side |
|---|---|---|
| Wall spaces | Each space has a fixed colour | Blank: you pick the space |
| Where the tile goes | The space of its colour in that row | Any free space in that row |
| Repeats | Cannot happen: each colour appears once per row and column by design | **No colour twice in a row, and no colour twice in a column** |
| Pattern line allowed? | Not if the wall row already has that colour | Same restriction |

Grey-side details:

- You choose the space when the tile moves across, during wall-tiling, and
  every space counts as free unless the row already holds that colour or the
  column does.
- Choose carefully: a tile placed now can leave a later line with no valid
  space. The pattern-line check at the factory offer looks at the **row**
  only, so a line can be filled legally and still turn out to be stuck.
- **Stuck line:** if a full pattern line has **no valid space** left on the wall
  (every free space in its row is in a column that already holds that colour),
  you cannot place its rightmost tile. **All the tiles of that line go to your
  floor line**, and they cost points as usual.
- Rows, columns and colours are still worth 2, 7 and 10 at the end. On the
  grey side, since no colour repeats, a complete row or column always holds all
  five colours.

## Winning

The highest score wins. **Tie-break:** the tied player with more complete
horizontal rows. If still tied, the victory is **shared**.

## Common disputes

- **Colour already on the wall row?** You cannot put that colour in the matching
  pattern line, even if the line is empty. The same applies on both sides.
- **Grey side, tile cannot be placed?** If every free space in the row is
  blocked by a column, the whole line goes to the floor line.
- **No legal pattern line?** Take the tiles anyway; they all go to the floor.
- **Starting marker:** whoever first takes from the centre in a round must take
  the marker too, with its floor penalty. It is not optional.
- **Row completed:** the game ends only after that wall-tiling phase, so every
  player scores their round first. Columns and colours count only at the very end.

## Gamelog tips

- Gamelog does not distinguish the two sides: the board is not modelled, so you
  can use either. Count the wall points yourself, including the stuck-line
  penalty on the grey side.
- Enter each player's round score (wall points minus floor penalties). Negative
  round scores are accepted, down to -14. Only the **running total** is kept at
  0 or above: if a negative round would take it lower, the app records just
  enough of the penalty to bring the total to 0, so the round shows a smaller
  loss than the one you entered.
- The row, column and colour bonus buttons only become available from round 5,
  the earliest a row can be complete. Tick them in the final round, and the
  app adds their points for you.
- The game ends automatically once a player has the row bonus ticked, and ties
  are broken on the number of rows.
