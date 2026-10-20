# PRD v2: Next Steps

**Proposed V2.** This document is a design for a future release. Nothing in it is built, and the demo stays as v1.6 built it. Every figure here comes from the v1.6 code, the README, `docs/results.md`, `docs/limits.md`, the seed-7 demo file, a recorded rehearsal, or TypeSafe's own published material, and each one names its source.

## Summary

Version 1 of the agent prices every flagged night with code, then asks one language model one question about each hotel's plans, which is whether to accept each plan or hold. The v1 results show five places where that single question isn't enough. The agent can't tell a real move in the competitors' prices from ordinary daily noise. It can't tell when a move was caused by its own earlier change. It can't see when bookings disagree with its forecast. It can raise the same night twice before the first raise has had time to show anything. In a second market, it proposed cutting prices on good news.

Version 2 splits the model's job into two roles and puts code on both sides of each one.

1. Code checks that the data is complete and that the plan is still valid. A plan that fails is held.
2. An investigator, which is a language model with read-only tools, decides which evidence to look at. It looks into the conflicting signals and writes down what it found and what it couldn't find out. It can't choose an action.
3. Code assembles an evidence packet. The packet holds the facts the tools returned, their sources and timestamps, the plan's identifier and the investigator's findings, with those findings kept separate and labeled as the investigator's.
4. A decider reads the packet and chooses one of three dispositions, which are to recommend the plan, to hold, or to send it for human review. The proposed decider is Jev, TypeSafe's System One model. It sits behind the same interface as the v1 reviewer, so the v1 reviewer can fill the role for comparison.
5. Code checks the disposition against the evidence rules, records it, and blocks any action the rules don't allow. Any failure becomes a hold, and the failure is recorded as the reason.

The design keeps every v1 guarantee. Code computes every number, no model sees anything before the moment it was known, a run with the same seed gives the same results, and a past day can be replayed without calling a model. Version 2 sits behind a setting, so every v1 result stays reproducible byte for byte.

Each role has to show it's worth having. The benchmark measures the investigator and the decider separately. Each one ships only if it beats the simpler thing it would replace.

## Why now: what the version 1 results showed

Each finding below is something the v1.6 repo measured about itself, and each one points to a question the agent should ask before it acts.

### Finding 1. The model adds nothing when the plans are right, and only part of the value when they're wrong

In the default run, every reviewer said yes to every plan, because the plans were right (README, "What the model adds"). That includes the template stand-in and all three models. The benchmark makes the plans wrong on purpose by giving the agent the wrong elasticity, which is its estimate of how strongly guests react to price. With a fixed wrong elasticity, Opus recovered 34% of the margin a perfect reviewer would have recovered, and it declined 230 plans. With a learned elasticity, it recovered 10% and declined 41. Sonnet and Haiku did no better than saying yes to everything (README). The benchmark's 7,744 calls cost $85.87.

In v1 the model sees only the plan and its numbers, so it has no way to find out why a plan might be wrong. Version 2 gives one model ways to look and asks a second component to decide on what was found.

### Finding 2. A move in the competitors' prices can be noise

The rate shop is the simulated service that reports the four competitors' prices every day. Each competitor's price moves by up to 3% either way every day. So the middle of the four prices, called the comp median, wanders up to 3% around its starting level even when nothing has happened (`docs/limits.md`). The agent flags a night when the comp median moves 5% or more since the day before, which means ordinary noise sometimes crosses that line.

In the seed-7 run, 23 flags had a comp-median move as their only cause. Code held 22 of them. One went through, which was the airport hotel's 10% raise on Mon 1 Feb. It was decided on day 23 and was worth an estimated $410 more than holding (seed-7 demo file). No scripted news touched that night that day, so the move came from the rate shop's daily noise. A revenue manager would check whether the move lasted more than one day before acting on it.

### Finding 3. The agent can mistake its own footprint for news

The simulator can make competitors react. With the reaction on, each competitor moves half of the hotel's price change three days after the change takes effect (`docs/results.md`, "The competitor reaction"). In that setup, 427 of the 898 comp-median flags in the default mode followed the hotels' own earlier changes, and 23 stay dates were changed twice within 14 days. The agent raised a price, the competitors followed it, the agent read their move as news, and it raised again. The results document records this as open question FRK-09, which asks whether a competitor move that follows our own change should count as a reason to flag at all.

A revenue manager would ask whether the competitors moved because of something we did.

### Finding 4. The forecast can be wrong, and nothing checks it

