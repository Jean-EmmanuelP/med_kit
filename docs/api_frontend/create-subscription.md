# POST `/api/create-subscription`

Creates a new Stripe subscription for authenticated users with monthly or yearly billing plans.

## Authentication

**Required:** User must be authenticated with a valid session and email address.

## Request Body

```typescript
{
  planIdentifier: 'monthly' | 'yearly'
}
```

## Response

### Success (200)
```typescript
{
  subscriptionId: string,  // Stripe subscription ID
  clientSecret: string     // Payment Intent client secret for first payment
}
```

## Usage in Frontend

Used in `CheckoutForm.svelte` component during the subscription checkout process.

**Location:** `src/lib/components/CheckoutForm.svelte:78`

## Behavior

1. Validates user authentication and email availability
2. Retrieves or creates a Stripe Customer:
   - Checks for existing `stripe_customer_id` in user profile
   - Creates new Stripe customer if none exists
   - Updates user profile with new customer ID
3. Creates Stripe subscription with:
   - Appropriate price ID (monthly/yearly from environment variables)
   - Payment behavior set to `default_incomplete` (requires payment confirmation)
   - Payment settings to save payment method for future renewals
   - Metadata including user ID and plan identifier
4. Returns subscription ID and client secret for payment confirmation

## Error Handling

- **401**: User not authenticated or email missing
- **400**: Invalid plan identifier (must be 'monthly' or 'yearly')
- **500**: Server configuration error, database error, or Stripe API error

## Environment Variables Required

- `STRIPE_SECRET_KEY`: Stripe secret API key
- `STRIPE_MONTHLY_PRICE_ID`: Price ID for monthly subscription
- `STRIPE_YEARLY_PRICE_ID`: Price ID for yearly subscription

## Notes

The subscription starts with an incomplete status and requires payment confirmation on the frontend using the returned client secret. 