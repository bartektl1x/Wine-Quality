---
name: repo-principal-review
description: >
  Repo-specific engineering review skill for Databricks/Python production code.
  Optimizes for simple, explicit, class-based designs that read top-down like a book,
  use platform guarantees instead of duplicating defensive logic, and are ready for
  Principal Engineer PR review.
---

# Repo Principal Review Skill

## Purpose

Use this skill when designing, reviewing, refactoring, or approving production code in this repository.

The goal is not maximum generality or theoretical robustness.

The goal is:

> The simplest production-quality implementation that is correct under the real business, domain, and platform contracts, is easy to read top-down, and can be defended in a Principal Engineer PR review.

This skill is deliberately biased against AI overengineering.

---

# 1. Core engineering philosophy

Before changing code, establish:

1. What must this component do?
2. What does it explicitly NOT need to support?
3. What invariants are already guaranteed upstream?
4. What invariants are guaranteed by the platform?
5. What failures are acceptable?
6. What failures are dangerous?
7. Which class owns each validation or responsibility?

Never start with:

> How can I make this implementation more robust?

Start with:

> What is the minimum correct implementation under the actual contract?

Complexity must be justified by a supported scenario.

---

# 2. Read-like-a-book style

Code should read top-down.

A public method should behave like a table of contents.

Preferred shape:

```python
def generate_retention_config(...):
    rules = self._read_retention_rules(...)
    self._validate_retention_targets(rules)
    rules = self._inherit_retention_rules(rules)
    return rules
```

Physical method ordering should normally follow the call hierarchy:

```text
public_method

_first_chapter
    _first_subchapter
        _leaf_detail
    _second_subchapter

_second_chapter
    _subchapter

_final_chapter
```

If `_read_lineage()` calls `_read_current_mappings()`, the implementation of `_read_current_mappings()` should normally appear immediately after `_read_lineage()` or within that chapter before unrelated methods.

Avoid organizing methods merely as:

```text
all public methods
all orchestration methods
all helpers
all utilities
```

when that forces the reader to jump around the file.

The reader should be able to keep scrolling downward.

---

# 3. Method decomposition rule

Do not split methods based on line count alone.

For every substantial method classify it as:

```text
KEEP WHOLE
EXTRACT ONE MEANINGFUL SUBCHAPTER
SPLIT — MULTIPLE RESPONSIBILITIES
MERGE — HELPER IS TOO TRIVIAL
```

A helper is justified when it:

- represents a meaningful domain/algorithmic chapter,
- hides a representation boundary that interrupts the parent story,
- isolates infrastructure mechanics from domain logic,
- or owns an independently meaningful validation step.

Good extraction:

```text
_collect_reachable_lineage
    ↓
_read_frontier_mappings
```

because graph traversal and Spark acquisition mechanics are different abstraction levels.

Bad extraction:

```text
_process_mapping
_register_edge
_update_frontier
_prepare_next_source
_handle_candidate
```

when each merely relocates a few obvious lines.

A coherent 25–40 line algorithm can be better than six tiny methods.

Do not optimize for the number of methods.

Optimize for comprehension.

---

# 4. Single Responsibility Principle

Apply SRP using **reasons to change**, not line count.

Ask:

> What event would cause this code to change?

Examples:

```text
Databricks changes system-table semantics
```

and:

```text
Business changes ambiguity rules
```

are different reasons to change.

That may justify a boundary.

But do not automatically create:

```text
Repository
Service
Manager
Provider
Strategy
Factory
Helper
```

because a class is long.

Split only when there is a real responsibility boundary.

---

# 5. Platform guarantees should delete code

Do not defend locally against states already prohibited by the surrounding system.

Examples:

```text
Platform guarantees a DAG
```

→ do not implement generic cycle recovery.

```text
Input reader guarantees non-empty rules
```

→ downstream classes should not add `if not rules` branches or duplicate validation unless empty input is intentionally part of their own public contract.

```text
Reader guarantees unique targets
```

→ resolver/validator/generator should not revalidate uniqueness merely “for safety”.

A platform guarantee should remove complexity.

It should not be documented while the defensive code remains.

---

# 6. Validation ownership

Every validation should have one clear owner.

Preferred pattern:

```text
Input reader
    → input/workbook/file-specific validation

Pydantic domain model
    → local domain invariants

Target validator
    → external system compatibility / existence

Inheritance resolver
    → inheritance semantics only

Generator
    → orchestration and destination contract
```

Do not validate the same invariant in every layer.

If upstream has already established the invariant and downstream is not an independently exposed arbitrary-input API, trust it.

---

# 7. Pydantic style

Prefer declarative validation for generic constraints.

Good:

```python
expiration_days: int = Field(ge=0, le=MAX_EXPIRATION_DAYS)
```