The agent's demand forecast uses the simulator's own formula, so in the default run it's always right. When the simulator's demand is made 10% weaker without telling the agent, the gain falls from +$16,164 to +$1,069 a seed, and the agent is ahead in only 12 of 20 runs (README). The agent keeps raising prices as if demand were where its forecast says.

The bookings carry the warning, because when demand is weaker than forecast, rooms book more slowly than the forecast expects. Version 1 shows the model one read-back line for nights it changed before, such as "since then 2 rooms booked against 1 expected". No code acts on that line, and the model sees nothing about pickup on other nights. A revenue manager would compare what the forecast expected with what actually booked before trusting the plan.

### Finding 5. Two quick raises, and a cut on good news

On day 18 the lifestyle hotel raised Sat 20 Mar by 10%, to $264, because bookings were well ahead of pace, with 40 rooms booked against a usual 24.8. On day 20 the new flights flagged the same night, and the agent raised it another 10%, to $290.40. Only two days separated the two raises, and the read-back line on day 20 said "since then 2 rooms booked against 1 expected" (seed-7 demo file). That night became the run's largest single gain, +$3,979 in contribution, so the second raise paid. Even so, a revenue manager would want to know whether the first change had time to show anything before stacking a second change on the same night.

In the harbour market, the airlines added seats on day 20, and the agent proposed cuts at all three hotels (the recorded harbour rehearsal of 2026-10-18).

- The city-centre hotel's plan lowered prices 5%, worth an estimated $1,230 more than holding, and the model declined it.
- The resort's plan lowered prices 5% on six days and raised Saturday, worth $2,680, and the model accepted it.
- The station hotel's plan lowered prices 5% from Friday to Sunday, worth $210, which clears that market's $200 minimum, and the model accepted it too.

A plan that moves against the direction of the news needs an explanation, and v1 doesn't ask for one.

## Why split investigating from deciding

In v1, one model call does two jobs. It reads the evidence and it chooses the action. Version 2 separates those jobs for three reasons.

The first reason is repeatability. In the author's experience on a production agent system, calculations moved out of the agent and into code because the agent didn't produce them repeatably. Decisions made over a fixed, ordered set of evidence proved more repeatable than workflows that also asked the model to calculate. That's one team's experience, so this design tests it instead of assuming it. The v1 repo already shows one data point. In the rehearsal of 2026-10-18, ten live reruns sent the recorded intraday run's ten requests with the same digests, and the model accepted all 13 plans every time while only the wording of its reasons changed (the author's rehearsal notes, outside this repository). That's an easy case, because every plan was right. Version 2 measures repeatability where the plans are wrong.

The second reason is auditability. When the investigator's findings and the decision come from separate steps, the record shows what evidence existed at the moment of the decision. A reviewer can then judge the decision against that evidence and nothing else.

The third reason is replaceability. The decider sits behind one narrow interface that takes an evidence packet and returns one of three dispositions. Any component that meets that interface can fill the role, which means the v1 reviewer, Jev, or the accept-all template used as a control. The benchmark can compare them on identical packets.

## The proposed decider: Jev

TypeSafe describes Jev as its first public System One model. In TypeSafe's words, it takes "unstructured state in" and returns "typed probabilistic decisions out" ([Introducing System One Models & Jev](https://typesafe.ai/blog/introducing-system-one-models-and-jev)). According to its documentation, a caller sends a state, as text or JSON, with one or more questions ([TypeSafe docs](https://docs.typesafe.ai/)). A Choice question picks one option from a list. The answer comes back with the choice, a probability for each option and a confidence. TypeSafe lists classification, routing and scoring among its intended uses. Jev doesn't generate free text.

Those properties match the decider role. The role asks for one choice among three fixed options, and the answer has to be a typed value that code can check.

This design treats Jev's suitability as a hypothesis. TypeSafe's material makes claims about calibration, consistency, speed and price. Those claims are the company's own and haven't been checked here, and the model hasn't been calibrated on hotel pricing decisions. TypeSafe lists Jev as available in early access, with a waitlist. Nothing here assumes Jev beats the v1 reviewer. The benchmark decides that.

Jev doesn't write text, so it can't explain its choice in words. The explanation a person sees is built from three recorded parts, which are code's summary of the evidence, the investigator's findings labeled as the investigator's, and the disposition with its probabilities. No text written by a language model is ever presented as Jev's reasoning.

## What code should fix first, without a model

Some findings have a plain rule as their fix. A rule is cheaper, faster and easier to test than a model, so version 2 does these first as separate changes, each measured on the existing benchmark.

