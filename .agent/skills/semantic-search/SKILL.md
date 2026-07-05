---
name: semantic-search
description: "AI embedding-based conceptual code search. Find code by meaning (e.g., 'how is auth handled?') instead of keywords."
---



## When to Activate

- AI embedding-based conceptual code search. Find code by meaning (e.g., 'how is auth handled?') instead of keywords.
- Working on search-related tasks
- Need guidance on: Best Practices

# Semantic Search Skill

> This skill extracts the "meaning" of code using AI embeddings, allowing for conceptual search (e.g., "how is auth handled?") instead of just keyword matching.

## Principles

1. **Local First**: Embeddings should be generated locally (using `transformers.js` or `ollama`) to ensure privacy and offline speed.
2. **Contextual Awareness**: Use `repomap.py` to identify important files to index first.
3. **Hybrid Search**: Combine semantic search with keyword search for maximum precision.

## Tools

### semantic_search(query)
- **Input**: Natural language query.
- **Output**: Top 5 relevant code snippets across the repository.

### semantic_index_update()
- **Action**: Triggers a re-scan of the codebase and updates the local embedding vector store.

## Best Practices

- Always run `semantic_index_update` after significant architectural changes.
- Use semantic search when you don't know the exact names of functions or classes.
- Combine with `vfs` to narrow down the search space.
