Relational Algebra Query (RAQ) Processor
=======================================

A tiny Python CLI that reads relation definitions and relational algebra (RA) queries, executes them, and prints the results.

Quick Start
- Run the test file: `python3 main.py examples/test.txt`
- Start interactive shell: `python3 main.py --repl examples/test.txt`
- Run with a file: `python3 main.py examples/sample.txt`
- Or pipe input: `python3 main.py < examples/sample.txt`

Input Format
1) Define relations

```
Employees (EID, Name, Age) = {
  E1, John, 32
  E2, Alice, 28
  E3, Bob, 29
}

Departments (Dept, Manager) = {
  Sales, Carol
  HR, Dana
}
```

- Attribute names are identifiers.
- Values may be bare tokens, quoted strings, ints, or floats. If a value has spaces/commas, quote it (e.g., "New York").

2) Add one-line queries (each starts with `Query:`)

```
Query: select Age > 30 (Employees)
Query: π Name (σ Age > 28 (Employees))
Query: Employees ∪ Employees
```

Supported Operations
- Selection: `σ predicate (Expr)` or `select predicate (Expr)`
- Projection: `π a,b,c (Expr)` or `project a,b,c (Expr)`
- Join:
  - Natural: `join(Expr, Expr)` or `Expr ⋈ Expr` (merges shared attributes)
  - Theta: `join [predicate] (Expr, Expr)`, `join(Expr, Expr, predicate)`, or `Expr ⋈[predicate] Expr`
- Set operations: `union(Expr, Expr)`, `intersect(Expr, Expr)`, `minus(Expr, Expr)`
  - Infix (set level): `∪`/`⋃`, `∩`, `−`/`-`

Predicates
- Comparisons: `=`, `==`, `!=`, `<`, `<=`, `>`, `>=`
- Boolean: `and`, `or`, `not` (also `∧`, `∨`, `¬`, `&&`, `||`)
- Attribute refs in joins: `left.Age`, `right.Age`, or unqualified `Age` when unambiguous. `Rel.Attr` also works inside joins.