1. Code stops counting a competitor move as a flag cause when it follows the hotel's own change on the same nights within the reaction delay. That settles FRK-09 one way, and the reaction sweep measures whether it helps.
2. Code requires a comp-median move to last across two shops before it raises a flag. On the four-times-a-day clock that means two ticks, and on the daily clock it means two days. The cost is a one-shop delay on a real move, and the benchmark measures that cost.
3. Code computes how sensitive each plan is. That means the plan's value over holding if demand were 10% lower or 10% higher, and if the elasticity were 1.0 or 2.0. The v1 reviewer receives these as extra lines in its request, so even without the new roles it can see a plan that only wins when the forecast is exactly right.

The investigator and the decider then handle what's left. Those are the cases where signals disagree and the right answer depends on weighing them, which fixed rules handle badly.

## Goal

Every plan the agent recommends has been checked against the evidence a careful revenue manager would want. A viewer can see which checks were made, what they returned, what the investigator concluded and which disposition the decider chose.

## Non-goals

Version 2 doesn't add a general chatbot, arbitrary queries, several cooperating agents, a generic orchestration framework, a new forecasting model or any write to an operational system. It doesn't change how the simulator works or how the planner calculates and selects candidate rates. It isn't a production deployment plan. It makes no claim about revenue at a real hotel. It doesn't read unstructured outside text, which is phase 5 below and a separate design.

## Who uses it, and what they see

The first user is a revenue manager on a brand's central revenue team, who would receive the agent's recommendations at a real hotel. That person sees each recommendation with an audit view underneath it. The view shows the checks code ran, the tools the investigator called, what each tool returned, the investigator's findings, and the disposition with its probabilities. A plan sent for human review reaches that person as a question to answer. One example is "Bookings for these nights are running 12% below forecast. Is there a reason demand would be weaker this month?"

The second user is the engineer or analyst checking the system. That person sees every tool call, its arguments and its result in the stored tables. They can replay any past decision without calling a model, and they can compare the deciders on identical packets in the benchmark.

## How version 1 works today

Version 1 makes a decision in five steps at every tick. A tick is one of the moments in a day when new data arrives, one a day by default and four with `--ticks 4`.

1. `detect.py` reads the four feeds as of that tick and flags the nights where something changed. A flag is a run of consecutive stay dates with one or more causes, such as "ahead of pace" or "seats up".
2. `plan.py` prices each flag for every day of the week the flag covers. It scores five options, which are holding the rate, raising it 5% or 10%, lowering it 5%, and, when the comp median has dropped, lowering it halfway to the new median. It scores each option by contribution, which is room revenue minus the cost of servicing each room sold. It picks the best option for each day of the week separately, because a Friday and a Tuesday can sell very differently. The result is a plan and its value at stake, meaning how much more the plan is expected to earn than holding. A plan worth less than $250 more than holding is held by code at this step.
3. `model.py` sends one hotel's remaining plans to the model in one request, and the model answers "plan" or "hold" with a short reason for each. Code checks that the answer names only the plans it was given. Answers are cached under a digest of the request, and without an API key a template answers instead and is never cached.
4. `agent.py` applies the accepted plans from the next tick and holds those nights for 7 days, unless new news lifts the hold.
5. `stored.py` writes the flags, plans and decisions to tables, and `demo_data.py` turns them into the demo page's tables.

In the seed-7 run, step 1 raised 117 flags over 60 days, and 6 of them ended in a rate change (seed-7 demo file).

## What changes in version 2

Version 2 replaces step 3 with five steps for each plan that passes step 2. Everything before and after stays the same.

### Step 3a. Gates, run by code

Before any model call, code checks three things, and a plan that fails any of them is held with the reason recorded.

1. Every feed has data for the decision time. On the stored route, where the agent reads tables, a missing day of bookings or a missing shop counts as a failure. On the simulated route the feeds are always complete, so tests inject the fault by deleting rows.
2. The plan is still valid. Our rate on the plan's nights has to be the rate the plan priced from, and those nights can't be under a hold.
3. The plan's nights fall inside the window the agent may act on, which is the next 90 nights.

These checks run as code because their outcome can't depend on whether a model decides to look. A stale feed blocks a recommendation every time.

### Step 3b. The investigation, run by a language model with tools that code owns

