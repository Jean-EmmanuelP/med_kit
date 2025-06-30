# GET `/api/get-liked-articles`

Retrieves a paginated list of articles that the authenticated user has liked, with optional filtering and search capabilities.

## Authentication

**Required:** User must be authenticated with a valid session.

## Query Parameters

```typescript
{
  offset?: number,           // Pagination offset (default: 0)
  search?: string,           // Search term for filtering articles
  specialty?: string,        // Discipline filter ('__ALL__' for all)
  subDiscipline?: string     // Sub-discipline filter
}
```

## Response

### Success (200)
```typescript
{
  data: Article[],  // Array of liked articles
  error: null
}
```

## Usage in Frontend

Used in the favorites page (`/favoris`) and referenced in `ArticleListView.svelte` for liked articles functionality.

**Locations:**
- `src/routes/favoris/+page.svelte:27`
- `src/lib/components/articles/ArticleListView.svelte:108,214,247,274`

## Behavior

1. Validates user authentication
2. Processes query parameters:
   - Treats empty or `'__ALL__'` specialty as null (show all disciplines)
   - Sets sub-discipline to null if main discipline is null
3. Calls the `get_liked_articles` RPC function with:
   - User ID for filtering liked articles
   - Discipline and sub-discipline filters
   - Pagination offset
   - Search term for content filtering
4. Returns paginated results of user's liked articles

## Error Handling

- **401**: User not authenticated
- **500**: Database RPC error

## Notes

This endpoint uses the same RPC function as other article listing endpoints but filters specifically for articles the user has liked. The filtering logic supports both discipline-level and sub-discipline-level filtering while maintaining the same interface as other article endpoints. 