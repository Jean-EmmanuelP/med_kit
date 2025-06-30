# POST `/api/update-feedback-modal`

Updates the feedback modal timestamp for the authenticated user to control when the feedback modal should be displayed.

## Authentication

**Required:** User must be authenticated with a valid session.

## Request Body

No body required.

## Response

### Success (200)
```typescript
{
  success: true,
  message: "Timestamp updated"
}
```

## Usage in Frontend

Used in feedback modal components to control the display timing of feedback requests.

**Locations:**
- `src/components/FeedbackModal.svelte:25,105` - When interacting with the modal
- `src/lib/components/FeedbackModalChecker.svelte:49` - For background timestamp updates

## Behavior

1. Validates user authentication
2. Fetches the current `feedback_modal` timestamp from the user's profile
3. Updates the timestamp based on current value:
   - **If NULL (first time)**: Sets to 23 days ago (triggers immediate modal display eligibility)
   - **If not NULL (has value)**: Sets to current time (resets the display timer)
4. Updates the `user_profiles` table with the new timestamp

## Error Handling

- **401**: User not authenticated
- **500**: Database error fetching or updating profile

## Notes

- This endpoint is part of the feedback modal timing system that ensures users see feedback requests at appropriate intervals
- Setting the timestamp to 23 days ago when NULL ensures the modal becomes eligible for display
- Setting it to the current time when it already exists resets the timer for the next feedback request
- The 23-day calculation is done in JavaScript and formatted as an ISO string for database storage 