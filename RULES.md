# Basic Terminology
These dice are called character dice, because they reflect things about your character that can help you succeed. 
A d20 is known as a fortune die, and it transcends these benchmarks.

_Fortune die: a d20 always included. Can be 2 d20s with advantage or disadvantage._
_Character dice: Technically this means the drives, style, values, etc... But within a given roll there's no distinction between character dice and any other dice that can be added. These are d4, d6, d8, d10 or d12._
_Every roll has 1 d20. Rolls with advantage or disadvantage roll 2 d20s but only keep the result of 1 d20_

# Critical Successes
When you roll a 20 on the fortune die and your action succeeds, it is considered a critical success.
When you roll a critical success, you can choose to either increase your impact by 2 or gain 1 inspiration point.

_Bot calls out a 20 as crit success_

# Critical Fumble
A Critical Fumble means something has gone seriously wrong with your action/counter and within the scene.
When you roll a 1 on a d20 die result it is considered a critical fumble. 
When this happens, you choose one other die in your pool that didn’t roll a 1 and scratch (remove) it. 
Calculate your action total and impact with your remaining die results. 
You may roll a critical fumble and still succeed in your action. 
You also critically fumble if your action is successfully countered and you roll a 1-3 on the d20 (in other words if you fail to generate any impact at all).
Whenever you roll a critical fumble, you gain 1 inspiration point. 

_Bot calls out a 1 as a critical fumble and automatically scratches the lowest non-1 die._
_TODO: Bot should mention that a 1-3 is also a critical fumble if action is countered._

# Success or Failure
To figure out whether your action succeeds, compare your action total to the opposing counter total. 
If the counter total is higher, you fail; otherwise, your action succeeds. 
**An unsuccessful action cannot inflict stress.**

_Bot doesn't really do anything with this. Doesn't differentiate action vs counter._

_Bot *does* add up the Action total and display that. Easy for users to compare rolls since action total is simple integer._

# Impact
Once you calculate your action total, determine your action’s Impact – the effect your action has on the scene. 
Look at the dice you rolled in your pool. Each die that rolls a 4 or higher generates one point of impact. 
This includes the dice you added for your action total, as well as the fortune die. 
Character dice that roll 10 or higher generate two impact.

_Bot adds this up and displays it after the Action total_

## Minimum Impact: 
Your character is highly capable. 
Even if their action is countered, they are still able to accomplish something positive with their action. 
So long as you roll a 4 or higher on your fortune die you still generate a minimum impact of 1. 
You may spend this on any result except causing stress.  

_TODO: Maybe include note about minimum impact whenever fortune die is >=4?_

# Advantage and Disadvantage
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

# Scratching a Die
In some situations (such as when you have taken too much stress), the rules require you to scratch a die. 
This is done after you roll your dice pool. 
Once all the dice are rolled, a scratched die is removed from your roll entirely, and cannot be used for your action total or your impact—it’s as if it was never part of your pool at all.

_Bot doesn't scratch die except in case of critical fumble via d20 rolling a 1._

# The Limits of Fortune
Your action total can never include more than one d20 fortune die.

_Bot enforces this: rolls have 1d20 except for advantage/disadvantage and only 1 d20 is used in totals for those._

# Stress
- Reduce your highest die if you are Overwhelmed OR Staggered. 
- Scratch your highest die if you are Overwhelmed AND Staggered.

_TODO: look for overwhelmed, staggered or both in roll string and do this automatically for the user?_

# Impact Total
Count how many dice rolled 4+ for your Impact 
Minimum 1 Impact if your fortune die rolled 4+, even if your action was countered.

_Bot calculates this. Except doesn't display minimum impact rule. Doesn't know if action was countered._
