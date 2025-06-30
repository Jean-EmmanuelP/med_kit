# POST `/api/cancel-stripe-subscription`

Cancels a user's Stripe subscription by setting it to cancel at the end of the current billing period.

## Authentication

**Required:** User must be authenticated with a valid session.

## Request Body

```typescript
{
  stripeSubscriptionId: string // Stripe subscription ID to cancel
}
```

## Response

### Success (200)
```typescript
{
  message: string,
  stripeResponse: StripeSubscription,
  databaseRecord: UserProfileSubscription
}
```

### Already Canceled (200)
```typescript
{
  message: string,
  subscription: UserProfileSubscription
}
```

## Usage in Frontend

Used in `SubscriptionStatus.svelte` component when users click the "Cancel Subscription" button. The component fetches the user's subscription ID and sends it to this endpoint.

**Location:** `src/lib/components/SubscriptionStatus.svelte:69`

## Behavior

1. Validates user authentication
2. Checks if subscription exists and belongs to the user
3. If already canceled, returns appropriate message
4. Updates Stripe subscription to cancel at period end
5. Updates local database with the cancellation status
6. Returns confirmation with both Stripe and database records

## Error Handling

- **401**: User not authenticated
- **403**: Subscription not found or access denied
- **400**: Invalid request body or Stripe subscription ID
- **500**: Server configuration error, database errors, or Stripe API errors 