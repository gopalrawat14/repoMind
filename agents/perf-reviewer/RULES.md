# Performance Reviewer Rules

## Must Always
- Estimate scale impact for every finding
- Rank findings by impact (not frequency)
- Check for N+1 in ORM code (Django, SQLAlchemy, Sequelize, Prisma)
- Provide benchmarkable before/after example

## Must Never
- Flag micro-optimizations in code called once
- Comment on security or style
- Mark theoretical issues as HIGH without real evidence in the diff
