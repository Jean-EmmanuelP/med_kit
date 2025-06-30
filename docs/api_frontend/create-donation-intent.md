# POST `/api/create-donation-intent`

Creates a Stripe Payment Intent for one-time donations, supporting multiple payment methods including cards and SEPA debit.

## Authentication

**Optional:** User authentication is not required, but user ID will be stored in metadata if available.

## Request Body

```typescript
{
  amount: number,              // Amount in cents (minimum 50 cents = €0.50)
  paymentMethodType: string    // 'card' or 'sepa_debit'
}
```

## Response

### Success (200)
```typescript
{
  clientSecret: string // Payment Intent client secret for Stripe Elements
}
```

## Usage in Frontend

Used on the donations page (`/donations`) when users select a donation amount and payment method.

**Location:** `src/routes/donations/+page.svelte:119`

## Behavior

1. Validates the donation amount (minimum €0.50)
2. Validates the payment method type (`card` or `sepa_debit`)
3. Creates a Stripe Payment Intent with appropriate configuration:
   - For card payments: Standard card processing
   - For SEPA debit: Includes `setup_future_usage: 'off_session'` for mandate handling
4. Stores metadata including user ID (if authenticated) and donation type
5. Returns client secret for frontend payment processing

## Error Handling

- **400**: Invalid amount (below minimum) or invalid payment method type
- **500**: Server configuration error or Stripe API error

## Payment Method Support

- **Card**: Credit/debit cards, Apple Pay, Google Pay
- **SEPA Debit**: European bank account direct debit

## Notes

The endpoint description includes `'Don ponctuel (${paymentMethodType}) pour Veille Médicale'` which translates to "One-time donation (payment method) for Medical Watch". 