Use custom validators for genuinely domain-specific semantics.

Repository conventions:

- Pydantic v2
- minimum supported version >= 2.11
- `strict=True`
- `frozen=True`
- `extra="forbid"`
- `validate_by_name=True`
- `validate_by_alias=True`
- avoid older `populate_by_name=True`
- Python 3.12 `type` aliases are acceptable

Keep domain models small.

Do not place Spark, file-format, or infrastructure concerns in domain models.

---

# 8. Naming style

Prefer names that describe domain intent.

Good:

```text
generate_retention_config
_read_retention_rules
_validate_retention_targets
_read_current_mappings
_collect_reachable_lineage
_resolve_inherited_rules
_create_retention_config_table
```

Be suspicious of vague verbs and generic nouns:

```text
process
handle
execute
build
refresh
manager
helper
data
frame
result
```

A method name should tell the reader why the step exists, not merely what low-level operation it performs.

Avoid `frame` in method names when the domain concept is clearer.

---

# 9. Comments and docstrings

Comments should explain **why**, especially where code intentionally looks redundant or conservative.

Good:

```python
# Collect one extra row to detect budget overflow.
```

Good:

```python
# Select the latest completed update before joining mappings,
# so missing mappings cannot expose an older update.
```

Good:

```python
# Pydantic trimming must not silently select another physical column.
```

Bad:

```python
# Increment the count.
count += 1
```

Docstrings must not overstate behavior.

Prefer precise contracts.

---

# 10. AI overengineering warning signs

Treat these phrases as review triggers:

```text
"For robustness..."
"To future-proof..."
"For completeness..."
"To be safe..."
"In case another producer..."
"To support arbitrary..."
"A generic solution would..."
"Let's add another validation..."
"We could introduce a service/repository/manager..."
```

These are not automatically wrong.

But require a concrete currently supported scenario.

If none exists, reject the complexity.

---

# 11. Complexity escalation kill switch

A common AI failure pattern is:

```text
edge case
→ new state
→ second edge case
→ second pass
→ reconciliation
→ extra metadata
→ safety bound
→ recovery logic
→ more abstractions
```

When this happens, STOP.

Do not add the next mechanism.

Ask:

> Which assumption or business decision could eliminate this entire branch of complexity?

Then challenge the requirement itself.

When a simple feature becomes disproportionately large, treat that as evidence that the problem may have been generalized too far.

---

# 12. Optional enrichment must remain optional

If a feature is explicitly optional enrichment, do not accidentally turn it into a consistency engine.

Example:

```text
explicit configuration = authoritative
lineage inheritance = optional enrichment
```

Then:

```text
missing lineage
ambiguous lineage
unsupported lineage
```

may simply mean:

```text
no derived rule
```

If false negatives are acceptable but false positives are dangerous, prefer conservative omission over historical reconstruction.

Do not recover old state merely to avoid losing enrichment unless the business requires it.

---

# 13. Spark / Databricks review rules

Distinguish Python structure from Spark execution.

DataFrame transformations are lazy.

Splitting transformations into Python methods does not inherently create extra Spark jobs.

But actions matter:

```text
collect
count
write
toPandas
```

Review explicitly:

- driver collection size,
- repeated actions,
- unnecessary scans,
- joins,
- persistence/caching,
- repeated lazy-plan evaluation,
- whether a strict snapshot is actually required,
- whether an optimization targets a realistic workload.

Do not add caching or materialization merely to make a theoretical consistency statement stronger if the business contract does not require it.

---

# 14. Error handling

Choose the business failure contract first.

Then implement only what that contract needs.

If optional enrichment has the contract:

```text
Spark failure while reading optional metadata
    → log
    → continue without enrichment
```

then a broad infrastructure exception boundary may be clearer than a large taxonomy of:

```text
SQLSTATE
missing table
missing schema
missing catalog
message parameters
```

Do not classify errors unless different classifications produce meaningfully different behavior.

Do not swallow non-optional domain failures.

---

# 15. Avoid duplicate defensive branches

Every guard should correspond to a supported state.

Question code like:

```python
if not explicit_rules:
    return explicit_rules
```

when upstream guarantees the input is non-empty.

Ask:

> Is this state part of this method's real contract?

If no, delete the branch.

Do not silently broaden component contracts “just in case”.

Do not replace deleted duplicate validation with another duplicate validation.

---

# 16. Long-method review

When a method looks long, perform this exact review:

### A. State its single sentence responsibility.

If that sentence needs “and” multiple times, it may be mixed.

### B. Identify abstraction levels.

Example smell:

```text
Spark DataFrame construction
+
domain decision
+
graph mutation
+
error translation
```

in one method.

### C. Identify meaningful chapters.

Extract only if a chapter has a useful name and lets the parent read more clearly.

