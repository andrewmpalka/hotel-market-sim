# Knowledge graph

A map of this repository for agents. Read it before you open source files. It tells you where things are and why they are that way. Several agents working at once then share the same picture. It describes this
repository only. Every node is a few lines of plain facts, and the map is
small enough to read whole.

Start with `index.md`, which lists every node on one line. Follow the links
to the nodes you need. The files are:

| File           | Holds                                                                  |
| -------------- | ---------------------------------------------------------------------- |
| `index.md`     | every node on one line, and each file's node and word counts; written by `kg_check.py` |
| `modules.md`   | MOD nodes: one per source file                                         |
| `data.md`      | DAT nodes: the data structures that pass between modules               |
| `rules.md`     | RUL nodes: the three project rules and every named constant            |
| `shocks.md`    | SHK nodes: the four shocks and the days they become known              |
| `concepts.md`  | CON nodes: the ideas the code is built on, with what implements them   |
| `measures.md`  | MEA nodes: the numbers a run is judged by, with formula and function   |
| `sources.md`   | SRC nodes: the data feeds, what stands in for each, what a real one is |
| `decisions.md` | DEC nodes: the design decisions, with what they replaced and why       |
| `results.md`   | RES nodes: the experiments, with their commands and headline figures   |
| `forks.md`     | FRK nodes: open choices, and the choices that were closed              |
| `unknowns.md`  | UNK nodes: what is not known, each with a labelled best guess          |

## IDs

Every node has an ID made of a prefix and a number, such as `MOD-06`. IDs are stable. Once given, an ID always means the same node. An ID is never reused, even after its node is retired. New nodes take the next free number.

| Prefix | Node                                |
| ------ | ----------------------------------- |
| MOD    | a source file                       |
| DAT    | a data structure                    |
| RUL    | a rule or a named constant          |
| SHK    | a shock                             |
| CON    | a concept                           |
| MEA    | a measure                           |
| SRC    | a data source                       |
| DEC    | a design decision                   |
| RES    | an experiment and its result        |
| FRK    | a fork: a choice, open or closed    |
| UNK    | an unknown                          |

## Status tags

Every node carries one tag after its ID.

| Tag | Meaning                                                          |
| --- | ---------------------------------------------------------------- |
| [C] | current and confirmed by a test, or a policy a person reviewed   |
| [T] | a decided target that is not built yet                           |
| [P] | in progress                                                      |
| [O] | open: a choice not yet made, or a recorded result no test pins   |
| [U] | unknown                                                          |
| [H] | historical: replaced, closed or moved                            |

## Style rule

Every node is written in Simplified Technical English. Each field line holds
one fact. No sentence is longer than 20 words. Sentences use the active voice and the present tense. An [H] node describes the design it records in the past tense. A field line is at most 240 characters, and a node has at
most 8 fields. `kg_check.py` enforces the two limits. A field key starts with a capital letter and holds letters, spaces and brackets only. Otherwise the checker cannot read the line.

## Evidence rule

A node marked [C] cites its evidence on its `Evidence:` line. The line holds the names of the tests in `tests/` that confirm it, separated by commas. It holds nothing else.
Each cited test fails when the claim is false. A constant's node cites the
test that confirms what the constant means, and `kg_check.py` confirms its
value against the code. A claim that no test can confirm, such as a rule the owner chose, is a policy node. It carries `Kind: policy` and the line `Evidence: review`. The checker accepts `review` only there. Any other
claim with no test is [O] or [U], never [C].

A node marked [H] needs no evidence beyond the line that links to its successor. That line is `Replaced by:` for a replaced design or `Closed by:` for a closed fork or unknown. It is `Moved to:` for a constant that moved to another file.

A RES node is [C] when a test pins at least one of its figures and [O] when
none does. Its `Table:` line names, in double quotes, the start of its table's caption in `docs/results.md`. The checker looks the caption up.

A `Commit:` line names the commit a decision landed in. The checker does not treat it as evidence, because this repository's history may be recreated. When the git history is present, `kg_check.py` looks each commit up. It reports a miss as a warning and never as a failure.

## Upkeep rule

A change to the code and the change to its nodes go in the same commit. If a constant moves, its RUL node moves with it. If a decision is reversed, the old DEC node becomes [H] and the new one links to it. If a run is repeated, its RES node changes with it. After adding or changing a node, run
`python kg_check.py --write-index` to rewrite `index.md`. The index opens with a table of each file's node and word counts, and the index itself may not pass 3,000 words.

`python kg_check.py` and `tests/test_kg.py` fail when the graph and the code disagree on what the check covers: the constants, the links, the cited test names and the shocks' known days, as the list below says. A fact outside the list, such as a stale sentence, is not caught. They report:

- a link to a node that does not exist,
- a source file with no MOD node,
- a [C] node that cites no test or cites something that is not a test,
- a `review` evidence line outside a policy node,
- a cited test that does not exist,
- an [H] node with no successor,
- a constant whose value or kind here differs from the code,
- a constant in the code with no node here,
- a measure whose function does not exist,
- an Event, a RateCut or a scenario's Shock in the code with no SHK node naming its known day,
- a RES node whose table is not in `docs/results.md`,
- a field line over 240 characters,
- a node with more than 8 fields,
- a decision outside the two groups,
- an `index.md` that differs from the generated one,
- an `index.md` over 3,000 words.

## Links

A link to another node is its ID in double brackets: [[MOD-06]]. Links may
appear anywhere in a node.

## Node format

A node is a level-three heading followed by one bulleted field per line:

```
### MOD-06 [C] bookings.py
- File: src/hotel_market/bookings.py
- Owns: ...
- Reads: [[MOD-04]], [[MOD-05]]
- Writes: [[DAT-07]]
- Tests: tests/test_bookings.py
- Evidence: test_same_seed_gives_the_same_books_and_another_seed_does_not
```

`File:` names the source file for MOD, DAT and RUL nodes. A RUL node for a constant also has `Value:` and `Kind:`. `Value:` is written as Python, such as `1.5`, `"hold"`, `1 / 3` or `date(2027, 1, 4)`. `kg_check.py` compares it with the code. `Kind:` is `parameter` when the value changes the results and `label` when it is a name or a string. A MEA node has `Formula:` and `Function:`, the
dotted name of the function that computes it, which `kg_check.py` resolves. A
SRC node labels every statement about a real feed as an assumption. A RES
node has `Ran:` with its command, `Result:` with its headline figures and
`Table:` with its caption in `docs/results.md`. A DEC node keeps at most one headline figure, on a `Measured:` line. It links to its RES node for the rest.

`decisions.md` has two `##` sections, "Market and agent design" and "Engineering". Every DEC node sits under one of them, and the index groups the decisions the same way. In the index, the parameters of `rules.md` are listed one per line. The labels are listed together on one line of IDs.
