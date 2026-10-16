# The model as a reviewer

The model does not set rates. Code computes every candidate action for a hotel
and estimates the contribution of each one before the model is asked. The model
then sees one hotel's queue of plans for the day. It accepts or declines each
plan and writes the reason in both cases. Code checks the answer against the
options in the request, so the model cannot return a rate that code did not
compute.

Every gain is measured against a control run with no rate changes. The same seed
produces the same bookings in both runs, so the accepted plans are the only
difference between them. A run can be repeated exactly, because the cache
returns a stored answer before the model is asked again, and each stored answer
carries a digest of the system prompt, so an edited prompt stops the rerun
instead of returning the old reasons.

The oracle reviewer scores every plan with the simulator's own elasticity and
declines the plan when holding scores at least as well. The oracle is the
ceiling in expectation over the agent's own candidates; a single seed's draw can
beat it, and in the default mode at a demand bias of 0.9 it is ahead of the
fixed-rate run in 15 seeds of 20, which a sign test puts at p 0.041. In the reacting market the oracle
scores the competitors' reaction as immediate, where the simulator applies it
three days later, so its ceiling there covers the agent's own candidates only.
The control arm follows the shape of
[Coinbase's post on its fraud agent](https://www.coinbase.com/blog/part-one-how-coinbase-built-evaluated-and-post-trained-a-fraud-agent).
The oracle and the decline precision and recall are this repository's own. Of
that shape the repository has the control arm and an oracle-scored reviewer, and
it has no online or shadow evaluation, no human in the loop, no outcome labels
from the world, no post-training and no incident path.

The benchmark ran seeds 1 to 20 in three elasticity modes on 2026-10-15 on world
v2. Each mode has five reviewers: the template, which says yes to every plan,
the oracle, and the three current Claude models. The template is a stand-in that
answers in the model's place when there is no key; it says yes to every plan and
writes a reason from the entry's own figures. In the true mode, every plan is
scored with the simulator's own elasticity, so saying yes to every plan is
correct. The oracle and the three models say yes to every plan, and each earns
the template's +$16,164 a seed. The headline figures in that mode therefore
measure the plans and not the model. The two modes with a wrong elasticity
separate the reviewers.

At a fixed elasticity of 1.0, saying yes to every plan loses $6,265 a seed,
because the agent prices with an elasticity below the simulator's 1.5 and raises
too often. The oracle earns +$13,107 and accepts 11% of the plans. The
difference, $19,372 a seed, is the value a reviewer can recover. Opus recovers
34% of it. It earns +$346 a seed and beats the fixed-rate run in 9 of 20 seeds.

Opus declines 230 plans, and the oracle declines every one of them, so its
precision is 1.00. Because it catches three in ten of the oracle's declines, its
recall is 0.31, and its dollar-weighted recall is 0.33. At a fixed elasticity of
2.0, saying yes to every plan loses $2,687 a seed and the oracle earns +$6,006.
Opus declines 38 plans with a precision of 0.92 and earns -$2,514, a recovered
share of 0.02.

Sonnet declines 8 plans at 1.0 and 5 at 2.0, each one the oracle also declines,
and Haiku declines none, so both stay within $100 a seed of saying yes to every
plan. At a fixed elasticity of 1.0 Opus's calls cost $0.71 per seed, Sonnet's
$0.26 and Haiku's $0.02. For the two cheaper models, the value of the run is in
the code, and the model writes the reasons.

The learned modes then ran live, from a prior of 1.0 and of 2.0, with and
without the cautious rule. One arm ran in the reacting market at a market
elasticity of 0.5. From a prior of 1.0, saying yes to every plan earns +$804 a
seed and the oracle +$13,199. The $12,395 a seed between them is open to a
reviewer, and Opus recovers 10% of it. It declines 41 plans, the oracle agrees
with every one, and it earns +$2,105. Sonnet declines 3 plans and Haiku 3.
Opus's declines now follow the uncertainty the request shows: it declines 7 of
the 8 plans whose estimate has a standard error under 0.15 and 6 of the 344 at
0.35 and over. With the cautious rule, saying yes to every plan earns +$12,527
and the oracle +$14,854. Opus declines 5 plans and earns +$12,561, Sonnet
declines none, and Haiku declines one plan the oracle accepts. From a prior of
2.0, Opus declines 12 plans without the rule, with a precision of 0.92, and none
with it. In the reacting arm Opus held 25 of the 577 plans it was shown on stay
dates the hotel had changed within 14 days, and the oracle held none, because
the simulator pays the second raise. The holds cost $2,491 a seed. Since world
v2 the request lists the hotel's earlier changes on those dates, with the rooms
booked since against the rooms expected. The five learn commands made 3,737
calls for $48.64 at list prices, and the fixed modes 4,007 calls for $37.23
(docs/results.md).

This repository does no post-training. Every booking in this world comes from
code in this repository. A model trained on these runs learns the simulator's
Poisson draws and its elasticity of 1.5 and nothing about hotels. Its gains say
nothing about a real market. The only learning that carries over to a real
market is the kind in estimate.py. It fits one parameter to the observed
bookings.
