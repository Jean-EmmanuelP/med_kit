# POST `/api/mark-article-read`

Marks an article as read by the authenticated user using an upsert operation.

## Authentication

**Required:** User must be authenticated with a valid session.

## Request Body

```typescript
{
  articleId: number  // ID of the article to mark as read
}
```

## Response

### Success (200)
```typescript
{
  success: true,
  message: "Article marked as read"
}
```

## Usage in Frontend

Used in multiple components when users interact with articles:

**Locations:**
- `src/lib/components/articles/ArticleImmersiveModal.svelte:39` - When viewing article details
- `src/lib/components/articles/ArticleListView.svelte:324` - When clicking on articles in lists

## Behavior

1. Validates user authentication
2. Validates the `articleId` parameter is a valid number
3. Performs an upsert operation on the `article_read` table:
   - Inserts a new record if the user hasn't read this article
   - Ignores the operation if the record already exists (`ignoreDuplicates: true`)
4. Returns success confirmation

## Error Handling

- **401**: User not authenticated
- **400**: Missing or invalid `articleId` in request body
- **404**: Article not found (foreign key violation)
- **500**: Database error

## Notes

- Uses upsert with `ignoreDuplicates: true` to handle cases where the article is already marked as read
- This operation is idempotent - calling it multiple times for the same article/user combination has no negative effects
- Triggers database triggers that update denormalized read counts in the articles table 