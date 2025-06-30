# GET `/api/get_sub_disciplines`

Retrieves sub-disciplines for a given discipline, with different behavior based on user authentication and mode.

## Authentication

**Conditional:** Required for 'user' mode, optional for 'public' mode.

## Query Parameters

```typescript
{
  disciplineName: string,    // Name of the parent discipline (required)
  mode?: string             // 'user' or 'public' (default: 'user')
}
```

## Response

### Success (200)
```typescript
SubDiscipline[] // Array of sub-discipline objects
```

```typescript
{
  id: number,
  name: string
}[]
```

## Usage in Frontend

Used in `ArticleListView.svelte` component to populate sub-discipline filter dropdowns when a main discipline is selected.

**Location:** `src/lib/components/articles/ArticleListView.svelte:162`

## Behavior

The endpoint behavior depends on the mode and authentication status:

### Public Mode or No Authentication
- Returns all sub-disciplines for the specified discipline
- No subscription filtering applied

### User Mode with Authentication
- **No subscriptions for discipline**: Returns empty array
- **Subscribed to main discipline only**: Returns all sub-disciplines for that discipline
- **Subscribed to specific sub-disciplines**: Returns only the subscribed sub-disciplines

## Error Handling

- **400**: Missing required `disciplineName` parameter
- **401**: Authentication required for user mode (returns empty array instead of error)
- **500**: Database error

## Notes

- If the specified discipline doesn't exist, returns an empty array
- The subscription logic ensures users only see sub-disciplines they have access to
- Used primarily for populating filter dropdowns in the article list interface 