The investigator receives the facts v1 sends, which are the flag, its causes, the plan and its value at stake, all as text that code wrote. It also receives the list of tools below. It may make up to four tool calls for each plan, in any order. Code answers each call by reading the four feeds as of the decision time, so no tool can return anything that wasn't known at that moment.

1. `news_detail` returns the scripted news behind the flag. For an airline filing, that's the routes, the dates they take effect and the change in arriving passengers for each night. For an event, it's the dates, the demand uplift and any competitor raise. For a competitor cut, it's which competitors cut and by how much. The tool answers whether the news covers the plan's nights, and in which direction it moves demand.
2. `pickup` returns, for each night in the plan, the rooms on the books, the usual pace at this point, and the rooms booked over the last 3 and 7 days against the number the forecast expected over the same days. The tool answers whether bookings are confirming the forecast, which is finding 4.
3. `median_history` returns the comp median for the plan's nights at each of the last five shops, with each competitor's price at the latest one. The tool answers whether a median move lasted or reverted, and whether one competitor moved or all four did, which is finding 2.
4. `own_changes` returns this hotel's price changes on the plan's nights and the nights around them over the last 14 days, with the days since each change and the read-back line for each one. The tool answers whether a competitor move followed our own change, which is finding 3. It also answers whether the last change has had time to show, which is finding 5.
5. `plan_sensitivity` returns the plan's value over holding, computed by `plan.py`, under four alternatives. They are demand 10% lower, demand 10% higher, an elasticity of 1.0, and an elasticity of 2.0. The tool answers whether the plan wins only when the forecast is exactly right, which is finding 4 again.

The investigator ends by calling `submit_findings` with three fields.

1. The findings are one or two sentences for each question it looked into. Each sentence cites the tool call and the field it relies on.
2. The unresolved questions are anything the tools couldn't answer, written as questions a revenue manager could answer.
3. The conflicts are any pair of findings that point in opposite directions, such as "the flights add passengers on these nights" and "pickup is 12% below forecast".

The investigator can't choose a disposition. It can't propose a rate, change a candidate or do arithmetic. Code checks that every citation points to a field a tool actually returned in this investigation, and that every figure in the findings appears in a tool result. A finding that fails either check is dropped from the packet and recorded as dropped.

### Step 3c. The evidence packet, assembled by code

Code assembles one packet for each plan. It keeps two kinds of content apart and labels both.

The verified part holds every tool result, with the tool's name, its arguments, the day and tick it read as of, and a digest of the result. It also holds the plan's identifier, its value at stake and the candidates it was chosen from. Code computed everything in this part.

The interpreted part holds the investigator's findings, unresolved questions and conflicts, labeled as written by the investigator.

Code puts both parts in a fixed order, so the same evidence always produces the same packet. That matters because the repeatability test sends identical packets to the decider again and again.

### Step 3d. The decision, made by the decider

The decider reads the packet and chooses one of three dispositions.

1. `recommend_plan` means the plan should go ahead as code priced it.
2. `hold` means the current rate stays.
3. `human_review` means a person should answer a question before anything changes.

The decider can choose only among these three. It can't create a plan, change one or pick a different candidate. If the whole decision ever came down to picking the largest computed value, code would make that choice instead. The decider's job is to judge whether the evidence supports acting, whether conflicting signals outweigh the plan, and whether a person needs to look.

Three components can fill this role behind the same interface.

1. Jev answers one Choice question over the packet and returns the disposition, a probability for each of the three, and a confidence.
2. The v1 language-model reviewer reads the packet and returns a disposition. This is the comparison arm.
3. The accept-all template always returns `recommend_plan`. This is the control.

The probabilities and confidence Jev returns are recorded and studied, and nothing acts on them. This design sets no threshold that approves anything automatically, and none will be set until the benchmark shows the probabilities mean something on these cases.

### Step 3e. Final checks and the record, run by code

Code checks the disposition before anything happens.

1. The disposition has to be one of the three allowed values, and it has to concern the plan in the packet.
2. A `recommend_plan` needs a minimum set of verified evidence that depends on the flag's cause. A cause from competitor prices needs `median_history` and `own_changes`. A cause from news needs `news_detail`. A cause from pace needs `pickup`. Every recommendation needs `plan_sensitivity`. The minimum set never uses more than three of the four calls, so the investigator always has at least one call of its own choosing.
3. The gates from step 3a still have to pass at the moment of applying, because data can change between the investigation and the decision.

Missing required evidence, an invalid answer or a failure in either model becomes a hold, and code records the reason. In the simulator, `human_review` counts as a hold for the money, because no person is there to answer. The benchmark counts it separately, so a decider that sends everything to review shows up as useless.

