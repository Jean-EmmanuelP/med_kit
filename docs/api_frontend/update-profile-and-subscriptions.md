# POST `/api/update-profile-and-subscriptions`

Updates user profile information, discipline subscriptions, and grade preferences in a single atomic operation.

## Authentication

**Required:** User must be authenticated with a valid session.

## Request Body

```typescript
{
  profile: {
    first_name?: string,
    last_name?: string,
    status?: string | null,
    specialty?: string | null,
    notification_frequency?: string,
    date_of_birth?: string | null
  },
  subscriptions: Array<{
    discipline_id: number,
    sub_discipline_id: number | null
  }>,
  gradePreferences: string[]  // Array of grades like ['A', 'B', 'C']
}
```

## Response

### Success (200)
```typescript
{
  success: true,
  message: "Profil et préférences mis à jour avec succès."
}
```

## Usage in Frontend

Used in the account page (`/account`) when users update their profile settings and subscription preferences.

**Location:** `src/routes/account/+page.svelte:171`

## Behavior

1. Validates user authentication and request data
2. **Updates Profile**: Updates the `user_profiles` table with provided profile fields
3. **Updates Grade Preferences**:
   - Deletes existing grade preferences for the user
   - Inserts new grade preferences from the array
4. **Updates Subscriptions**:
   - Deletes existing subscriptions for the user
   - Processes subscription logic:
     - If specific sub-disciplines are selected: stores only those sub-discipline subscriptions
     - If only main discipline is selected (no subs): stores main discipline subscription with `sub_discipline_id: null`
   - Inserts new subscription records

## Error Handling

- **401**: User not authenticated
- **400**: Missing required data or invalid grade preferences
- **500**: Database error during any of the update operations

## Validation

- **Grade Preferences**: Only accepts 'A', 'B', 'C' as valid grades
- **Profile Fields**: Explicitly excludes `minimum_grade_notification` if accidentally sent

## Notes

- All operations are performed as separate database calls but within the same transaction context
- The subscription logic ensures that users are subscribed to either main disciplines or specific sub-disciplines, but not both for the same discipline
- Success message is in French: "Profile and preferences updated successfully"
- The endpoint handles complex subscription relationships while maintaining data consistency 