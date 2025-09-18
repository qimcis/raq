Relational Algebra Query (RAQ) Processor
=======================================

Functionality
- Parse relation definitions: `Name (A, B, ...) = { rows }`
- Run single-line queries: lines starting with `Query:`
- Selection: `σ` and `select` forms
- Projection: `π` and `project` forms
- Joins: natural (`⋈` or `join(A,B)`) and theta (`⋈[pred]`, `join [pred] (A,B)`, `join(A,B,pred)`)
- Set operations: `union`, `intersect`, `minus` and infix `∪/⋃`, `∩`, `−/-`
- Predicates: `=`, `==`, `!=`, `<`, `<=`, `>`, `>=`, boolean `and/or/not` and `∧/∨/¬` and `&&/||`
- Attribute refs: unqualified (`Age`) or qualified in joins (`left.Age`, `right.Age`, `Rel.Attr`)
- Nesting: operations can be nested arbitrarily
- Semantics: set semantics (deduped results); natural join merges shared columns; theta join suffixes duplicate right columns with `_right`
- Set-compatibility: set ops require same attribute names; right side reordered to match left when names match in different order
- Output: prints a relation block and a tab-separated table
- CLI: run `python3 main.py examples/sample.txt` or `python3 main.py < examples/sample.txt`
- No external data-processing libraries used

Cheat Sheet

Definitions
```
Employees (EID, Name, Age) = {
  E1, John, 32
  E2, Alice, 28
}
Departments (Dept, Manager) = {
  Sales, Carol
  HR, Dana
}
EmpDept (EID, Dept) = {
  E1, Sales
  E2, HR
}
```

Selection
```
Query: σ Age > 30 (Employees)
Query: select Age >= 30 (Employees)
Query: σ (Age > 25 and Name = "John") (Employees)
```

Projection
```
Query: π Name,Age (Employees)
Query: project Name (σ Age > 25 (Employees))
```

Natural Join
```
Query: Employees ⋈ EmpDept
Query: join(Employees, EmpDept)
```

Theta Join
```
Query: Employees ⋈[left.EID = right.EID] EmpDept
Query: join [left.EID = right.EID] (Employees, EmpDept)
Query: join(Employees, EmpDept, left.EID = right.EID)
```

Set Operations
```
Query: Employees ∪ Employees
Query: (σ Age > 25 (Employees)) ∩ (σ Age > 25 (Employees))
Query: (σ Age > 25 (Employees)) − (σ Age > 30 (Employees))
Query: union(Employees, Employees)
Query: intersect(Employees, Employees)
Query: minus(Employees, Employees)
```

Predicates & Qualifiers
```
Comparisons: =, ==, !=, <, <=, >, >=
Boolean: and/or/not  (also ∧/∨/¬, &&/||)
Unary: numeric unary minus in predicates, e.g., Age = -1 or -Age < 0
Qualify in joins: left.Age, right.Age, or Rel.Attr
```

Complex Example
```
Query: π Name ( σ (Age >= 28 and (left.EID = right.EID)) ( Employees ⋈[left.EID = right.EID] EmpDept ) )
```

Notes
- Queries must be one line each (`Query:` prefix). No multi-line queries or inline `#` comments.
- Use quotes for values with spaces/commas: "New York".