Code then records the packet, the disposition, its probabilities, the checks and the outcome. Anything a person later reads as an explanation is assembled from that record, so it can only describe evidence that existed when the decision was made.

## Architecture

### New modules

1. `investigate.py` runs the gates, the investigator's tool loop and the final checks. It's an agent module, so it reads data only through the four interfaces in `sources.py`, and `tests/test_sources.py` adds it to the list of modules it checks.
2. `tools.py` holds the five tools and `submit_findings`. Each tool is a pure function of the sources as of the decision time and the plan, and it returns text and numbers that code wrote. It's also an agent module.
3. `evidence.py` assembles the evidence packet in its fixed order and computes its digest. It's an agent module too.

### Changed modules

1. `model.py` gains a client that runs a conversation with tool calls for the investigator. It also gains a `Decider` interface with three implementations, which are the v1 reviewer adapted to packets, a Jev client and the accept-all template. The v1 call stays exactly as it is, so a run without the new setting doesn't change.
2. `agent.py` calls `investigate.py` in place of `model.ask` when the setting `--investigate` is on. A second setting, `--decider`, chooses the decider.
3. `plan.py` exposes the plan's value under the four alternatives that `plan_sensitivity` reports. It computes them with the functions it already uses to score candidates.
4. `stored.py` and `sql/schema.sql` gain the table `investigation_steps`, with one row for each tool call. The row holds the day, tick, hotel and plan, the step number, the tool, its arguments, its result and a digest of the result. The `decisions` table gains the disposition, the decider's name, its probabilities, the evidence packet's digest and any unresolved question.
5. `bench.py` gains the arms and worlds described under "How we'll know it works".
6. `demo_data.py` and `sql/demo.sql` gain an `investigation` table with display text for each step. `demo_page.py` draws it as an audit view in a closed expander under each recommendation, so the page still computes nothing and still fits the window. The audit view is part of the future release and isn't added to the interview demo.
7. `CLAUDE.md` adds the three new modules to rule 6. `kg/` gains their nodes, a decision node for version 2 and a results node for each benchmark run.

### The cache and replay

Version 1 caches one answer for each hotel and tick, keyed by a digest of the request and a digest of the system prompt. Version 2 caches every model turn. Each investigator turn is keyed by a digest of the conversation up to that turn, and the conversation includes every tool result. Each decider answer is keyed by the packet's digest. If the data under a tool changes, its result changes, the digest changes and the cached answer is refused. That's the same protection v1 has against reusing an answer to a different question.

A replay reads the cached turns and answers along with the stored tool results. It checks that the tools still return the same results from the tables, and it never calls a model. Replay tests auditability. Repeated fresh calls test consistency, and the benchmark runs both.

### The scripted investigator

A scripted investigator stands in for the language model offline, the way the template does in v1. It calls the minimum evidence for the flag's cause and writes fixed findings from the results. For example, it writes "pickup is more than 10% below forecast", "the median move reverted at the next shop" or "the median move followed our own change three days earlier". It also records a conflict whenever the plan moves against the direction of the news. Its output is labeled as scripted on the page and in the logs, and it's never cached. It doubles as a benchmark arm, because a rule-based investigator is the fairest test of whether the language model adds anything.

### Diagram

Every part of this diagram is described above. The numbered sentences underneath repeat it in words.

```
 [1] FOUR FEEDS, read through sources.py as of the decision time
     bookings · competitor rates · flight schedule · events
            │
            ▼
 [2] detect.py ─── flags: runs of nights with causes
            │
            ▼
 [3] plan.py ─── a plan for each flag, priced by contribution
            │        under $250 over holding → held by code
            ▼
 ┌─ PROPOSED V2 ─────────────────────────────────────────────────────────┐
 │ [4] gates (code): feeds complete? plan valid? inside 90 nights?       │
 │            │ fail → hold, reason recorded                             │
 │            ▼ pass                                                     │
 │ [5] INVESTIGATOR (language model)                                     │
 │       ──tool call──► tools.py ──reads──► sources.py (as of now)       │
 │       ◄──result───── tools.py           up to 4 calls                 │
 │       submit_findings → citations checked by code                     │
 │            │                                                          │
 │            ▼                                                          │
 │ [6] evidence.py (code): verified results │ investigator's findings    │
 │            │            fixed order, one digest                       │
 │            ▼                                                          │
 │ [7] DECIDER behind one interface: Jev │ v1 reviewer │ accept-all      │
 │       → recommend_plan · hold · human_review, with probabilities      │
 │            │                                                          │
 │            ▼                                                          │
 │ [8] final checks (code): evidence minimum met? gates still pass?      │
 │            │ fail → hold, reason recorded                             │
 └────────────┼──────────────────────────────────────────────────────────┘
              ▼
 [9] agent.py ─── a recommended plan applies from the next tick, nights held 7 days
              │
              ▼
 [10] stored.py ─── flags, plans, investigation_steps, packets, dispositions
              │
              ├──► [11] cache and replay: every turn and answer keyed by a digest
              ▼
 [12] demo_data.py → future audit view under each recommendation
```

