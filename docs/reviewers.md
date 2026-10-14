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
returns a stored answer before the model is asked again.

The oracle reviewer scores every plan with the simulator's own elasticity and
declines the plan when holding scores at least as well. The oracle is the
ceiling in expectation over the agent's own candidates; a single seed's draw can
beat it, and at a demand bias of 0.9 it is ahead of the fixed-rate run in 13
seeds of 20. The control arm follows the shape of
[Coinbase's post on its fraud agent](https://www.coinbase.com/blog/part-one-how-coinbase-built-evaluated-and-post-trained-a-fraud-agent).
The oracle and the decline precision and recall are this repository's own.

The benchmark runs seeds 1 to 20 in three elasticity modes. Each mode has five
reviewers: the template, which accepts every plan, the oracle, and the three
current Claude models. In the true mode, every plan is scored with the
simulator's own elasticity, so accepting every plan is correct. The oracle and
the three models accept every plan, and each earns the template's +$32,899 a
seed. The headline figures in that mode therefore measure the plans and not the
model. The two modes with a wrong elasticity separate the reviewers.

At a fixed elasticity of 1.0, accepting every plan earns +$8,438 a seed. The
oracle earns +$30,588 and accepts 15% of the plans. The difference, $22,150 a
seed, is the value a reviewer can recover. Opus recovers 28% of it. It earns
+$14,584 a seed and beats the fixed-rate run in 17 of 20 seeds.

Opus declines 47 plans, and the oracle declines every one of them, so its
precision is 1.00. Because it catches one in seven of the oracle's declines, its
recall is 0.14. Its dollar-weighted recall is 0.25, which means its declines are
the costlier ones. The declines cluster on the plan code makes after the day-40
seat cut, a 10% raise on all seven days for stay dates 70 to 90. Opus holds
instead in 36 of the 47 cases.

Its reasons state that the estimate rests on an elasticity "fixed for the run
rather than learned from our bookings" and that the dates are behind pace and
priced above the median. At a fixed elasticity of 2.0, Opus declines one plan in
20 seeds. It ties with accept-all, +$9,557 against +$9,551, and the oracle earns
+$23,058.

Sonnet and Haiku decline no plan in any mode, so their runs equal the template's
runs. One model beats accept-all, by $6,146 a seed at a fixed elasticity of 1.0
and by nothing at 2.0. Its calls cost $0.41 per seed. For the other two models,
the value of the run is in the code, and the model writes the reasons.

The learned modes then ran live, from a prior of 1.0 and of 2.0, with and
without the cautious rule. One arm ran in the reacting market at a market
elasticity of 0.5. From a prior of 1.0, accepting every plan earns +$14,141 a
seed and the oracle +$30,828. The $16,687 a seed between them is open to a
reviewer, and Opus recovers 4% of it. It declines 7 plans, six of them the
day-40 raise it held at the fixed elasticity. The oracle agrees with every one.
The decline rate was the same at every standard error, so the uncertainty shown
in the request did not change any model's declines. In the cautious arms three
models agreed on a wrong decline because of a rounding in the display. The
request rounded a gain of a few dollars at an end of the band to "the same as
holding". Each model read that as a failed rule. That was the request's fault,
and the benchmark found it. The request now states the rule's verdict and writes
those gains to the dollar. Rerun on seeds 1 to 20, the three models declined
nothing and tie with accept-all at +$25,076 a seed. In the reacting arm Opus
held 43 of the 556 second raises it was shown. The oracle held one, because the
simulator pays the second raise. Opus did not decline the second raise as such,
because the request carries no history of the hotel's own changes, which the
next version adds. The holds cost $5,824 a seed. The first run's five commands
made 3,553 calls for $46.76, and the rerun 852 calls for $10.48
(docs/results.md).

This repository does no post-training. Every booking in this world comes from
code in this repository. A model trained on these runs learns the simulator's
Poisson draws and its elasticity of 1.5 and nothing about hotels. Its gains say
nothing about a real market. The only learning that carries over to a real
market is the kind in estimate.py. It fits one parameter to the observed
bookings.
