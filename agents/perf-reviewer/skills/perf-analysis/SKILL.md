---
name: perf-analysis
description: Performance review skill. Detects slow algorithms (O(n²)), N+1 DB query patterns, regex in loops, blocking calls in async context, and inefficient memory usages.
---

# Performance Analysis Skill

## Step 1: Find Hot Paths
- API endpoint handlers (high traffic)
- Database access functions
- Data transformation loops
- Functions called in loops

## Step 2: Complexity Check
- Single loop = O(n) — OK
- Nested loops = O(n²) — FLAG if n > 100 possible
- Loop with .find()/.filter()/.where() inside = O(n²) — ALWAYS FLAG
- Recursive without memoization = check depth

## Step 3: N+1 Pattern (most common issue)
BAD — N+1 queries:
  for user in users:
      orders = Order.objects.filter(user=user)  # 1 query per user!

GOOD — prefetch:
  users = User.objects.prefetch_related('orders').all()

## Step 4: Memory Patterns
- Large list() where iter() would work
- .copy() of huge objects unnecessarily
- Objects created fresh in every loop iteration that could be cached
