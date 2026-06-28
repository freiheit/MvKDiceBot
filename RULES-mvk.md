<!--
Rules below are verified against the current corebook PDF
(Mecha_Vs_Kaiju_202X_Corebook.pdf), which supersedes the older
202X-V1.05 .docx. Quoted lines are from that corebook. The italic
"_Bot ..._" notes describe what MvKDiceBot actually does.
-->

# Mecha vs Kaiju (MvK) Rules

Just tbe rules and terminology around dice rolling.

## Basic Terminology

These dice are called character dice, because they reflect things about your character that can help you succeed.
A d20 is known as a fortune die, and it transcends these benchmarks.

- _Fortune die: a d20 always included. Can be 2 d20s with advantage or disadvantage._
- _Character dice: Technically this means the drives, style, values, etc... But within a given roll there's no distinction between character dice and any other dice that can be added. These are d4, d6, d8, d10 or d12._
- _Every roll has 1 d20. Rolls with advantage or disadvantage roll 2 d20s but only keep the result of 1 d20_

## Critical Successes

Corebook:
> When you roll a 20 on the fortune die you use for your total it is considered a critical success. You can choose to either increase your Impact by 2 or gain 1 Inspiration point.

- _Bot calls out a 20 on the kept fortune die as a critical success and notes the +2 impact / 1 inspiration choice._

## Critical Fumble

A Critical Fumble means something has gone seriously wrong with your action/counter and within the scene.
When you roll a 1 on a d20 die result it is considered a critical fumble.
When this happens, you choose one other die in your pool that didn’t roll a 1 and scratch (remove) it.
Calculate your action total and impact with your remaining die results.
You may roll a critical fumble and still succeed in your action.
You also critically fumble if your action is successfully countered and you roll a 1-3 on the d20 (in other words if you fail to generate any impact at all).
Whenever you roll a critical fumble, you gain 1 inspiration point.

- _Bot calls out a 1 as a critical fumble and automatically scratches the lowest non-1 die._
- _Bot mentions that a 1-3 is possibly a critical fumble if action is countered._

## Success or Failure

Corebook:
> To figure out whether your action succeeds, compare your action total to the opposing counter total. If the counter total is higher, you fail; otherwise, your action succeeds. A successfully countered action cannot inflict stress.

- _Bot adds up the Action total and displays it; easy for users to compare rolls since it's a simple integer._
- _Optionally, give the bot a counter total with `vs N` (or `counter N`) and it reports Success/Failure (tie = success). On a failure it notes the action can't inflict stress but still gets minimum impact._

## Impact

Once you calculate your action total, determine your action’s Impact – the effect your action has on the scene.
Look at the dice you rolled in your pool. Each die that rolls a 4 or higher generates one point of impact.
This includes the dice you added for your action total, as well as the fortune die.
Character dice that roll 10 or higher generate two impact.

- _Bot adds this up and displays it after the Action total_

### Minimum Impact

Corebook:
> Your minimum impact when taking an action is 1, even if the action is successfully countered (so long as the Fortune Die rolled 4 or higher).

- _Bot notes "Minimum impact 1 from the fortune die" when the only impact is the lone point a 4+ fortune die guarantees (the floor that applies even if countered). A 4+ fortune die already contributes 1 impact on its own, so the floor only binds when no character die rolled 4+; with a sub-4 fortune die and no qualifying character dice the impact is genuinely 0._

## Advantage and Disadvantage

Sometimes the rules grant you Advantage on a particular roll.
When that happens, you roll one additional fortune die as part of your pool.
You still choose two die results for your action total, only one of which may be a d20.
If multiple situations affect a roll and each one grants advantage, you still only add one additional d20 to your pool.

There are also times when the rules impose Disadvantage on a roll.
When you roll with disadvantage, you roll one additional fortune die as part of your pool, but the highest-rolling d20 in your pool is scratched.
If multiple situations affect a roll and each one grants disadvantage, you still only add one additional d20 to your pool.

If circumstances cause a roll to have both advantage and disadvantage, you are considered to have neither of them, and you do not add an additional d20 to your pool.
This is true even if multiple circumstances impose disadvantage and only one grants advantage or vice versa.
In such a situation, you have neither advantage nor disadvantage.

_Bot looks for "advantage" or "disadvantage" in the roll request, rolls 2 d20s and discards the higher or lower appropriately._

## Scratching a Die

