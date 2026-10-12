# Forks

Open choices nobody has made yet. Each node says what the choice is, what is
known about it, and what making it would take. None of these is in progress.

### FRK-01 [H] Revenue or contribution as the target
- Choice: whether the agent should score candidates on room revenue instead of contribution ([[DEC-12]]), or on both.
- Replaced by: [[DEC-41]], which made the target a setting of the customer file and measured both targets on seeds 1 to 20.
- Was known: on contribution the agent is ahead in 20 of 20 seeds, by $32,899 on average, while room revenue falls in every seed, by $22,861 on average, because it raises rates on nights that may sell out and sells fewer rooms. A revenue manager judged on revenue would see a loss. The room cost is a scenario choice ([[RUL-61]]); at a lower cost the two targets move closer together.
- Links: [[DEC-12]], [[DEC-41]], [[MOD-08]], [[UNK-06]]

### FRK-02 [H] Setting AGENT_ELASTICITY apart from the simulator's ELASTICITY
- Choice: what the agent should assume about price sensitivity when the assumption is wrong, and how wrong it can be before the gain goes.
- Replaced by: [[DEC-38]], which measured it with the --elasticity modes: fixed:1.0 and fixed:2.0 for a wrong assumption, learn:1.0 and learn:2.0 for an assumption the agent corrects from the bookings.
- Was known: both constants were 1.5 ([[RUL-39]], [[RUL-21]]) and the agent's was its own ([[DEC-26]]); nothing had been measured with them apart.
- Links: [[DEC-26]], [[RUL-39]], [[UNK-07]]

### FRK-03 [O] A length-of-stay model
- Choice: whether bookings should have a length of stay, so that a minimum-stay rule can be simulated rather than advised ([[DEC-10]]).
- Known: the Books hold rooms per stay date with no link between nights ([[DAT-07]]); the minimum stay is recorded as advice marked not simulated ([[DAT-15]]). A stay-length model needs a distribution of lengths, bookings that take rooms on several nights, and a rule for turning a one-night request away on a two-night minimum.
- To decide it: write the booking draw for multi-night stays first and check that the fixed-rate occupancies stay within 60% to 90%; the one-random-number-per-draw rule ([[DEC-22]]) must survive it.
- Links: [[DEC-10]], [[MOD-06]]

### FRK-04 [O] Swapping the model for a locally hosted one
- Choice: whether the decisions could come from a model run on the owner's machine instead of the hosted one ([[RUL-46]]).
- Known: the call sits behind the Client protocol in [[MOD-09]]: a client needs one method, complete(system, prompt, schema), returning JSON that fits the schema ([[DEC-34]]). The cache records "source": "model" without saying which model, so answers from two models would share one cache and would need the model's name in the record ([[DAT-17]]) to be told apart. The template already shows the loop running with no model at all.
- To decide it: write a client for a local server, give the cache record a model field, and compare the two models' choices on the same seed's queue.
- Links: [[MOD-09]], [[DAT-17]], [[UNK-01]]
### FRK-05 [O] Deliberate price tests, to learn the elasticity faster
- Choice: whether a learning agent should make small deliberate rate changes on ordinary nights, far from selling out, to move the rate ratio and sharpen its elasticity estimate sooner, instead of learning only from the changes it makes for other reasons.
- Known: in a fixed-rate run the rate ratio barely moves (the standard deviation of its log is 0.011 to 0.027 by hotel), the bookings alone would pin the elasticity near the prior, and the agent's own rate changes supply most of the usable variation ([[DEC-38]]). On days 10 and 20, when the convention and the new flights are decided, a learning agent's estimate still sits near its prior, and the cautious rule ([[DEC-39]], [[DEC-43]]) holds wherever the band is wide, which is why it keeps 76% of the true arm's gain from a prior of 1.0 and 54% from 2.0 rather than all of it. A test costs the contribution the moved nights give up, which on this market is small for a 5% move on a night that will not sell out ([[DEC-12]]) and which the simulator could measure. The owner's choice was to record this and leave the agent alone.
- To decide it: add a candidate kind "test" that a learning agent may take on nights far from selling out while the standard error is above a threshold, mark those changes in the log so that the estimator can tell them apart, and measure on seeds 1 to 20 the day-20 standard error and the gain against the cautious arms.
- Links: [[DEC-38]], [[DEC-39]], [[DEC-43]], [[MOD-16]], [[CON-06]], [[CON-11]], [[UNK-07]]
