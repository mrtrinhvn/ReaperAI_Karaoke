# Performance Review Specialist Checklist

> Scope: Khi diff chứa database queries, API endpoints, frontend rendering, hoặc loop logic.
> Output: Structured findings với severity, confidence, path, category, summary, fix.

---

## Categories

### N+1 Queries
- ORM associations traversed in loops without eager loading
- Database queries inside iteration blocks that could be batched
- Nested serializers that trigger lazy-loaded associations

### Missing Database Indexes
- New WHERE clauses on columns without indexes
- New ORDER BY on non-indexed columns
- Composite queries without composite indexes
- Foreign key columns added without indexes

### Algorithmic Complexity
- O(n²) patterns: nested loops, Array.find inside Array.map
- Repeated linear searches that could use Map/Set lookup
- String concatenation in loops (use join or StringBuilder)
- Sorting/filtering large collections multiple times

### Bundle Size Impact (Frontend)
- Heavy dependencies (moment.js, lodash full, jquery)
- Barrel imports instead of deep imports
- Large static assets without optimization
- Missing code splitting for route-level chunks

### Rendering Performance (Frontend)
- Fetch waterfalls: sequential API calls that could be parallel
- Unnecessary re-renders from unstable references
- Missing React.memo/useMemo on expensive computations
- Layout thrashing from DOM read/write in loops
- Missing loading="lazy" on below-fold images

### Missing Pagination
- List endpoints returning unbounded results
- Database queries without LIMIT
- API responses embedding full nested objects

### Blocking in Async Contexts
- Synchronous I/O inside async functions
- sleep/Thread.sleep inside event-loop handlers
- CPU-intensive computation blocking main thread
