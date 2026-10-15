# Forks

The choices nobody has made yet, and the ones that were closed. An open fork
is [O]: its node says what the choice is, what is known about it, and what
making it would take. A closed fork is [H] and names the decision that closed
it. None of these is in progress.

### FRK-01 [H] Revenue or contribution as the target
- Choice: whether the agent should score candidates on room revenue instead of contribution ([[DEC-12]]), or on both.
- Closed by: [[DEC-41]], which made the target a setting of the customer file. It measured both targets on seeds 1 to 20 ([[RES-07]]).
- Was known: on contribution the agent is ahead in 20 of 20 seeds, while room revenue falls in every seed ([[RES-01]]). The agent raises rates on nights that may sell out and so sells fewer rooms.
- Judgement: a revenue manager judged on revenue would see a loss. The room cost is a scenario choice ([[RUL-61]]); at a lower cost the two targets move closer together.
- Links: [[DEC-12]], [[DEC-41]], [[MOD-08]], [[UNK-06]]

### FRK-02 [H] Setting AGENT_ELASTICITY apart from the simulator's ELASTICITY
- Choice: what the agent should assume about price sensitivity when the assumption is wrong. The second question is how wrong it can be before the gain goes.
- Closed by: [[DEC-38]], which measured it with the --elasticity modes. fixed:1.0 and fixed:2.0 stand for a wrong assumption ([[RES-03]]). learn:1.0 and learn:2.0 stand for one the agent corrects from the bookings ([[RES-04]]).
- Was known: both constants were 1.5 ([[RUL-39]], [[RUL-21]]), and the agent's was its own ([[DEC-26]]). Nothing had been measured with them apart.
- Links: [[DEC-26]], [[RUL-39]], [[UNK-07]]

### FRK-03 [O] A length-of-stay model
- Choice: whether bookings should have a length of stay, so that a minimum-stay rule can be simulated rather than advised ([[DEC-10]]).
- Known: the Books hold rooms per stay date with no link between nights ([[DAT-07]]). The minimum stay is recorded as advice marked not simulated ([[DAT-15]]).
- Needs: a distribution of lengths and bookings that take rooms on several nights. It also needs a rule for turning a one-night request away on a two-night minimum.
- To decide it: write the booking draw for multi-night stays first and check that the fixed-rate occupancies stay within 60% to 90%. The one-random-number-per-draw rule ([[DEC-22]]) must survive it.
- Links: [[DEC-10]], [[MOD-06]], [[UNK-12]]

### FRK-04 [O] Swapping the model for a locally hosted one
- Choice: whether the decisions could come from a model run on the owner's machine instead of the hosted one ([[RUL-46]]).
- Known: the call sits behind the Client protocol in [[MOD-09]]. A client needs one method, complete(system, prompt, schema), returning JSON that fits the schema ([[DEC-34]]). The remaining choice is the local client itself.
- Cache: the cache record names its model ([[DAT-17]]). An agent given another model keeps its answers in their own folder ([[DEC-23]]). Two models' answers are told apart.
- Template: the template already shows the loop running with no model at all.
- To decide it: write a client for a local server. Then compare the two models' choices on the same seed's queue with the benchmark ([[MOD-23]]).
- Links: [[MOD-09]], [[DAT-17]], [[DEC-23]], [[UNK-01]], [[MOD-23]]

