# POST `/api/toggle-article-like`

Toggles the like status of an article for the authenticated user (like if not liked, unlike if already liked).

## Authentication

**Required:** User must be authenticated with a valid session.

## Request Body

```typescript
{
  articleId: number  // ID of the article to toggle like status
}
```

## Response

### Success - Article Liked (201)
```typescript
{
  success: true,
  liked: true,
  message: "Article liked"
}
```

### Success - Article Unliked (200)
```typescript
{
  success: true,
  liked: false,
  message: "Article unliked"
}
```

## Usage in Frontend

Used in `ArticleListView.svelte` component when users click the like button on articles.

**Location:** `src/lib/components/articles/ArticleListView.svelte:416`

## Behavior

1. Validates user authentication and article ID
2. Attempts to delete existing like record first
3. If no like existed (delete count = 0):
   - Inserts a new like record
   - Returns `liked: true` with 201 status
4. If like existed and was deleted (delete count > 0):
   - Returns `liked: false` with 200 status

## Error Handling

- **401**: User not authenticated
- **400**: Missing or invalid `articleId`
- **404**: Article not found (foreign key violation)
- **500**: Database error

## Notes

- Uses a delete-first approach to avoid race conditions
- The operation is atomic and handles concurrent requests gracefully
- Handles potential unique constraint violations from race conditions by logging a warning
- Triggers database triggers that update denormalized like counts in the articles table 