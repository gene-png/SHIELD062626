# SHIELD principles: keeping client-visible claims true

_Created 2026-08-06. Owner: David Catarious. Companion to `CLAUDE.md`, which carries
the six engineering non-negotiables and the environment facts. This file covers the
one thing those six did not: what a deliverable is allowed to say. It is the standing
contract that `ROADMAP.md` sequences work against._

## Why this file exists

Sprint 10 spent twelve sprints making deliverables defensible. Its own closing audit
found five client-facing false statements still shipping, and the flagship CSF
playbook artifacts had never been reached by the fix at all. Every one of those five
passed every test it had.

That is the gap. The six principles in `CLAUDE.md` govern how code behaves. None of
them governs what a rendered sentence asserts, so a report could be built entirely
from correct code and still tell a client something untrue. Sprint 10's own lesson
put it precisely: a truthful report can faithfully describe a gap that a silent
failure created.

The four principles below close that gap, and the two mechanisms after them are how
we check rather than hope.

## The claim principles

### C1. A deliverable asserts only what its input supports.

The unit of honesty is the sentence a client reads, not the function that computed
it. Before writing any exporter prose, name the input condition that makes the
sentence true. If the sentence would survive an input that makes it false, it is the
wrong sentence.

The recurring failure has one shape: a count of zero standing in for two different
facts. Zero gaps because every target was met, and zero gaps because no target was
ever recorded, are the same number and opposite findings. Five separate instances of
this shipped in one batch.

### C2. Absent is not zero, and "no target" is not "target met".

Where a value can be unrecorded, the deliverable says so in the words, not by
printing a dash in a cell the summary line then contradicts. Three of four services
printed something untrue when rendered from an empty assessment: tech debt asserted
`Total annual cost: $0` where the cost was unrecorded, CSF headlined a maturity tier
at 2.8% coverage, and ZT reported no gaps at target having scored nothing.

Zero Trust already carries the correct treatment as of Sprint 10 S4. Copying it is
the job. Deciding it again is not.

### C3. Every client-visible claim is inventoried, with the condition that makes it true.

An assertion nobody wrote down is an assertion nobody can check. The inventory is the
list; C4's render test is the check. Adding a sentence to an exporter means adding
its row.

### C4. Every exporter renders from nothing, in a committed test.

The empty-input render is the cheapest way to find a false reassurance, and it is the
check that would have caught H1 directly. A report built for a fully scored
assessment is correct for the only input it was ever given. Render it from nothing
and read what it says.

## The two mechanisms

Both are gates. Neither is advisory.

### M1. The frozen claim inventory

**Where:** `apps/api/app/claims.py` (the inventory) and
`tests/unit/test_claim_inventory.py` (the gate).

One committed row per client-visible assertion across the six exporters: the exact
string, the module that emits it, and the input condition under which it is true. The
test renders each condition and asserts the claim appears under it and stays absent
otherwise.

The inventory is frozen in the sense that matters: a row is edited only alongside the
prose it describes, in the same commit, and a claim with no row fails the gate.
Deleting a row to make a test pass is the failure mode this exists to prevent, so a
removed row needs the sentence removed too.

This is the primitive that would have caught H1, H5 and the ATT&CK
`Overall coverage: 100.0%` on one scored technique of 633.

### M2. The empty-input render test, per exporter

**Where:** one test per exporter module, beside its existing content tests.

Render the deliverable from an assessment with nothing scored, nothing targeted and
no evidence, then assert on the text. The assertion is not "it did not raise". The
assertion names the false claims that must be absent and the honest ones that must be
present.

`test_playbook_export_content.py` carries the first worked example, added with the H1
fix: rows with no targets recorded, four renderers, and a counterexample proving the
reassuring sentence still appears when every target genuinely is met. A test that
only deletes a claim is weaker than one that also proves the claim survives where it
is true.

## Guidelines for the work that closes this project

**Fix the class, never the instance.** Sprint 10 S0 existed to sweep phantom Tailwind
utilities and swept only the one instance a grep already knew about. Two more
survived, and the third was found by a systematic sweep of all 55 colour utilities
months later. A fix that cannot be expressed as a check does not stop the next one.

**An evidence command that passes before the work begins certifies nothing.** Nine of
Sprint 10's eleven executed sprints had at least one defective acceptance criterion.
Write the criterion so it is red on the tree you are starting from, then confirm it is
red before trusting it.

**A claim change on a client deliverable is a decision, not a scrub.** D-035 set that
precedent. Prose passes tighten words; they never widen or narrow what the document
asserts. Anything that changes the assertion gets a D-number.

**Prove it against the served artifact.** A token proven by reading the config is not
proven. A claim proven by reading the exporter source is not proven. Read the served
stylesheet, extract the real PDF bytes, open the real workbook.

**Grep prose with a multiline search.** Python splits strings across adjacent
literals, so `"...read as " "verified..."` never matches `read as verified` on one
line. Nine protected honesty strings were once reported missing on exactly this.

## Considered and not adopted

Recorded so neither gets rediscovered as an oversight.

**An external golden set for the existing engines.** Cloud Mod's pattern: a fixed set
of cases with externally derived expected labels, where a miss means correct the
engine and never the label. Strong, and it makes "AI suggests, code computes"
measurable rather than asserted. Not adopted for SHIELD's four current engines,
because their scoring is already proven by zero-line diffs and unit coverage, and the
failures we actually shipped were in prose rather than in arithmetic. It arrives
anyway with the Cloud Mod port, where it is the acceptance oracle for the port itself.

**Contract tests at the AI, engine and exporter seams.** Worth having, ranked below
M1 and M2 because the redacting egress client already has a single choke point and
the prompts carry zero-line diffs. Revisit if a seam starts drifting.
