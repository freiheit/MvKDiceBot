<!--
13th Age dice-rolling reference, compiled from the books kept locally (gitignored):
  - 13th Age 2nd Edition Player's Handbook   (cited "PHB")
  - 13th Age 2nd Edition GM Guide            (cited "GMG")
  - 13 True Ways (1st-edition supplement)    (cited "TTW")
Mechanics (numbers / procedures) are stated plainly; short quotes mark the
load-bearing wording. This is a reference for the dice the bot rolls and the
many 13th Age rules that are too situational to automate. 13th Age is © Pelgrane
Press; quotes are brief excerpts for interoperability/reference only.
-->

# 13th Age (2nd Edition) — Dice-Rolling Rules

## What the bot does

MvKDiceBot's `plainroll` is a generic d20 roller usable for 13th Age:

- It tracks the **escalation die** per channel (`escalation`/`nextround`) and, for
  a single d20, adds it to the total (`w/Esc`).
- For a single d20 it calls out the likely-relevant natural results: **20** (crit),
  **1** (fail), **even/odd**, and a possible **two-weapon hit** on a natural **2**.

Everything else below is **not** automated — it's a reference for the table.

---

## Player's Handbook (PHB)

### Core resolution

- Attacks: roll **d20 + ability mod + level + other mods** vs. the target's
  defense (AC, PD, or MD); equal-or-higher hits. Multi-target attacks roll a
  separate d20 per target but *"roll damage only once."*
- Skill checks/backgrounds: **d20 + ability mod + level + relevant background
  points** vs. a DC set by the environment; only the single highest applicable
  background applies to a check.

### Natural-roll triggers (a defining 13th Age mechanic)

- Many powers fire on a *specified natural d20 result* (e.g. "Natural 11+",
  "Natural 2–5", "natural even hit"). Per the PHB these *"add to"* the hit/miss
  result and *"[trigger] regardless of whether the attack hits or misses."*
- A roll high enough to crit but low enough to miss *"is still a crit"*, and
  crit effects also satisfy effects that "require a hit."

### Crits, fumbles, miss damage

- **Crit:** *"Every attack roll that is natural 20 is a crit ... for double
  damage."* Ongoing damage is doubled too, but only for the first turn. Stacking
  multipliers compound (double a double → triple, etc.).
- **Crit range** can be widened by powers; each point drops the number needed by
  1 (e.g. +2 → crit on 18–20). Optional harder-game variant: base crit range 18+.
- **Natural 1** has no effect on the target — *not even* miss damage. (No default
  fumble table; the GM may impose a consequence "in a precarious position.")
- A miss deals damage only if the attack says so; most damage bonuses apply to
  hits only.

### The escalation die

- Set to **+1 at the start of round 2**, **+1 per round to a max of +6**. Each PC
  adds the current value to **attack rolls**.
- *"PCs only"* as a rule — most monsters/NPCs don't add it (notable exceptions
  like dragons do).
- **De-escalation:** if the party avoids the fight (or combat all but stops), the
  die doesn't advance and can drop/reset to 0. Delaying can also let the GM hold
  it.
- It is *"only 'even' at 2, 4, and 6"* and *"At zero the escalation die doesn't
  exist."* Effects that read the die use its value when the effect is created
  unless they say otherwise.

### Initiative

- Per battle: **d20 + Dexterity mod + level** (one roll shared by each identical
  monster type). Ties go to the monsters.

### Disengage

- **Disengage check: 11+**, with a **−1 penalty per extra foe** beyond the first.
  On a failure you don't move and lose the move action.

### Saves

- A save is *"a d20 roll with no standard modifiers."* Difficulties:
  **Easy 6+ / Normal 11+ / Hard 16+** (unspecified = normal 11+). Saves are rolled
  at the **end of your turn**.
- **Ongoing damage** is taken at end of turn, then a normal save (11+) ends it;
  failure repeats. Mooks ignore ongoing damage.

### Recoveries & recovery dice

- PCs start with **8 recoveries** (fighters 9). Using one: spend it and *"regain
  lost hit points by rolling recovery dice equal to your level + your
  Constitution modifier"* (recovery die size is d6/d8/d10 by class).
- CON bonus scales: **×2 at 5th**, **×4 at 8th** plus **+5 per epic level**.
- Players may take **average** instead of rolling. Out of recoveries: half
  healing and a **−1 to defenses and attacks** (stacks) until a full heal-up.

### Rally

- Once per battle, a standard action to **rally** (spend a recovery to heal).
  Each *additional* rally in the same battle first needs a **quick-action normal
  save (11+)**; fail and the quick action is wasted.

### Death & dying