1. The agent reads the four feeds through the interfaces in `sources.py`, and each read returns only what was known at the decision time.
2. `detect.py` turns the feeds into flags, which are runs of nights where something changed, each with its causes.
3. `plan.py` prices each flag by contribution and holds any plan worth less than $250 more than holding.
4. Code checks the feeds, the plan and the 90-night window, and a failure becomes a hold with its reason.
5. The investigator calls up to four read-only tools, `tools.py` answers each call from the feeds as of the decision time, and code checks every citation in the investigator's findings.
6. `evidence.py` puts the verified tool results and the investigator's labeled findings into one packet in a fixed order.
7. The decider chooses one of three dispositions from the packet. Jev, the v1 reviewer or the accept-all template can fill that role behind the same interface.
8. Code checks that the required evidence is present and that the gates still pass, and a failure becomes a hold.
9. `agent.py` applies a recommended plan from the next tick and holds those nights for seven days, as in v1.
10. `stored.py` writes the flags, the plans, every tool call, every packet and every disposition to tables.
11. The cache stores every investigator turn and every decider answer under a digest, so a replay can rebuild any decision without a model.
12. `demo_data.py` turns the stored record into display text for a future audit view on the demo page.

## How we'll know it works

The simulator knows the truth in every setup it runs, and that's what makes this measurable. The benchmark already scores a reviewer against a perfect reviewer that knows the true elasticity. Version 2 extends that so the investigator and the decider are measured separately.

### Measuring the investigator

The decider stays fixed at the v1 reviewer, and three ways of building the packet are compared.

1. With no investigation, the packet holds only the plan, as v1's request does today.
2. With a fixed packet, code calls all five tools for every plan and puts every result in the packet.
3. With investigation, the language model chooses up to four tools, as designed.

A fourth arm swaps in the scripted investigator for the language model.

### Measuring the decider

The packet stays fixed, with identical packets built once and stored, and four deciders are compared on them.

1. The accept-all template is the control.
2. The v1 language-model reviewer is the incumbent.
3. Jev is the proposal.
4. The perfect reviewer is the ceiling.

### The setups

1. The default setup, where the plans are right. Neither change may lose money here by holding good plans.
2. The wrong elasticity, fixed at 1.0. This is the benchmark's existing hard mode, where Opus recovered 34%.
3. Demand 10% weaker than the agent believes (`--demand-bias 0.9`), where v1's gain fell to +$1,069 a seed.
4. Competitors that react (`--react`), where 427 of 898 comp-median flags followed the hotels' own changes.
5. A stale feed. On the stored route, the test harness deletes a day of bookings rows for one hotel before the agent decides. This adds no simulator mechanics, because the fault lives in the test harness.

### The acceptance cases

Three clearly labeled synthetic cases check the release before any benchmark run. They're proposed acceptance cases for version 2 and aren't additions to the interview demo.

1. Relevant flights with healthy feeds and a favorable plan. The system may recommend the plan, and the record has to cite the flights, the pickup and the sensitivity.
2. Flights that don't cover the plan's nights. The planner already limits each flag to the nights its news affects, so this case is built by hand. The test checks that code drops any finding that cites flights for nights outside the plan, and that the decision doesn't rest on them.
3. A stale booking feed. The gates have to block the plan before any model is called, and the record has to name the missing data.

### The measures

1. The share of the perfect reviewer's margin each arm recovers, as the benchmark reports today.
2. The number of plans recommended that the perfect reviewer would hold, and the number held that it would recommend.
3. The share of plans sent for human review.
4. Repeated-call agreement. Each stored packet goes to each decider five times in fresh calls, and the measure is the share of packets that got the same disposition every time.
5. Evidence correctness, meaning the share of the investigator's citations that pass code's checks, and the number of findings dropped.
6. For Jev only, whether its probabilities are calibrated. The question is whether the dispositions it gives 80% to are right about 80% of the time against the perfect reviewer. That's measured on these cases only, and it's reported as experimental.
7. Tool calls, tokens, dollars and seconds for each decision.
8. In the stale-feed setup, the share of plans the gates blocked, which has to be 100%.

