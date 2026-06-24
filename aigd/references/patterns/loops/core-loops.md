# Gameplay paradigm · common core loops (5 templates)

> **Purpose**: ammunition for `aigd-concept`'s concept interview. The methodology only gives "process"; as an interview guide, the AI must be able to **cut weak directions and propose the right conventions** — the core loop is the first cut: a game's "what to do — why keep going" compressed into one loop sentence; if the loop doesn't close, don't design further.
> **How to use**: align with the user on one loop (or a primary + secondary pair) → drill into that loop's "driving variable / feedback / stall point" item by item → land it as a system list. **Don't stuff in 3 loops at once**; for a new project, first run one primary loop closed.

---

## Universal three-stage form

Any core loop is the closed loop of **invest → convert → yield back**: the player invests (time/resources/operations) → the system converts (growth/progress/output) → the yield-back (stronger ability/new content/new resources) feeds back into the next round of investment. **The criterion for the loop closing**: the yield-back can **lower or speed up** the next round of investment, and **there is always a next reachable goal**. Wherever it breaks = that link is the stall point.

---

## Template 1: collect → progress → validate

```text
collect (gacha/drop/synthesis to obtain units) → progress (push power up via numeric axes) → validate (stages/Boss/arena consume power) → drop materials/unlock → back to collect
```
- **Driving variable**: power. Progression raises power, validation sets power thresholds.
- **Feedback**: clear a stage → drop progression materials + unlock a higher stage → higher power requirement.
- **Common stall point**: the **gradient mismatch** between progression output and validation thresholds — materials given too fast (mindless steamrolling, content consumed too fast) or too slow (wall-stuck, quitting).
- **Ask**: power formula? How many progression axes (see [`battle-unit-progression.md`](battle-unit-progression.md))? How is a stage's recommended power set? What short-term goal is given at a stuck point?

## Template 2: explore → acquire → build

```text
explore (open the map/unlock a region) → acquire (gather/pick up resources) → build (base/tech/production) → unlock farther exploration → back to explore
```
- **Driving variable**: production capacity + exploration radius.
- **Feedback**: building raises production and unlocks; production supports farther exploration.
- **Common stall point**: production **exponential inflation** (late-game resources overflow into meaninglessness, see trap page §1); or the build prerequisite chain is too long, with new content long out of reach.
- **Ask**: resource types and conversion chains? Is production linear or exponential? Does exploration-unlock rely on resources or on progress? Is there a production cap / storage pressure as a throttle?

## Template 3: match → compete → settle (PVP)

```text
match (tier/MMR pairing) → compete (real-time/turn-based match) → settle (rank up/down + rewards) → adjust roster/progress → back to match
```
- **Driving variable**: rank/score + roster strength.
- **Feedback**: a win raises rank + rewards, a loss drops points, driving adjustment.
- **Common stall point**: matchmaking fairness (steamroll matches drive people away); **paid power** directly buys win rate (pay-to-win imbalance); the rank-reward gradient lets the top/bottom tiers lie flat.
- **Ask**: is win/loss driven by operations or by numbers? Match dimensions (power/rank/activity)? Season reset and protection mechanisms? The upper bound of progression's effect on win rate?

## Template 4: gacha → team-up → push stages

```text
gacha (obtain characters/cards) → team-up (formation/bonds/Build) → push stages (main story/event stages) → resource backflow to gacha and progression → back to gacha
```
- **Driving variable**: character-pool breadth + Build strength.
- **Feedback**: pushing stages gives gacha tickets and progression materials; new characters open new Builds.
- **Common stall point**: **pity variance** (the unlucky-player experience collapses, see trap page §8); too few bond/Build dimensions causing "only one optimal answer" and making collection meaningless.
- **Ask**: gacha pity mechanism? Are characters orthogonal (each has a place to shine)? Formation constraints (position/bond/element counter)? Are stage-push resources enough to raise new characters?

## Template 5: farm → harvest → trade (economy/simulation)

```text
farm (plant/produce/idle) → harvest (output items) → trade (sell/process/fulfill orders) → reinvest to expand production → back to farm
```
- **Driving variable**: output efficiency + currency circulation.
- **Feedback**: trading earns currency → expand production / unlock high-value output.
- **Common stall point**: **inflation** (currency output > recovery, prices collapse); a too-deep production chain loses newbies; idle output makes online operation meaningless.
- **Ask**: what are the currency's output faucet and recovery sink respectively (there must be a sink)? Production-chain depth? The yield ratio of idle vs active operation? Is there market regulation (tax/loss)?

---

## Interview landing: from loop to system list

Once a loop is chosen, map each link to **at least one system**, and mark the inter-link "yield-back" as a **cross-system reference**:
- E.g. (Template 1): collect = gacha/drop system, progress = unit-progression system, validate = stage/battle system; "stages drop progression materials" = the `item.id` the stage system **reverse-provides** to the progression system (broadcast-type, registered in the manifest F table).
- Each stall point → a `[to-confirm]` convention (gradient/cap/pity), for the user to decide, don't decide numbers on their behalf.
- Multi-loop project: build the full set of systems for the primary loop first, mark secondary loops `[to-design]`, and only greenlight them once the primary loop's playtest runs through (see the manifest A-table dependencies).