- At **0 hp or below**: unconscious, gain a **Skull**, make **death saves**. You
  die at negative half your max hp, or at **5 Skulls** (a four-Skull variant
  exists).
- Death save (d20, at the start of your turn while down): **15 or lower** → a step
  toward death + another Skull; **16–19** → spend a recovery and return to
  consciousness (that's your whole turn); **20+** → heal *and* act normally.
- A quick rest clears all but one Skull; the last clears on a full heal-up.

### Last gasp saves

- Some "death attack" effects force **last gasp saves**: the first turn you may
  take one action then roll a **hard save (16+)**; fail and you're helpless and
  can only keep rolling. **Four failures** in a battle = the bad outcome (petrify,
  etc.); a **natural 20** lets you act normally. An adjacent ally can help (then
  recovery only needs an 11+). Last gasp saves don't give Skulls.

### Rest & recharge

- After a battle (at a quick rest), **roll d20 for each expended recharge
  power**; meet/beat its recharge number (e.g. **6+ / 11+ / 16+**) to regain it.

### Other PHB dice rules

- **Coup de grace:** attacking an engaged, helpless enemy (after the setup) is an
  **automatic crit**.
- **Resistance** is rated to the attacker's **natural d20**: e.g. *resist 12+/16+/
  18+*. If the natural roll is below the resistance number the attack deals half
  damage; sources with no attack roll are simply halved.
- **Two-weapon fighting:** trained classes with a 1-handed weapon in each hand
  *"hit"* on a natural **2** (no extra attack is granted).
- **Weapon/damage:** **1 Weapon die per level + ability mod** (mod ×2 champion,
  ×4 epic; +5/epic level). Die-size steps: d4 < d6 < d8 < d10 < d12 < 2d6 < 2d8…
- **Damage-roll shortcuts:** roll all dice; or roll one die ×count; or "even =
  max / odd = min"; or 1d6 → 1 min / 2–5 avg / 6 max.
- **Icon relationships:** **3 points**; at the start of each arc roll **1d6 per
  point** — each **5 or 6** is an advantage to spend that arc (no 5/6 at all →
  a GM-chosen connection that always comes with a twist). A **combat connection**
  lets you add a **second d20** to one attack/save/roll; then roll a d20 for a
  **twist** (narrative connection: 1–5; combat: 1–10).
- **Ability scores:** standard arrays, point buy, or rolling **4d6 drop lowest**
  (or the "Roll Four" hybrid: an 18 and 16 plus four 4d6-drop-lowest in order).
- **Dice averages** (round up on an odd number of dice): d4≈2.5, d6≈3.5, d8≈4.5,
  d10≈5.5, d12≈6.5, d20≈10.5.
- **Random direction:** orient one d12 toward the GM, roll another, match the face.
- **Mooks:** track damage against the mob; it's staggered at half its bodies.
- Kin/class examples keyed to the die (situational): Barbarian rage (roll d12 +
  escalation, **9+** to rage), Wood Elf elven grace (1d8 **≤ escalation** → extra
  standard action), Human "quick to fight" (roll initiative twice, keep one),
  Halfling perseverance (natural 1–2 grants a later reroll), many kin/class powers
  trigger on natural 16+/even/odd.

---

## GM Guide (GMG)

### Escalation die — control & exceptions

- The GM judges whether to advance it after a one-sided opening; significant
  **reinforcements** can stall or set it back. It **resets to 0** when a new
  battle/initiative starts.
- Some monsters use or attack it: most **dragons** *"escalate"* (black/blue/red
  add it; green/white don't); a staggered sahuagin adds it and widens its crit
  range by it; effects can **steal** it (a rakshasa resets it to 0 for the PCs and
  adds the stolen value to itself), **freeze** it, or key big effects to it (e.g.
  an aura that deals damage *"whenever the escalation die advances"*).

### Tiered skill-check DCs (the load-bearing numbers)

| Tier | Normal | Hard | Ridiculously hard |
|------|:------:|:----:|:-----------------:|
| Adventurer | 15 | 20 | 25 |
| Champion | 20 | 25 | 30 |
| Epic | 25 | 30 | 35 |

- The GM may nudge DCs off multiples of 5, and need not make higher-tier PCs roll
  trivial lower-tier tasks ("make them roll when it's dramatic").

### Environmental threats & traps

- The **Environmental Threats** table pairs the DCs above with trap **attack
  bonuses** and **impromptu damage** by tier, e.g. adventurer normal = **+5**,
  single-target damage **2d6** (multi **1d10**); hard = **+10 / 2d8 / 1d12**;
  champion normal = **+10 / 4d6 / 2d8**; etc. Trap/obstacle/hazard damage *is*
  still rolled, even at epic.
- Spotting a trap is usually a **normal or hard Wisdom check**; a trap easy to
  spot tends to attack on the *hard* row and vice-versa. Sample traps list their
  own notice DC / disarm DC / attack / damage (e.g. an adventurer poison-arrow
  trap: notice **15**, disarm **13**, **+5 vs PD**, **2d6 + 5 ongoing poison**).

### Other GMG dice patterns

- **Natural-roll triggers (general):** monster extra effects default to **16+**,
  but can use even/odd, 5 or less, 6+, etc. 2E often replaces a fixed-natural
  trigger with *"a hit that forces an immediate save."*
- **Monster dice:** breath weapons **recharge on a d6 (5+)**; random monster
  abilities are rolled on **d6/d8/d10/d12** tables; troll-style **regeneration**
  is an easy save (6+) at the start of its turn. (By design, monster *damage* is
  fixed/average rather than rolled.)
- **Icon dice as story-guides (optional):** roll a **d12**, or roll a PC's icon
  dice and use **5s/6s**, to pick which icon is involved in an unexpected event.
- **Battlefield dangers** keyed to rolls, e.g. *"Natural even misses are hits,"*
  expanded crit ranges, or "natural 1–5 botches" for a hazard.
- **Surprise/ambush:** resolved with Wisdom checks (hard by default) and a
  **+5/+10 initiative** bonus to the ambushers.

---

## 13 True Ways (TTW) — class-specific special dice

(1st-edition supplement; mechanics still commonly used. Routine attacks omitted.)

- **Summoning (general):** summoned creatures don't get the escalation die unless
  you spend a quick action to command them (one quick action covers a whole mook
  mob).
- **Chaos Mage:** the spell *category* each turn is **random** — draw a stone or
  roll **d6** (1–2 attack / 3–4 defense / 5–6 iconic), ignoring repeats until the
  battle resets. Iconic spells pick an icon with a **d12**. Getting critted forces
  a roll on the **d100 High Weirdness** table.
- **Commander:** runs on **command points** gained via dice — e.g. hit in melee →
  **1d3** points; "Weigh the Odds" → **1d4**; icon **5/6** → bonus points. Spend
  them to grant allies a reroll, an extra save (best of multiple d20s), a +bonus
  up to the escalation die, etc., and a couple of tactics raise/lower the
  escalation die.
- **Druid:** Strength druids use **d10 recovery dice** (others d6). Beast/Shifter
  form keys off the die — *"Natural Even Hit"* (bigger die) vs *"Natural Odd Hit"*
  (smaller), miss → repeat the attack; Warrior-druid "flexible attacks" trigger on
  natural even/odd/specific numbers; several beast aspects roll **2d20 keep one**
  or reroll a natural 2 with widened crit range.
- **Monk:** form chain (opening → flow → finishing); **JAB d6 / PUNCH d8 / KICK
  d10** damage per level; **ki** (1 + WIS per day) can **shift a natural attack
  result by 1** (never a natural 1); always two-weapon (natural **2** reroll);
  "Dance of the Mantis" rolls an extra d20 on finishing attacks.
- **Necromancer:** "Wasting Away" — subtract CON from spell attacks if positive,
  but you survive to **five** failed death/last-gasp saves; summons come in
  **1d3+1** (later 1d4+1) and can be given the escalation die; several spells
  require/scale with the escalation die, and an epic feat can **steal** it.
- **Occultist:** gain **focus** (standard action, draws opportunity attacks),
  spend it on interrupt spells; many let you **retain focus** when the spell's
  attack roll falls in a low band (e.g. **1–5**, **1–10**) — i.e. you tend to keep
  focus on a *miss*.

---

## Situational / easy-to-forget dice rules (cross-book)

- "Specified natural result" effects fire **whether the attack hits or misses**
  (PHB) — the single most important quirk for a dice tracker.
- The escalation die is **even only at 2/4/6** and **absent at 0** (PHB), and many
  monster/hazard effects only switch on at a given escalation value (GMG/TTW).
- **Resistance** and monster effects compare the **natural** d20, not the total
  (PHB/GMG) — so the raw die matters even on a clear hit.
- **Two-weapon natural 2** auto-hits for trained classes/monk (PHB/TTW).
- Death saves (**16–19** vs **20+**), last gasp (**hard 16+**, four failures),
  and Necromancer's extended **five-save** clock (PHB/TTW).
- Recharge powers, breath weapons (**d6 5+**), regeneration (**easy 6+**), and
  rally re-attempts (**11+**) are all separate d20/d6 rolls people forget
  mid-battle (PHB/GMG).
- Icon relationship dice (**5/6 per d6**) and the **twist** roll after spending a
  connection (1–5 narrative / 1–10 combat) (PHB/GMG).