### The rules for shipping

1. The investigation ships only if it recovers more of the perfect reviewer's margin than the no-investigation packet in setups 2, 3 and 4, and loses nothing in setup 1. Letting the model choose its tools ships only if it matches the fixed packet's result at a lower cost, or beats it. If the fixed packet does as well for less, the fixed packet ships. If the scripted investigator matches both, the language model goes back to writing reasons only.
2. Jev replaces the v1 reviewer as decider only if it matches or beats the reviewer's recovered share on identical packets, and it's also more consistent across repeated calls or cheaper and faster. Until then it runs in shadow, which means its disposition is recorded next to the reviewer's and nothing acts on it.
3. Either change can be switched off by its setting, and every v1 result stays reproducible.

## Cost

The v1 benchmark's 7,744 calls cost $85.87, which is about 1.1 cents a call (README). A live seed of v1 costs between $0.08 and $0.20 (README). An investigation takes up to five language-model turns for each plan, which is four tool calls and one `submit_findings`. Each turn resends the conversation so far, so a live seed would cost several times v1's on the handful of plans that reach the models. In the seed-7 daily run that's six plans in 60 days, so the cost stays in cents.

TypeSafe publishes Jev's price as $0.042 for every million input tokens, with output tokens free, and its response time as 70 to 500 milliseconds (TypeSafe's blog post). Those are the company's figures and haven't been checked here. They'd make the decider's cost small next to the investigator's.

A full benchmark rerun at today's scale with the investigator would cost several hundred dollars, so phase 3 starts with five seeds and widens only if the results are close. All of these costs are estimates scaled from v1's, and phases 2 to 4 replace them with measured numbers.

## Risks

1. The investigator may waste calls or loop. The four-call limit and the forced `submit_findings` end every investigation, and every failure becomes a hold.
2. The investigator may cite evidence it didn't get, or invent a figure. Code's citation and figure checks drop those findings and record why.
3. Jev might not suit this decision. Its probabilities haven't been calibrated on hotel pricing, and TypeSafe's claims haven't been checked. The shadow phase and the benchmark exist to find that out before Jev decides anything.
4. Jev is in early access. Access depends on TypeSafe's waitlist, and the service could change. The decider interface keeps it replaceable, and the v1 reviewer stays available as the decider at all times.
5. Sending packets to an outside service is a data question. At a real hotel, sending a packet to TypeSafe's API means sending the hotel's booking and pricing data outside its own deployment. The simulator's data is synthetic, so the benchmark has no such issue. A deployment would need the hotel's agreement and TypeSafe's data terms, or a model it could run inside its own environment.
6. Live runs vary in wording. The cache makes a recorded run replay exactly, and the benchmark scores dispositions, which don't depend on wording.
7. The minimum evidence for each cause is a judgment, and it could be wrong. The benchmark measures the system with and without the minimum.
8. Version 2 reads only text that code wrote. That means hidden instructions in outside text can't reach it. Phase 5 changes that, so its design has to treat outside text as data and never as instructions.

## Phases

Each phase ends with a decision about whether to go on.

1. Phase 0 is the code fixes. It covers the own-change rule for FRK-09, the two-shop persistence rule and the sensitivity lines in the v1 request, each measured on the existing benchmark. The work goes on only if the findings still leave a gap.
2. Phase 1 works offline. It builds the gates, the five tools, `submit_findings`, the evidence packet, the final checks, the scripted investigator, the accept-all decider, the new tables and the tests, all without an API key. It's done when the stale-feed setup blocks every plan, every tool refuses a later moment, and replay rebuilds every decision.
3. Phase 2 makes the investigator live. It adds the language-model client with tool calls, the cache and the audit, with the v1 reviewer as decider and seed 7 recorded on the daily and four-tick clocks. It's done when the recorded runs pass the audit and replay without a key.
4. Phase 3 is the measurement. It runs the investigator arms and the decider arms in the five setups and applies the rules for shipping.
5. Phase 4 runs Jev in shadow. Once early access is granted, Jev decides on the stored packets beside the v1 reviewer, nothing acts on its dispositions, and the decider measures are reported. It replaces the reviewer only under rule 2 for shipping.
6. Phase 5 comes later, as a separate design. In it the investigator learns to read unstructured news, such as an events listing or a group request, and turns it into a structured event that code validates and prices. That's where letting a model choose what to read is most likely to pay off, and it needs its own design for treating outside text as data.

