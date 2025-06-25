# Stripe Recurring Handler (Production)

**Location**: `supabase/functions/stripe-recurring-handler/index.ts`

**Purpose**: Processes Stripe webhook events for recurring subscription payments in production, handling monthly and yearly subscription renewals.

## Function Overview

This webhook handles `invoice.payment_succeeded` events to process subscription renewals and update user subscription status in the database.

## Key Features

### 🔄 Subscription Management
- Processes monthly and yearly subscription renewals
- Updates subscription status and period information
- Handles subscription lifecycle events

### 🔒 Production Security
- Live Stripe API keys and webhook secrets
- Secure webhook signature verification
- Production-grade error handling

### 💳 Price Validation
- Validates against configured monthly/yearly price IDs
- Ignores unknown or test prices
- Ensures only legitimate subscriptions are processed

## Configuration

### Price IDs (Hardcoded for Production)
```typescript
const MONTHLY_PRICE_ID = "price_1RWFkCCkHiGS8lZz5O5MRk5r";
const YEARLY_PRICE_ID = "price_1RVoCuCkHiGS8lZzLvI7uF1d";
```

### API Configuration
```typescript
const stripe = new Stripe(STRIPE_SECRET_KEY, {
  apiVersion: '2025-03-31.basil',
  httpClient: Stripe.createFetchHttpClient(),
  typescript: true
});
```

## Webhook Event Processing

### Supported Events
- **`invoice.payment_succeeded`**: Processes successful subscription payments
- **Other Events**: Logged and ignored

### Processing Flow

#### 1. Invoice Validation
```typescript
// Extract price ID from invoice line items
const lineItem = invoice.lines?.data?.[0];
const priceIdFromInvoice = lineItem?.price?.id;

// Validate against known prices
if (priceIdFromInvoice !== MONTHLY_PRICE_ID && priceIdFromInvoice !== YEARLY_PRICE_ID) {
  return new Response(JSON.stringify({
    received: true,
    ignored: 'unknown_price_id'
  }), { status: 200 });
}
```

#### 2. Subscription Retrieval
```typescript
// Get subscription ID from invoice
const stripeSubscriptionId = invoice.subscription;
const subscription = await stripe.subscriptions.retrieve(stripeSubscriptionId);
```

#### 3. User Lookup
```typescript
// Find user by Stripe customer ID
const { data: userProfile } = await supabaseAdmin
  .from('user_profiles')
  .select('id')
  .eq('stripe_customer_id', stripeCustomerId)
  .single();
```

#### 4. Database Update
```typescript
const subscriptionData = {
  user_profile_id: userProfileId,
  stripe_subscription_id: subscription.id,
  stripe_customer_id: subscription.customer,
  stripe_price_id: subscription.items.data[0]?.price?.id,
  status: subscription.status,
  current_period_start: safeConvertToISODate(subscription.current_period_start),
  current_period_end: safeConvertToISODate(subscription.current_period_end),
  cancel_at_period_end: subscription.cancel_at_period_end,
  canceled_at: safeConvertToISODate(subscription.canceled_at),
  trial_start: safeConvertToISODate(subscription.trial_start),
  trial_end: safeConvertToISODate(subscription.trial_end)
};

await supabaseAdmin
  .from('user_profile_subscriptions')
  .upsert(subscriptionData, { onConflict: 'stripe_subscription_id' });
```

## Database Schema

**Table**: `user_profile_subscriptions`

| Column | Type | Description |
|--------|------|-------------|
| `user_profile_id` | UUID | User profile reference |
| `stripe_subscription_id` | TEXT | Stripe subscription ID (unique) |
| `stripe_customer_id` | TEXT | Stripe customer ID |
| `stripe_price_id` | TEXT | Monthly or yearly price ID |
| `status` | TEXT | Subscription status (active, past_due, etc.) |
| `current_period_start` | TIMESTAMPTZ | Current billing period start |
| `current_period_end` | TIMESTAMPTZ | Current billing period end |
| `cancel_at_period_end` | BOOLEAN | Will cancel at period end |
| `canceled_at` | TIMESTAMPTZ | Cancellation timestamp |
| `trial_start` | TIMESTAMPTZ | Trial period start |
| `trial_end` | TIMESTAMPTZ | Trial period end |

