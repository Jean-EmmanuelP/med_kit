# POST `/api/create-customer-portal-session`

Creates a Stripe Customer Portal session URL where users can manage their billing and subscription details.

## Authentication

**Required:** User must be authenticated with a valid session.

## Request Body

No body required.

## Response

### Success (200)
```typescript
{
  url: string // Stripe Customer Portal session URL
}
```

## Usage in Frontend

Used in `SubscriptionStatus.svelte` component when users click the "Manage Billing" button to access their Stripe customer portal.

**Location:** `src/lib/components/SubscriptionStatus.svelte:96`

## Behavior

1. Validates user authentication
2. Fetches user's Stripe Customer ID from the `user_profiles` table
3. Creates a Stripe billing portal session with return URL set to `/account`
4. Returns the portal session URL for redirection

## Error Handling

- **401**: User not authenticated
- **404**: User doesn't have a Stripe Customer ID
- **500**: Server configuration error, database error, or Stripe API error

## Notes

The return URL is automatically set to the account page (`/account`) where users will be redirected after finishing their session in the Stripe portal. 