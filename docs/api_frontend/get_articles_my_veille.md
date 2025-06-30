# GET `/api/get_articles_my_veille`

Retrieves a paginated list of articles filtered by user's subscription preferences and optional search/discipline filters.

## Authentication

**Optional:** User authentication is not required, but filtering by user subscriptions requires authentication.

## Query Parameters

```typescript
{
  specialty?: string,           // Discipline filter ('__ALL__' for all)
  subDiscipline?: string,       // Sub-discipline filter
  offset?: number,              // Pagination offset (default: 0)
  search?: string,              // Search term for filtering articles
  filterByUserSubs?: boolean    // Whether to filter by user subscriptions
}
```

## Response

### Success (200)
```typescript
{
  data: Article[],  // Array of articles
  error: null
}
```

## Usage in Frontend

Used in `ArticleListView.svelte` component for the "My Watch" functionality that shows articles based on user's subscription preferences.

**Location:** `src/lib/components/articles/ArticleListView.svelte:32`

## Behavior

1. Processes query parameters:
   - Treats empty or `'__ALL__'` specialty as null (show all disciplines)
   - Sets sub-discipline to null if main discipline is null
2. Calls the `get_all_articles_sub_disciplines` RPC function with:
   - Discipline and sub-discipline filters
   - Pagination offset
   - Search term for content filtering
   - User ID (if authenticated)
   - Flag to filter by user subscriptions
3. Returns articles that match the specified criteria

## Error Handling

- **500**: Database RPC error

## Notes

- This endpoint is the main article retrieval endpoint for personalized content
- When `filterByUserSubs` is true and user is authenticated, only articles from subscribed disciplines/sub-disciplines are returned
- The RPC function handles the complex logic of subscription-based filtering while maintaining consistent pagination and search functionality 