### FRK-05 [O] Deliberate price tests, to learn the elasticity faster
- Choice: whether a learning agent should make small deliberate rate changes on ordinary nights, far from selling out. The aim is to sharpen its elasticity estimate sooner.
- Known: in a fixed-rate run the rate ratio barely moves, so the bookings alone would pin the elasticity near the prior. The agent's own rate changes supply most of the usable variation ([[RES-10]], [[DEC-38]]).
- Precision: the rate ratio's spread in a fixed-rate run is 0.011 to 0.027 by hotel ([[RES-10]]). The data then cannot outweigh the prior. Only the hotel's own moves of several per cent across most of its bookings do.
- Timing: the convention and the new flights are decided on days 10 and 20. A learning agent's estimate still sits near its prior then ([[RES-04]]). The cautious rule ([[DEC-39]], [[DEC-43]]) holds wherever the band is wide.
- Cost: a test costs the contribution the moved nights give up. On this market that is small for a 5% move on a night that will not sell out ([[DEC-12]]). The simulator could measure it.
- Owner: the owner's choice was to record this and leave the agent alone.
- To decide it: add a candidate kind "test" for nights far from selling out, allowed while the standard error is high. Mark those changes in the log. Then measure the day-20 standard error and the gain against the cautious arms.
- Links: [[DEC-38]], [[DEC-39]], [[DEC-43]], [[MOD-16]], [[CON-06]], [[CON-11]], [[UNK-07]]

### FRK-06 [O] A read-only dashboard over the stored tables
- Choice: whether to add a read-only view over the stored tables ([[DAT-28]]): the queue, the decisions and the feeds by day.
- Known: the tables already hold every flag, plan and decision with the day it was known on. replay rebuilds a day from them alone ([[DEC-42]]), and a view would read and never write.
- To decide it: pick a reader, such as a notebook, a static page or DuckDB's own tools. Keep the rule that nothing reads a day before it is written.
- Links: [[DAT-28]], [[MOD-21]], [[DEC-42]]

### FRK-07 [O] Reviewers from other providers
- Choice: whether a model from another provider could review the queue next to the three Claude models the bench runs ([[RUL-79]]).
- Known: the client behind the Client protocol is Anthropic's SDK ([[MOD-09]]). The call record keeps its usage fields and its fallback flag ([[DAT-30]]). A second provider's client is out of scope here.
- Needs: a client whose complete(system, prompt, schema) returns JSON that fits the schema. Measured records its usage as it is, and PRICES needs its prices ([[RUL-80]]). The bench then takes it as one more --model ([[DEC-48]]).
- Links: [[FRK-04]], [[MOD-09]], [[MOD-23]], [[DAT-30]], [[RUL-79]], [[RUL-80]]

### FRK-08 [O] A market response as the default
- Choice: whether MARKET_ELASTICITY should be above 0.0 by default ([[RUL-87]]). That would move every pinned result and re-pin [[RES-01]] and [[RES-02]].
- Known: at 0.0 a matched raise is free, and the reaction run measured the ratchet ([[RES-24]]). With the reaction on, 0.5 and 1.0 cut the gain by a third and by more than half ([[RES-26]]).
- Without: without the reaction, the term acts only where a shock moves the median ([[RES-27]]).
- Needs: a value with a source ([[UNK-15]]). Then a run of seeds 1 to 20 at it, with and without the reaction. [[RES-01]] and [[RES-02]] would then need new pins, and the README's results would change.
- Reaction: the README's next version also makes the competitors react by default ([[DEC-51]]). A matched raise would then stop being a demand gift ([[DEC-59]], [[RES-41]]).
- Links: [[RUL-87]], [[DEC-52]], [[RES-01]], [[RES-02]], [[RES-24]], [[RES-26]], [[RES-27]], [[UNK-15]]

### FRK-09 [O] A comp move that follows our own change as a flag cause
- Choice: whether a comp median move that follows our own change should count as a flag cause ([[RUL-65]]). It arrives within REACTION_LAG days on the same stay dates ([[RUL-84]]), so the detector could read it as the reaction.
- Known: at 0.5 with the reaction on, the cautious learn arm changes 702 stay dates twice within 14 days ([[RES-26]]). Its rate changes are 784. That is the arm anyone would run, and the flag lifts the hold, so it raises again ([[DEC-51]]).
- Needs: the hotel's own change days per stay date among detect.py's inputs, and a rule for the window. The oracle already scores the followed median ([[DEC-52]]), so the arm would measure the flag alone.
- Live: the reviewer arm at 0.5 shows Opus 556 plans on dates changed within 14 days. It holds 43 ([[RES-37]], [[MEA-14]]). Its reasons cite the cautious band's display and never the earlier raise, which the request does not carry.
- Before: the simulator pays the second raise, so the oracle holds 1 of the 556. Opus's holds therefore cost $5,824 a seed. Opus does not decline the second raise as such. The 43 holds are the before measurement for this fix.
- History: Opus did not decline the second raise as such, because the request carries no history of the hotel's own changes. [[DEC-45]] keeps each decision's outcome in the tables, so the request can carry that history next.
- Links: [[DEC-45]], [[DEC-51]], [[DEC-52]], [[RUL-65]], [[RUL-84]], [[RUL-85]], [[RES-24]], [[RES-26]], [[RES-37]], [[MEA-14]]