## Error Handling

### Unknown Price IDs
```typescript
if (priceIdFromInvoice !== MONTHLY_PRICE_ID && priceIdFromInvoice !== YEARLY_PRICE_ID) {
  console.log('Ignoring unknown price ID:', priceIdFromInvoice);
  return new Response(JSON.stringify({
    received: true,
    ignored: 'unknown_price_id'
  }), { status: 200 });
}
```

### Missing Subscription ID
```typescript
if (!stripeSubscriptionId) {
  console.error('Subscription ID missing from invoice');
  return new Response('Subscription ID missing', { status: 400 });
}
```

### User Not Found
```typescript
if (!userProfile) {
  console.error('User not found for customer:', stripeCustomerId);
  return new Response(`User not found for customer ${stripeCustomerId}`, { status: 404 });
}
```

### Date Conversion Issues
```typescript
const safeConvertToISODate = (unixTimestamp) => {
  if (typeof unixTimestamp === 'number' && !isNaN(unixTimestamp) && isFinite(unixTimestamp)) {
    return new Date(unixTimestamp * 1000).toISOString();
  }
  return null;
};
```

## Production Environment Variables

```env
# Production Stripe Keys
STRIPE_SECRET_KEY=sk_live_your_production_secret_key
STRIPE_WEBHOOK_SIGNING_SECRET=whsec_your_production_signing_secret

# Supabase Production
SUPABASE_URL=your_production_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_production_service_role_key
```

## Stripe Dashboard Configuration

### Webhook Endpoint
- **URL**: `https://your-production-project.supabase.co/functions/v1/stripe-recurring-handler`
- **Events**: `invoice.payment_succeeded`
- **API Version**: `2025-03-31.basil`

### Subscription Products
- **Monthly Subscription**: `price_1RWFkCCkHiGS8lZz5O5MRk5r`
- **Yearly Subscription**: `price_1RVoCuCkHiGS8lZzLvI7uF1d`

## Monitoring

### Key Metrics
- **Processing Success Rate**: Webhooks processed vs failed
- **Subscription Status Updates**: Monthly vs yearly renewals
- **User Lookup Success**: Customer ID to user mapping success
- **Database Update Success**: Subscription data persistence

### Critical Logs
```typescript
console.log(`Processing ${planType} subscription: ${stripeSubscriptionId}`);
console.log(`Found user_profile_id: ${userProfileId} for customer ${stripeCustomerId}`);
console.log(`Subscription ${subscription.id} successfully processed`);
```

## Testing

### Production Testing
⚠️ **Warning**: This is the production handler - test carefully!

### Stripe CLI Testing
```bash
# Listen to production webhooks (use cautiously)
stripe listen --forward-to https://your-project.supabase.co/functions/v1/stripe-recurring-handler

# Test specific event
stripe events resend evt_production_event_id
```

### Integration Testing
Test with real subscription renewals in production:
1. Monitor webhook delivery in Stripe Dashboard
2. Verify database updates in Supabase
3. Check user subscription status in application

## Security Considerations

- **Production API Keys**: Securely stored in Supabase environment
- **Webhook Signature Verification**: Always validates incoming requests
- **Error Response Strategy**: Returns 200 for most errors to prevent retries
- **Database Access**: Uses service role key for unrestricted access
- **Logging**: Comprehensive but excludes sensitive data

## Troubleshooting

### Common Issues
1. **Unknown Price ID**: Check if new products need to be added
2. **User Not Found**: Verify customer ID mapping in database
3. **Date Conversion Errors**: Check Unix timestamp validity
4. **Webhook Signature Failures**: Verify endpoint and secret configuration 