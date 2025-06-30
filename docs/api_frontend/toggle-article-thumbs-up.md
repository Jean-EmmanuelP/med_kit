# POST `/api/toggle-article-thumbs-up`

Toggles the thumbs-up status of an article for the authenticated user (thumbs up if not rated, remove thumbs up if already rated).

## Authentication

**Required:** User must be authenticated with a valid session.

## Request Body

```typescript
{
  articleId: number  // ID of the article to toggle thumbs-up status
}
```

## Response

### Success - Article Thumbed Up (201)
```typescript
{
  success: true,
  thumbed_up: true,
  message: "Article thumbed up"
}
```

### Success - Thumbs Up Removed (200)
```typescript
{
  success: true,
  thumbed_up: false,
  message: "Article thumbed down"
}
```

## Usage in Frontend

Used in `ArticleListView.svelte` component when users click the thumbs-up button on articles.

**Location:** `src/lib/components/articles/ArticleListView.svelte:394`

## Behavior

1. Validates user authentication and article ID
2. Attempts to delete existing thumbs-up record first
3. If no thumbs-up existed (delete count = 0):
   - Inserts a new thumbs-up record
   - Returns `thumbed_up: true` with 201 status
4. If thumbs-up existed and was deleted (delete count > 0):
   - Returns `thumbed_up: false` with 200 status

## Error Handling

- **401**: User not authenticated
- **400**: Missing or invalid `articleId`
- **404**: Article not found (foreign key violation)
- **500**: Database error

## Notes

- Uses a delete-first approach similar to the like toggle endpoint to avoid race conditions
- The operation is atomic and handles concurrent requests gracefully
- Handles potential unique constraint violations from race conditions by logging a warning
- Triggers database triggers that update denormalized thumbs-up counts in the articles table
- The `thumbed_up_at` timestamp is automatically set to the current time when inserting new records 