### D. Re-read the parent after extraction.

If understanding now requires jumping through several tiny helpers, undo the extraction.

The objective is not small methods.

The objective is a clear story.

---

# 17. Fresh-eye + context review protocol

For important PRs, review every class in three passes.

## Pass A — Fresh eye

Ignore historical explanations initially.

Ask what a Principal Engineer would question on first read:

- responsibility unclear?
- method unexpectedly long?
- mixed abstraction levels?
- vague names?
- hidden assumptions?
- duplicate validation?
- clever algorithm?
- suspicious abstraction?
- comments compensating for unclear code?

## Pass B — Context-aware

Apply the actual platform/business contracts.

For each concern ask:

> Does the context remove the concern?

Also ask:

> What code is now unnecessary because of these contracts?

## Pass C — Principal-level approval

Evaluate:

- responsibility
- method hierarchy
- abstraction levels
- validation ownership
- names
- comments
- error handling
- Spark behavior
- testability
- coupling
- accidental generality
- unnecessary complexity

Then give exactly one verdict:

```text
APPROVED
APPROVED WITH SMALL CHANGES
NOT READY
```

`APPROVED` means genuinely ready to send to a Principal Engineer.

---

# 18. Class locking rule

Review and lock classes one by one.

Once a class is approved:

> LOCK THIS CLASS.

Do not reopen it merely because another stylistic alternative exists.

Reopen a locked class only if a later component reveals a concrete interface or correctness defect.

This prevents endless AI iteration and design churn.

---

# 19. Final cross-class review

After individual classes are locked, review the whole feature once.

Check:

- dependency direction,
- responsibility boundaries,
- duplicated validation,
- naming consistency,
- orchestration,
- coupling,
- shared assumptions,
- testability,
- whether one class knows too much about another.

Do not redesign individually approved classes unless there is a concrete cross-class problem.

Final verdict:

```text
READY FOR PRINCIPAL REVIEW
```

or:

```text
NOT READY — <specific blockers>
```

---

# 20. Repo-specific preferred design tendencies

Default preferences for this repository:

- class-based design,
- explicit domain models,
- shallow call hierarchy,
- public method as table of contents,
- physical method order follows conceptual call order,
- meaningful helpers rather than tiny helpers,
- no abstraction for abstraction's sake,
- no speculative future-proofing,
- no repeated validation,
- platform guarantees are trusted,
- optional enrichment degrades simply,
- deterministic output where useful,
- one clear owner for each invariant,
- direct, domain-specific names,
- comments explain non-obvious reasoning,
- simple code is preferred over clever code.

---

# 21. Questions the AI must ask itself before proposing changes

Before adding code:

1. What supported scenario needs this?
2. Is this already guaranteed elsewhere?
3. Is this validation already owned by another layer?
4. Does this improve the happy path or only a theoretical edge case?
5. Is the edge case actually supported?
6. Could a documented limitation delete this machinery?
7. Am I solving a general problem instead of the repo's problem?
8. Would a Principal Engineer understand the algorithm faster after this change?
9. Can I delete code instead of extracting it?
10. Am I adding complexity because it sounds "robust"?

Before splitting a method:

1. Is there a real second responsibility?
2. Is there a mixed abstraction level?
3. Does the new helper have a meaningful domain/algorithmic name?
4. Does the parent become easier to read?
5. Will the reader have to jump around more?
6. Would keeping one coherent algorithm together be clearer?

---

# 22. Anti-pattern case study from this repo

A retention-inheritance feature originally needed:

```text
read explicit rules
→ follow trusted downstream lineage
→ inherit when unambiguous
→ explicit rules win
→ missing lineage means no inheritance
```

AI iterations gradually introduced:

```text
historical target reconstruction
table + column lineage reconciliation
producer ownership recovery
timestamp tie handling
cycle handling
fixed-point traversal
rejected-table state
repeated ambiguity tracing
multiple safety budgets
detailed Spark error taxonomy
many helper methods
```

Most additions were individually defensible.

Together they solved a much more general problem than required.

The major simplification came from explicitly trusting the real platform contract:

```text
SDP graph is acyclic
stable pipeline ownership
latest successful update is enough
no historical fallback
false-negative enrichment is acceptable
```

Lesson:

> The best refactor was not a smarter algorithm. It was deleting requirements we never had.

---

# 23. Final quality standard

Good production code should make the normal path obvious.

A Principal Engineer should quickly understand:

```text
what the class owns
what assumptions it relies on
how the happy path flows
where validation belongs
what happens on missing optional data
```

The desired reaction is:

> "Given these contracts, this is the obvious implementation."

Not:

> "This is clever."

For every final review ask:

> If I deleted half of this complexity, which supported scenario would stop working?

If nobody can answer clearly, simplify.
