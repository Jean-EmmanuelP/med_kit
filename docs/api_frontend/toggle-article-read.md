# POST `/api/toggle-article-read`

Toggles the read status of an article for the authenticated user (mark as read if unread, mark as unread if already read).

## Authentication

**Required:** User must be authenticated with a valid session.

## Request Body

```typescript
{
  articleId: number  // ID of the article to toggle read status
}
```

## Response

### Success - Article Marked as Read (201)
```typescript
{
  success: true,
  read: true,
  message: "Article marked as read"
}
```

### Success - Article Marked as Unread (200)
```typescript
{
  success: true,
  read: false,
  message: "Article marked as unread"
}
```

## Usage in Frontend

Used in `ArticleListView.svelte` component when users click the read/unread toggle button on articles.

**Location:** `src/lib/components/articles/ArticleListView.svelte:427`

## Behavior

1. Validates user authentication and article ID
2. Checks current read status by querying the `article_read` table
3. If currently read:
   - Deletes the read record
   - Returns `read: false` with 200 status
4. If currently unread:
   - Inserts a new read record
   - Returns `read: true` with 201 status

## Error Handling

- **401**: User not authenticated
- **400**: Missing or invalid `articleId` in request body
- **404**: Article not found (foreign key violation)
- **500**: Database error

## Notes

- This endpoint provides explicit read/unread toggling functionality (unlike `mark-article-read` which only marks as read)
- The operation checks current status before performing the toggle to ensure accurate state management
- Includes comprehensive logging for debugging and monitoring
- Triggers database triggers that update denormalized read counts in the articles table 