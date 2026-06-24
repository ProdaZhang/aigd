# EXAMPLE-01 · sample screen · difficulty-select / detail screen

> Purpose: roguelike difficulty select (vertical ladder) + a preview of the selected difficulty's details (rewards/affixes) + enter
> Layout pattern: left vertical difficulty ladder + central large background art + right detail card + top/bottom function bars
> Tags: #difficultySelect #verticalLadder #detailCard #affixList #roguelike #threeColumn
> Source: sample (structure reference · not a real project) / original image discarded
> Type: screen
> Size: 1856×1080 (landscape sample; geometry uses percentage 0–100, origin top-left)

## Palette (optional hint, semantic reference only — art swaps in its own assets)

background dark red-purple gradient #1c0f18→#08060c · main accent magenta #e848a0 · card face deep-purple semi-transparent #2a2442 · text #f0eaf2 · affix orange #e89048 · value green #7ad08a · currency blue #6ab0e0

## Layout (hierarchy tree: element :id [type] @{x y w h, %} z=layer "text")

```
windowTitlebar   :titlebar [chrome]  @{0 0 100 3.4}  z=9
  title                   [text]   @{0.9 0.6 12 2} z=9              "Sample Title"
  windowControls ×3       [button] @{92 0.5 8 2.8} z=9              "—  □  ✕"
topbar           :topbar   [container] @{0 4.5 100 7.5}  z=5
  back           :back     [button] @{1.8 4.9 4.8 5.3} z=6      "◁"
  screenTitle             [text]   @{7.3 5.5 6 4} z=6              "Chaos"
  seasonInfo     :season   [button] @{14 6.2 12.3 4} z=6        "ⓘ Season Info"
  currency·card  :curCard  [iconSlot] @{59 5.9 11.3 4.3} z=6      "[card] 0/4 ＋"
  currency·melody:curMelody[iconSlot] @{73 5.9 13.1 4.3} z=6      "♪ 2,424"
  home           :home     [button] @{88 5.3 3.8 5.6} z=6       "⌂"
  menu           :menu     [button] @{93.8 5.3 3.8 5.6} z=6     "≡ (red dot)"
difficultyLadder :diffrail [container] @{1.8 14 11 65}  z=4
  title                   [text]   @{1.8 14.7 9 3.6} z=5           "◎ Difficulty"
  connectorLine           [decoration] @{6.3 21 1.5 58} z=4
  difficulty·VII  :nodeVII  [button] @{4.6 25.9 4.8 8.1} z=5 shape=circle "VII"
  difficulty·VIII :nodeVIII [button] @{4 36 6 10.3} z=6 [selected·magentaGlow] shape=circle "VIII"
    selectionRing         [decoration] @{1.9 39 2 3.5} z=6 shape=circle "◎"
  difficulty·lock1 :nodeL1  [button] @{4.6 48.3 4.8 8.1} z=5 [locked] shape=circle "🔒"
  difficulty·lock2 :nodeL2  [button] @{4.6 60 4.8 8.1} z=5 [locked] shape=circle "🔒"
  difficulty·lock3 :nodeL3  [button] @{4.6 71.3 4.8 8.1} z=5 [locked] shape=circle "🔒"
centralBackgroundArt(fullscreen base image) :heroArt [bgSlot] @{0 0 100 100} z=1  "fullscreen base layer · eye-of-the-vortex centered slightly left ~37%/48% · red wings surrounding · UI floats above · swap in your own asset"
detailCard       :card     [panel]  @{68.4 13.7 30.3 70.9} z=3
  cardTitle               [text]   @{70.6 20.8 22.5 6} z=4     "Theater of Illusion"
  stageLevel              [text]   @{69.9 28.6 9.4 4.1} z=4    "🔥 Level 80"
  boss·portrait   :boss     [iconSlot] @{92.4 24.8 5 8.5} z=4 shape=circle "Bossⓘ"
  rewardMultiplierRow      [panel]  @{69.4 34 28.8 5.3} z=4     "♪ Flawless Melody gain 240%"
  reward·1                [text]   @{70.6 40.8 27.5 3.2} z=4   "· Stored Data value 14 tiers"
  reward·2                [text]   @{70.6 44.4 27.5 3.2} z=4   "· Rare Fate trigger rate +50%"
  divider                 [decoration] @{69.9 49.1 27.6 0.2} z=4
  affix·harden2           [text]   @{70.3 51 28.4 3.6} z=4     "[Harden2] Aberrations gain Unyielding 2 every 3 turns"
  affix·disease3          [text]   @{70.3 55.1 28.4 3.6} z=4   "[Disease3] Max HP reduced by 40%"
  affix·gangrene3         [text]   @{70.3 59.4 28.4 6} z=4     "[Gangrene3] From the second turn on, HP decreases 5% at the start of each turn"
  affix·neglect1          [text]   @{70.3 66 28.4 3.6} z=4     "[Neglect1] At the start of a turn, randomly discard 1 card"
  reobserve       :reobserve[button] @{68.6 76.7 29.8 6.1} z=4   "◎ Observe Again      ♪ 10"
bottombar        :bottombar[container] @{0 85.5 100 9.4}  z=5
  exploration             [text]   @{1.9 86.8 16.3 6.4} z=6        "◎ Exploration  Level 20"
  rewardInfo      :rewardInfo[button] @{21.3 86.8 18.8 6.4} z=6  "▣ Reward Info"
  weeklyProgress  :weekly   [valueBar] @{43.8 86.3 23.8 6.8} z=6   "Weekly Progress 8000/8000 (full)"
  enter           :enter    [button·primary] @{80 85.5 18.8 9.4} z=6    "Enter"
```

## Events

```
click back                         -> parent (chapter/map select)
click seasonInfo                   -> season-info popup
click home                         -> main interface
click menu                         -> system menu
click difficulty·VII / difficulty·VIII  [unlocked] -> switch difficulty → refresh detail card
click difficulty·lock*             [locked] -> hint "not unlocked"
click boss·portrait                -> boss codex/detail
click reobserve     [cost ♪10]     -> re-roll the current difficulty's affixes/rewards
click rewardInfo                   -> reward-overview popup
click enter                        -> enter the stage (Theater of Illusion · Level 80)
```

## Notes (retrieval facet)

- Three columns: left select / center atmosphere art / right detail, the classic "stage-select + detail-preview" skeleton.
- Vertical difficulty ladder: uses locks + glow to express unlock progress and current position; the selected state relies on **size enlargement + magenta glow**, not on color as a single dimension.
- The detail card has three segments: **rewards (positive, green/blue)** → divider → **affixes (negative debuffs, orange)**, with clear positive/negative color contrast; each affix is prefixed with a `[name+strength]` tag.
- "Observe Again" = a paid re-roll, placed at the card bottom for emphasis, the entry to the core numeric loop.
- The bottom bar is "left info / right action," the "Enter" button is the largest and carries a sound-wave decoration = the visual focus.
