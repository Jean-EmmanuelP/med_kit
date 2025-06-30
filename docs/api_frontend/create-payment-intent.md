# POST `/api/create-payment-intent` (Legacy)

**⚠️ Legacy Endpoint**: This endpoint appears to be an older version of subscription creation that may not be actively used.

Creates a Stripe subscription with a payment intent for monthly or yearly plans.

## Authentication

**Not Required:** This endpoint doesn't explicitly check for user authentication.

## Request Body

```typescript
{
  plan: 'monthly' | 'yearly'  // Plan identifier
}
```

## Response

### Success (200)
```typescript
{
  clientSecret: string,     // Payment Intent client secret
  subscriptionId: string    // Stripe subscription ID
}
```

## Usage in Frontend

This endpoint doesn't appear to be actively used in the current frontend codebase. It may have been replaced by `/api/create-subscription`.

## Behavior

1. Validates the plan parameter ('monthly' or 'yearly')
2. Determines the appropriate Stripe Price ID based on environment variables
3. Creates a new Stripe Customer (without linking to user account)
4. Creates a Stripe Subscription with:
   - `payment_behavior: 'default_incomplete'`
   - `payment_settings: { save_default_payment_method: 'on_subscription' }`
5. Returns the client secret for payment confirmation

## Error Handling

- **400**: Invalid plan selected
- **500**: Server configuration error or Stripe API error

## Environment Variables Required

- `STRIPE_SECRET_KEY`: Stripe secret API key
- `STRIPE_MONTHLY_PRICE_ID`: Price ID for monthly subscription
- `STRIPE_YEARLY_PRICE_ID`: Price ID for yearly subscription

## Notes

- This endpoint creates anonymous customers not linked to user accounts
- It uses Stripe API version '2023-10-16' (older than the main create-subscription endpoint)
- Consider using `/api/create-subscription` for new implementations as it properly handles user authentication and customer linking 