# POST `/api/dismiss-feature-notice`

Marks a feature notice or tooltip as seen by the user, preventing it from being displayed again.

## Authentication

**Required:** User must be authenticated with a valid session.

## Request Body

No body required.

## Response

### Success (204)
No content - the operation completed successfully.

## Usage in Frontend

Used in the `Header.svelte` component when users dismiss feature notices or tooltips.

**Location:** `src/lib/components/Header.svelte:109`

## Behavior

1. Validates user authentication
2. Updates the user's profile in the `user_profiles` table:
   - Sets `has_seen_tooltip` to `true`
   - Sets `tooltip_time` to current timestamp
3. Returns 204 No Content on successful update

## Error Handling

- **401**: User not authenticated
- **500**: Database error updating profile

## Notes

This endpoint is used to track which users have seen specific UI notices or tooltips, ensuring they don't see the same notice repeatedly. 