In some situations (such as when you have taken too much stress), the rules require you to scratch a die.
This is done after you roll your dice pool.
Once all the dice are rolled, a scratched die is removed from your roll entirely, and cannot be used for your action total or your impact—it’s as if it was never part of your pool at all.

_Bot scratches a die on a critical fumble (d20 rolling a 1) and for Overwhelmed+Staggered stress (see Stress, below)._

## The Limits of Fortune

Your action total can never include more than one d20 fortune die.

_Bot enforces this: rolls have 1d20 except for advantage/disadvantage and only 1 d20 is used in totals for those._

## Stress

Corebook (Being Overwhelmed or Staggered):
> If you are Overwhelmed OR Staggered: Reduce the highest die in your pool for all rolls.
> If you are Overwhelmed AND Staggered: Scratch the highest die in your pool for all rolls.

Corebook quick reference clarifies "highest die" as the highest die **type**:
> Overwhelmed. ... Reduce the highest die type in your pool.
> Staggered. ... Reduce the highest die type in your pool.
> Overwhelmed+Staggered. Scratch the highest die type in your pool.

(The older .docx was self-contradictory here — one passage said the
Overwhelmed-AND-Staggered case was "reduce, then drop the highest die result
from your total." The corebook settles it: that case is simply "scratch," and
"highest die" means highest die _type_, i.e. size.)

- _Bot looks for `overwhelmed`/`staggered` in the roll string and adjusts the pool **before rolling**: one of them reduces the largest character die type one size (d12→d10→…→d4, and a d4 is removed); both together scratch the largest character die type. The fortune d20 is never reduced/scratched (the rules never boost/reduce the fortune die)._

## Impact Total

Count how many dice rolled 4+ for your Impact
Minimum 1 Impact if your fortune die rolled 4+, even if your action was countered.

_Bot calculates this and notes the minimum-impact-1 case. It only knows an action was countered if you give it a counter total (`vs N`)._

## Boost / Reduce (pool building)

Corebook:
> The rules sometimes tell you to boost a die, changing it from a die of one size to one of a larger size ... or to reduce a die (the reverse...). When you boost a d12 in your dice pool, you keep the d12, but add an extra d4 to your pool as well. When you reduce a d4 in your pool, you remove that die entirely. You never boost the Fortune die up or down, and no other die size can boost to a d20.

- _Bot supports `boost dN` / `reduce dN` keywords that apply this before rolling: boost steps a die up one size (boosting a d12 keeps it and adds a d4); reduce steps it down (reducing a d4 removes it). The die must already be in the pool, and the fortune d20 is never boosted/reduced. (You can also just type the dice you end up with.)_

%# Ability-driven dice mechanics from the corebook

These come from specific character abilities/perks/powers. The bot now automates
the parts that are pure dice math (via keywords); anything that requires knowing
which of your dice is the "Drive die" etc. is left to the player.

- Flat modifiers — _Bot: `+N`/`-N` adjust the **action total**; `impact +N` (or `+N impact`) adjusts **impact**. (MvK is mostly a dice-not-modifiers system; these cover the rare flat bonuses.)_
- Perk "Dice": "Add a d6 to your dice pool. • Boost a die that helps you. • Double a specific trait die in your pool. • Reduce a die that opposes you. • Reroll your dice pool." — _Bot: boost/reduce are keywords (see Boost/Reduce); add/double a die by just typing it; reroll by rolling again._
- Perk "Impact": "Add 2 points of impact towards a specific outcome." — _Bot: `impact +2`._
- "Unstable": "Apply a cumulative -1 modifier to your action total each time this is used." — _Bot: `unstable` keyword applies -1 (the per-use stacking is up to you — repeat the keyword or use `-N`)._
- "Burst": "Double your Drive die and add +2 Impact ... roll one additional fortune die ... but the highest-rolling d20 in your pool is scratched." — _Bot: `burst` keyword adds +2 impact and rolls with disadvantage; add the doubled Drive die yourself._
- "Burn Out": "Add three dice to determine your action total." — _Bot: `burnout` keyword totals the highest three dice (the extra trait dice are added by you)._
- Spend Inspiration: before rolling, add a trait die or roll with Advantage; after rolling, add an unused die to your total / use one as an extra impact. — _Not automated; add the die or use `advantage`._
- "Blowback": "If you roll a 1 on any die in your pool the GM may immediately reroll that and use it as an Impact die on you or an ally." — _Not automated (GM-side)._