## Open questions

1. Should a competitor move that follows our own change count as a flag cause at all? This is FRK-09, and phase 0 measures one answer.
2. How should `human_review` be scored? This design counts it as a hold for the money and reports it separately, and the results may suggest a better rule.
3. Should plans held by code for being worth less than $250 also be investigated? This design says no, to keep the cost bounded.
4. What should Jev's state contain? This design sends the whole packet as JSON. A smaller state with only the verified part may decide better, and the benchmark can compare the two.
5. At a real hotel, `human_review` would go to the central revenue team's queue. The design for that queue, and for writing to an RMS, is separate and isn't in this repository.

## Words in this document

- **Feed.** One of the four kinds of data the agent reads, which are bookings, competitor rates, the flight schedule and events. Each one arrives on a schedule.
- **Tick.** One of the moments in a day when the feeds are read and the agent runs. The default is one a day, and `--ticks 4` makes it four.
- **As of.** The rule that every read returns only what was known at a given day and tick.
- **Flag.** A run of consecutive nights that `detect.py` marked because something changed, together with its causes.
- **Pace.** How many rooms an ordinary version of a night would have booked by this point. "Ahead of pace" and "behind pace" compare the rooms actually booked with it.
- **Pickup.** The rooms booked over a recent period, such as the last 3 or 7 days.
- **Comp median.** The middle of the four competitors' prices for a night. The rate shop is the service that reports those prices every day.
- **Plan.** The best option for each day of the week in a flag. `plan.py` chooses it from holding, +5%, +10%, −5% and, after a drop in the comp median, halfway down to it.
- **Contribution.** Room revenue minus the cost of servicing each room sold. The plans are scored on it.
- **Value at stake.** How much more a plan is expected to earn than holding the current rate.
- **Hold.** Keeping the current rate. Code holds a plan worth less than $250 or one that fails a check, and a decider can choose to hold.
- **Elasticity.** How strongly guests react to price. The simulator uses 1.5, and the benchmark gives the agent a wrong value on purpose.
- **Demand bias.** A setting that makes the simulator's demand weaker or stronger than the agent believes, such as 0.9 for 10% weaker.
- **Reaction.** A setting that makes competitors follow half of a hotel's price change three days later.
- **Gate.** A check run by code before any model call. A plan that fails one is held.
- **Investigator.** The language model in version 2 that chooses tools and writes findings. It can't choose a disposition.
- **Tool.** A read-only function in `tools.py` that the investigator can ask code to run. It returns text and numbers that code computed.
- **Finding.** A sentence the investigator writes about one question, citing the tool result it relies on.
- **Evidence packet.** The record code assembles for each plan, with verified tool results in one part and the investigator's labeled findings in another, in a fixed order.
- **Decider.** The component that reads the evidence packet and chooses a disposition. Jev, the v1 reviewer and the accept-all template can each fill the role.
- **Disposition.** The decider's choice, which is `recommend_plan`, `hold` or `human_review`.
- **Human review.** A disposition that sends the plan to a person with a question before anything changes. In the simulator it counts as a hold.
- **Jev.** TypeSafe's first public System One model. TypeSafe describes it as taking a state and returning typed choices with probabilities.
- **System One model.** TypeSafe's name for a model built to return fast, structured decisions instead of generated text.
- **Shadow.** Running a component so that its choices are recorded and compared, while nothing acts on them.
- **Repeated-call agreement.** The share of identical packets that get the same disposition every time they're sent to a decider in fresh calls.
- **Calibration.** Whether a decider's stated probabilities match how often it's right. For example, choices given 80% should be right about 80% of the time.
- **Perfect reviewer.** The benchmark's oracle, which knows the true elasticity and decides each plan correctly. Every arm is scored against it.
- **Recovered share.** How much of the perfect reviewer's margin over saying yes to everything an arm recovers.
- **Fixed packet.** A benchmark arm where code always runs every tool and the investigator isn't used.
- **Scripted investigator.** A rule-based stand-in for the investigator that works offline. Its output is labeled and never cached, like the template in v1.
- **Digest.** A short fingerprint of a request, a conversation or a packet. The cache uses it to refuse an answer to a different question.
- **Replay.** Rebuilding a past day's decisions from the stored tables and the cache without calling a model.
