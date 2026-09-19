# AI Engineering Anti-Overengineering Skill

Use these instructions when designing, reviewing, or refactoring production software with an AI assistant.

The purpose is to prevent a common AI failure mode:

> Solving a more general, defensive, abstract, and complicated problem than the application actually has.

The primary optimization target is not theoretical robustness.

It is:

> The simplest implementation that is correct under the real platform and business contracts.

---

# 1. Start with the actual contract, not the implementation

Before reviewing code, state:

* What must the feature do?
* What may it deliberately not support?
* What does the surrounding platform already guarantee?
* What failures are acceptable?
* What failures are dangerous?
* What is optional enrichment versus required behavior?

Do not start by asking how to improve the existing implementation.

First ask:

> Why does this implementation exist in this form at all?

---

# 2. Platform guarantees are inputs to the design

Never independently defend against states the platform guarantees cannot occur.

If the platform guarantees:

```text
dependency graph is acyclic
```

do not build generic cycle resolution.

If the platform guarantees:

```text
one pipeline owns one output table
```

do not build historical producer reconciliation.

If the input reader already guarantees:

```text
one explicit rule per table
```

do not validate that invariant again in every downstream component unless the downstream API intentionally supports arbitrary callers.

A platform guarantee should DELETE code.

It should not merely be documented while defensive code remains.

---

# 3. Challenge every safety mechanism

AI-generated code often accumulates checks because every check sounds individually reasonable.

For every check ask:

```text
What concrete failure does this prevent?

Can this failure actually happen under our platform contract?

If it happens, what is the business consequence?

Would simpler failure behavior already be acceptable?
```

Classify every defensive mechanism as:

```text
REQUIRED
USEFUL
REDUNDANT
IMPOSSIBLE UNDER PLATFORM CONTRACT
OVER-CONSERVATIVE
```

Delete the last three unless there is a strong reason not to.

---

# 4. Optional enrichment should stay optional

If a feature is optional enrichment, do not accidentally design it like a mission-critical consistency engine.

Example:

```text
explicit retention rules = required truth
lineage inheritance = optional enrichment
```

Therefore:

```text
missing lineage
→ no inheritance
```

may be perfectly valid.

This is fundamentally different from:

```text
missing lineage
→ reconstruct historical system state
→ search previous versions
→ resolve producer ownership
→ run graph stabilization algorithm
```

Before adding recovery behavior ask:

> Are false negatives acceptable?

If yes, many difficult consistency problems disappear.

---

# 5. Prefer explicit limitations over generic machinery

A small documented limitation is often better than hundreds of lines of generic handling.

Example:

```text
Supported:
one stable Lakeflow pipeline owner per target

Not supported:
automatic interpretation of a target migrating between unrelated pipeline IDs
```

can be much better than implementing a general historical ownership reconciliation system.

Do not make a local feature solve every theoretically possible future scenario.

---

# 6. Do not confuse “more correct” with “more general”

AI frequently interprets correctness as:

```text
works under every imaginable state
```

Production correctness is:

```text
works under the states permitted by the system contract
```

These are not the same thing.

Code that handles impossible states:

* costs maintenance,
* obscures normal behavior,
* adds failure modes,
* becomes harder to test,
* makes reviews harder,
* may itself introduce bugs.

---

# 7. Re-evaluate the requirement when complexity grows

Use complexity as feedback.

If a feature described in one sentence becomes hundreds of lines, stop.

Do NOT immediately refactor those hundreds of lines.

Ask:

> Which requirement caused this complexity?

Then challenge that requirement.

Example from retention inheritance:

Original requirement:

```text
Follow column lineage and inherit a retention rule downstream.
```

Implementation drifted into:

```text
Reconstruct a uniquely current target dependency state across historical,
incomplete lineage observations, multiple possible producers, failed updates,
timestamp ties, cycles, ownership migrations and stale mappings.
```

That is a different problem.

Whenever the implementation becomes disproportionate to the business description, return to first principles.

---

# 8. Read-like-a-book code means hierarchy, not tiny methods

A top-level method should read like a table of contents.

Good:

```python
def generate_retention_config(...):
    rules = self._read_retention_rules(...)
    rules = self._inherit_retention_rules(rules)
    self._validate_retention_targets(rules)
    return rules
```

Then each chapter may expose meaningful subchapters.

Good:

```text
_validate_target_tables
├── _validate_target_tables_exist
└── _validate_target_tables_support_retention
```

Bad:

```text
_process
├── _prepare
│   └── _create
│       └── _transform
│           └── _execute
```