### FRK-10 [O] An arrival time column
- Choice: whether each row should carry PASSENGER_ARRIVAL_TIME_LOCAL. It would come from the departure time, a block time from the distance and the origin's time-zone offset.
- Known: the rows carry a departure time only ([[DAT-01]]). An airport hotel's demand turns on the arrival hour. The feed page should not claim a departure-only row is the feed's shape.
- Needs: a block time per distance band and a time-zone offset per origin station on the Route ([[DAT-03]]). build_schedule would write the column. Nothing in the simulator reads it yet.
- Links: [[DAT-01]], [[DAT-03]], [[MOD-01]], [[DEC-35]], [[UNK-05]]

### FRK-11 [O] A periodic re-plan beside the anomaly flags
- Choice: whether every stay date should be re-planned on a fixed cadence, beside the flags that an anomaly raises ([[DEC-13]]).
- Known: at a demand bias of 1.1 the uncorrected learner raised on false pace flags ([[RES-31]]). The raises paid, because the market was larger than the start rates assume. --level removed them and the correct raises too ([[DEC-54]]).
- Reason: the agent acts only on a flag, and a market that is simply larger raises none. The pace rule of Part D is anomaly-driven in the same way and will share the blind spot.
- Needs: a cadence, and on it a plan for every stay date with the usual candidates. The queue's minimum would keep the model calls down. The oracle grades such plans as it grades any other.
- Links: [[DEC-13]], [[DEC-54]], [[RES-31]], [[DEC-55]], [[UNK-08]]

### FRK-12 [H] Per-hotel booking curves in the customer file
- Choice: whether each hotel should carry its own booking curve ([[CON-01]], [[RUL-68]], [[RUL-69]]), with a group base on the convention hotel's event dates and a late curve at the airport hotel.
- Known: on world v1 one transient curve served all four hotels ([[DAT-27]]). The pace baseline is normal demand ([[MOD-07]]), so a hotel that received a shock ran ahead of pace every day until the stay date.
- Consequence: "pace" meant that a shock's bookings had arrived, and the pace control priced the shocks at one remove ([[DEC-55]], [[RES-42]]).
- Closed by: [[DEC-66]], on world v2. Every pinned figure changed, and the template arms reran for nothing; the live arms wait for the world v2 benchmark ([[UNK-16]]).
- Links: [[CON-01]], [[DAT-27]], [[MOD-07]], [[DEC-55]], [[DEC-66]], [[RES-42]], [[UNK-16]]

### FRK-13 [H] The stored route refuses a later day
- Choice: whether stored_sources should take the day it is made for and refuse a later one, as the simulated sources do ([[MOD-19]], [[MOD-21]]).
- Closed by: [[DEC-61]], which made both routes' sources hold only what the day knows.
- Known: the simulated sources are made for a day and refuse a later one. The stored sources answer any day the tables hold, so a replay of day 10 can read day 34 ([[DEC-42]]).
- Needs: an as_of_day on the four stored sources and on stored_sources(), passed by run-day and replay ([[MOD-12]]). No figure changes.
- Links: [[MOD-19]], [[MOD-21]], [[DEC-40]], [[DEC-42]], [[RUL-03]]
