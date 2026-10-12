# Knowledge graph

A map of this repository for agents: read it before opening source files, so
that you know where things are and why they are that way, and so that several
agents working at once share the same picture. It describes this repository
only. Every node is a few lines of text; the map is small enough to read
whole.

Start with `index.md`, which lists every node on one line. Follow the links
to the nodes you need. The files are:

| File           | Holds                                                                  |
| -------------- | ---------------------------------------------------------------------- |
| `index.md`     | every node: ID, status, name and file; written by `kg_check.py`        |
| `modules.md`   | MOD nodes: one per source file                                         |
| `data.md`      | DAT nodes: the data structures that pass between modules               |
| `rules.md`     | RUL nodes: the three project rules and every named constant            |
| `shocks.md`    | SHK nodes: the four shocks and the days they become known              |
| `concepts.md`  | CON nodes: the ideas the code is built on, with what implements them   |
| `measures.md`  | MEA nodes: the numbers a run is judged by, with formula and function   |
| `sources.md`   | SRC nodes: the data feeds, what stands in for each, what a real one is |
| `decisions.md` | DEC nodes: the design decisions, with what they replaced and why       |
| `forks.md`     | FRK nodes: open choices nobody has made yet                            |
| `unknowns.md`  | UNK nodes: what is not known, each with a labelled best guess          |

## IDs

Every node has an ID made of a prefix and a number, such as `MOD-06`. IDs
are stable: once given, an ID always means the same node, and an ID is never
reused, even after its node is retired. New nodes take the next free number.

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
| FRK    | an open fork: a choice not yet made |
| UNK    | an unknown                          |

## Status tags

Every node carries one tag after its ID.

| Tag | Meaning                                            |
| --- | -------------------------------------------------- |
| [C] | current and confirmed by evidence                  |
| [T] | a decided target that is not built yet             |
| [P] | in progress                                        |
| [O] | open: a choice or a claim nobody has settled       |
| [U] | unknown                                            |
| [H] | historical: a design that was built, then replaced |

## Evidence rule

A node marked [C] cites its evidence on its `Evidence:` line: the names of
the tests in `tests/` that confirm it, separated by commas, and nothing else.
A claim with no test is [O] or [U], never [C]. A node marked [H] needs no
evidence beyond a `Replaced by:` line linking to the node that replaced it.

A `Commit:` line names the commit a decision landed in. It is information,
not evidence, because this repository's history may be recreated: when the
git history is present, `kg_check.py` looks each commit up and reports a
miss as a warning, never a failure.

## Upkeep rule

A change to the code and the change to its nodes go in the same commit. If a
constant moves, its RUL node moves with it; if a decision is reversed, the old
DEC node becomes [H] and the new one links to it. After adding or changing a
node, run `python kg_check.py --write-index` to rewrite `index.md`.

`python kg_check.py` and `tests/test_kg.py` fail when the graph and the code
disagree: a link to a node that does not exist, a source file with no MOD
node, a [C] node that cites no test or cites something that is not a test, a
cited test that does not exist, an [H] node with no replacement, a constant
whose value or kind here differs from the code, a constant in the code with
no node here, a measure whose function does not exist, a decision outside the
two groups, or an `index.md` that differs from the generated one.

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

`File:` names the source file for MOD, DAT and RUL nodes. A RUL node for a
constant also has `Value:`, written as Python (`1.5`, `"hold"`, `1 / 3`,
`date(2027, 1, 4)`), which `kg_check.py` compares with the code, and
`Kind:`, which is `parameter` when the value changes the results or `label`
when it is a name or a string. A MEA node has `Formula:` and `Function:`, the
dotted name of the function that computes it, which `kg_check.py` resolves. A
SRC node labels every statement about a real feed as an assumption.

`decisions.md` has two `##` sections, "Market and agent design" and
"Engineering"; every DEC node sits under one of them, and the index groups the
decisions the same way. In the index, the parameters of `rules.md` are listed
one per line and the labels together on one line of IDs.
