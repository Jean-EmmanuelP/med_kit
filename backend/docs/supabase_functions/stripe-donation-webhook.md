# Stripe Donation Webhook

**Location**: `supabase/functions/stripe-donation-webhook/index.ts`

**Purpose**: Processes Stripe webhook events for one-time donations, validating payments and recording them in the database.

## Function Overview

This webhook function handles the `payment_intent.succeeded` event from Stripe for processing completed donation payments.

## Key Features

### 🔒 Webhook Security
- Verifies Stripe webhook signatures using `STRIPE_WEBHOOK_SIGNING_SECRET`
- Prevents unauthorized or tampered webhook calls
- Uses Stripe's official signature verification

### 💰 Payment Processing
- Handles `payment_intent.succeeded` events specifically
- Extracts payment details (amount, currency, status)
- Records successful donations in the database

### 👤 User Association
- Links donations to users via `user_id` in payment metadata
- Handles anonymous donations gracefully
- Tracks donation history per user

## Webhook Event Handling

### Supported Events
- **`payment_intent.succeeded`**: Processes completed donation payments
- **Other Events**: Logged but not processed

### Required Headers
```
POST /functions/v1/stripe-donation-webhook
Stripe-Signature: t=timestamp,v1=signature
Content-Type: application/json
```

## Payment Processing Flow

### 1. Signature Verification
```typescript
const event = await stripe.webhooks.constructEventAsync(
  body, 
  signature, 
  signingSecret
);
```

### 2. Event Type Check
```typescript
if (event.type === 'payment_intent.succeeded') {
  const paymentIntent = event.data.object;
  // Process donation...
}
```

### 3. Data Extraction
```typescript
const amount = paymentIntent.amount;           // Amount in cents
const currency = paymentIntent.currency;       // Currency code (e.g., 'eur')
const status = paymentIntent.status;           // 'succeeded'
const paymentIntentId = paymentIntent.id;      // Stripe payment ID
const userId = metadata?.user_id || null;      // User from metadata
```

### 4. Database Recording
```typescript
const { error } = await supabaseAdmin
  .from('donations')
  .insert({
    user_id: userId,
    stripe_payment_intent_id: paymentIntentId,
    amount: amount,
    currency: currency,
    status: status,
    stripe_event_id: eventId,
    metadata: metadata
  });
```

## Database Schema

**Table**: `donations`

| Column | Type | Description |
|--------|------|-------------|
| `user_id` | UUID | User who made the donation (nullable for anonymous) |
| `stripe_payment_intent_id` | TEXT | Stripe PaymentIntent ID (unique) |
| `amount` | INTEGER | Amount in smallest currency unit (cents) |
| `currency` | TEXT | Currency code (e.g., 'eur', 'usd') |
| `status` | TEXT | Payment status ('succeeded') |
| `stripe_event_id` | TEXT | Stripe webhook event ID |
| `metadata` | JSONB | Additional Stripe metadata |
| `created_at` | TIMESTAMP | Auto-generated creation time |

## Error Handling

### Missing Signature
```typescript
if (!signature) {
  return new Response('Missing Stripe-Signature header', { status: 400 });
}
```

### Invalid Signature
```typescript
catch (err) {
  console.error(`Webhook signature verification failed: ${err.message}`);
  return new Response(`Webhook Error: ${err.message}`, { status: 400 });
}
```

### Anonymous Donations
```typescript
if (!userId) {
  console.warn('Anonymous donation, not tracked');
  return new Response(JSON.stringify({
    received: true,
    message: 'Success (anonymous donation, not tracked)'
  }), { status: 200 });
}
```

### Duplicate Events
```typescript
if (insertError.code === '23505') {  // Unique constraint violation
  console.warn('Donation already exists, skipping duplicate');
  return new Response(JSON.stringify({ received: true }), { status: 200 });
}
```

## Response Formats

### Success
```json
{
  "received": true
}
```

### Anonymous Donation
```json
{
  "received": true,
  "message": "Success (anonymous donation, not tracked)"
}
```

### Database Error (Still Success to Stripe)
```json
{
  "received": true,
  "error": "Database insert failed",
  "details": "Error details..."
}
```

## Environment Variables Required

```env
STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key
STRIPE_WEBHOOK_SIGNING_SECRET=whsec_your_webhook_signing_secret
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

## Stripe Dashboard Configuration

### Webhook Endpoint
- **URL**: `https://your-project.supabase.co/functions/v1/stripe-donation-webhook`
- **Events**: `payment_intent.succeeded`
- **API Version**: `2023-10-16`

### Payment Intent Metadata
Include user identification in payment creation:
```javascript
const paymentIntent = await stripe.paymentIntents.create({
  amount: donationAmount,
  currency: 'eur',
  metadata: {
    user_id: currentUser.id,  // Critical for user association
    donation_type: 'one_time'
  }
});
```

## Testing

### Test Mode Setup
1. Use test API keys in development
2. Configure test webhook endpoint
3. Use test payment methods

### Webhook Testing
```bash
# Using Stripe CLI
stripe listen --forward-to localhost:54321/functions/v1/stripe-donation-webhook

# Trigger test event
stripe trigger payment_intent.succeeded
```

### Manual Testing
```bash
curl -X POST https://your-project.supabase.co/functions/v1/stripe-donation-webhook \
  -H "Stripe-Signature: valid_stripe_signature" \
  -H "Content-Type: application/json" \
  -d '{"type": "payment_intent.succeeded", "data": {...}}'
```

## Monitoring

### Key Metrics
- **Success Rate**: Webhook processing success vs failures
- **Duplicate Rate**: How often duplicate events are received
- **Anonymous Rate**: Percentage of donations without user_id
- **Processing Time**: Webhook response times

### Logs to Monitor
- Signature verification failures
- Database insert errors
- Anonymous donations
- Duplicate event handling

## Security Considerations

- **Always verify webhook signatures** - prevents unauthorized calls
- **Use service role key** - bypasses RLS for database writes
- **Return 200 for most errors** - prevents Stripe retries
- **Log but don't expose sensitive data** in error responses
- **Validate event structure** before processing 