A helper should exist because it represents:

* a meaningful domain chapter,
* an independently understandable subproblem,
* or implementation detail that obscures the parent's story.

Do not extract a method merely because a block is 8 lines long.

---

# 9. Single Responsibility is about reasons to change

Do not apply SRP mechanically based on line count.

Ask:

> What would cause this code to change?

For example:

```text
Databricks changes lineage system tables
```

and:

```text
Business changes ambiguity semantics
```

are different reasons to change.

That can justify separating:

```text
lineage acquisition
```

from:

```text
retention-policy resolution
```

But do not invent:

```text
Repository
Service
Manager
Strategy
Factory
Provider
```

just because a class is long.

---

# 10. Beware of AI “enterprise reflexes”

AI frequently invents abstractions because they resemble enterprise architecture patterns.

Common unnecessary additions include:

* repository layers,
* service layers,
* factories,
* strategies,
* publisher classes,
* generic validators,
* custom exception hierarchies,
* graph frameworks,
* provenance models,
* result wrappers,
* configuration abstractions,
* manually maintained allowlists.

Before accepting one ask:

> What concrete problem does this abstraction solve today?

If the answer is mostly:

```text
separation of concerns
future extensibility
clean architecture
```

without a concrete current reason, reject it.

---

# 11. Beware of defensive-algorithm escalation

A particularly dangerous AI pattern is:

```text
edge case discovered
→ add state
→ new edge case appears
→ add second pass
→ add reconciliation
→ add safety limit
→ add recovery
→ add metadata
→ add another state machine
```

Each change individually seems sensible.

The final architecture may be absurd.

When this happens, do not add another protection.

Ask:

> Which assumption would make this entire branch of complexity unnecessary?

---

# 12. Distinguish required correctness from conservative behavior

For every conservative behavior ask whether it is:

```text
required for correctness
```

or merely:

```text
avoids a theoretical false positive
```

Then evaluate business cost.

For optional enrichment:

```text
false negative
```

may be cheap.

Therefore rejecting an uncertain inherited rule can be much simpler than reconstructing enough historical state to recover it.

---

# 13. Do not silently upgrade the feature's reliability contract

Example:

Business requirement:

```text
If lineage is available, enrich rules.
```

AI implementation:

```text
Determine precisely whether lineage system tables are unavailable due to:
- permissions
- missing table
- missing schema
- missing catalog
- SQL state
- message parameter
- system table name
```

Ask whether all of this changes the business outcome.

If all expected metadata failures mean:

```text
use explicit rules only
```

then detailed exception classification may be unnecessary.

However, do not hide genuine programming errors unless that is intentionally accepted.

Choose the failure contract first.

Then implement only what that contract needs.

---

# 14. Respect lazy execution models

In Spark, creating:

```python
df = spark.table(...)
```

does not necessarily execute the query.

Errors may occur later at:

```python
collect()
count()
write()
```

Therefore do not design exception handling based only on syntactic API calls.

Likewise, splitting a lazy DataFrame transformation into multiple Python methods does not necessarily create additional Spark jobs.

Do not confuse:

```text
Python method decomposition
```

with:

```text
Spark execution boundaries
```

But also do not create dozens of DataFrame helper methods merely because laziness makes it technically cheap.

---

# 15. Names must describe intent, not mechanics

Prefer:

```text
_read_retention_rules
_validate_target_tables
_read_latest_completed_updates
_inherit_rule
```

over:

```text
process
handle
execute
build
refresh
manager
helper
data
result
```

Variables should also tell the algorithmic story.

Prefer:

```text
candidate_rules
ambiguous_tables
inherited_rules
```

over:

```text
possible
reached
state
items
```

---

# 16. SQL complexity is architecture complexity

Do not hide a complicated algorithm inside one SQL string and call the Python method simple.

A method like:

```python
_read_lineage()
```

containing an 80-line SQL reconstruction algorithm is still complex.

CTEs help readability, but they do not eliminate conceptual complexity.

When SQL grows, ask:

> Why does this query need every stage?

For every CTE require:

```text
What exact failure occurs if this stage is removed?
```

If the answer depends on a scenario excluded by platform guarantees, delete the stage.

---

# 17. Do not preserve old complexity after requirements simplify

This is a major AI failure mode.

After changing the contract from:

```text
support arbitrary target ownership migration
```

to:

```text
stable pipeline ownership
```

AI may leave old producer-reconciliation code in place “for safety.”

That defeats the purpose of simplifying the contract.

Whenever an assumption becomes stronger:

> explicitly list which code is now obsolete and remove it.

---

# 18. Avoid duplicate validation across layers

Validation should live at the appropriate boundary.

Example:

```text
Excel reader
→ input format + duplicate explicit policies

Pydantic domain model
→ local domain invariants

Target validator
→ Unity Catalog / Auto-TTL compatibility

Inheritance resolver
→ inheritance semantics
```

Do not have every layer verify every invariant.

Duplicate validation increases code without necessarily increasing safety.

---

# 19. Keep domain models small and declarative

Prefer:

```python
expiration_days: int = Field(ge=0, le=MAX_EXPIRATION_DAYS)
```

over manually implementing generic numeric validation.

Use custom validators for genuinely domain-specific rules.

Avoid putting infrastructure concerns into domain models.

---

# 20. Explicit rules and derived state must remain conceptually separate

Whenever a system has:

```text
user intent
+
derived configuration
```

do not blur them.

Example:

```text
explicit PO retention rules
        ↓
lineage inheritance
        ↓
effective retention configuration
```

Derived rules should not silently become explicit source-of-truth input.

This separation simplifies ownership and debugging.

---

# 21. Ask “what can we delete?” before “what can we extract?”

This is perhaps the most important rule.

When a method is too complex, AI usually asks:

> How can I split this into smaller methods?

Ask first:

> Why does this code exist?

The best refactor may be:

```text
delete 70%
```

not:

```text
split 100% into twelve methods
```

---

# 22. Review protocol for future AI sessions

Before accepting an implementation, require the AI to perform these steps.

## Step 1 — State the business requirement

Maximum a few paragraphs.

## Step 2 — State platform invariants

Explicitly list guarantees supplied by the surrounding platform.

## Step 3 — State deliberate limitations

What does this feature intentionally NOT support?

## Step 4 — Describe the simplest algorithm

No code yet.

If it cannot be explained simply, investigate why.

## Step 5 — Complexity budget

For every substantial piece of logic ask:

```text
Which requirement forces this complexity?
```

## Step 6 — Overengineering audit

Classify existing code:

```text
ESSENTIAL
PLATFORM RESPONSIBILITY
DUPLICATE
DEFENSIVE FOR IMPOSSIBLE STATE
FUTURE-PROOFING
ACCIDENTAL COMPLEXITY
```

Delete aggressively.

## Step 7 — Method hierarchy

Only after algorithm simplification.

Use meaningful chapters.

## Step 8 — Implementation

Write production code.

## Step 9 — Adversarial self-review

Ask:

```text
What did I add that the user never asked for?

What impossible states am I defending against?

What validations are duplicated?

What abstractions exist only for theoretical future extensibility?

What could I delete while preserving the contract?
```

Then simplify again.

---

# 23. AI red flags

When an AI says any of these, investigate carefully:

```text
"For robustness..."
"To future-proof..."
"For completeness..."
"To be safe..."
"In case another producer..."
"To support arbitrary..."
"A generic solution would..."
"We could introduce a manager/service/repository..."
"Let's add another validation layer..."
```

These statements are not automatically wrong.

But they often precede unnecessary complexity.

Demand a concrete current requirement.

---

# 24. Retention inheritance case study — what went wrong

This project is a useful example.

The desired feature was approximately:

```text
Read explicit retention rules.

Use Lakeflow lineage to propagate rules downstream when clear.

Explicit rules win.

If lineage is uncertain, do nothing.
```

The implementation gradually accumulated:

```text
historical target reconstruction
multiple lineage system tables
latest target activity
producer reconciliation
timestamp tie handling
cycle handling
fixed-point traversal
rejected-table state
ambiguous-table state
repeated traversals
Spark error classification
multiple safety budgets
```

Many pieces were locally defensible.

The combined system solved a much more general problem than required.

The turning point was identifying stronger SDP guarantees:

```text
DAG topology
stable pipeline ownership
latest successful update sufficient
no historical fallback required
false-negative inheritance acceptable
```

Those guarantees should eliminate major branches of complexity.

Lesson:

> Better architecture often comes from strengthening and documenting assumptions, not writing smarter algorithms.

---

# 25. Final standard

Production code should make the happy path obvious.

A principal engineer opening the file should first understand:

```text
what this feature does
what assumptions it relies on
what happens when information is missing
```

before encountering implementation mechanics.

The ideal reaction is:

> “Of course it works this way.”

Not:

> “This is clever.”

Cleverness is frequently a warning sign in platform code.

The final question for every review is:

> If I deleted half of this code, which actual supported scenario would stop working?

If nobody can answer clearly, delete it.
