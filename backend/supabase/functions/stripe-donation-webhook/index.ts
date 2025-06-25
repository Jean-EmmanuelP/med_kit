// supabase/functions/stripe-donation-webhook/index.ts
import { serve } from 'https://deno.land/std@0.177.0/http/server.ts';
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.43.4';
import Stripe from 'https://esm.sh/stripe@14.12.0?target=deno';
// Initialize Stripe
const stripe = new Stripe(Deno.env.get('STRIPE_SECRET_KEY'), {
  httpClient: Stripe.createFetchHttpClient(),
  apiVersion: '2023-10-16'
});

const supabaseAdmin = createClient(Deno.env.get('SUPABASE_URL'), Deno.env.get('SUPABASE_SERVICE_ROLE_KEY'));
serve(async (req)=>{
  if (req.method !== 'POST') {
    return new Response('Method Not Allowed', {
      status: 405
    });
  }
  const signature = req.headers.get('Stripe-Signature');
  if (!signature) {
    console.error('Missing Stripe-Signature header');
    return new Response('Missing Stripe-Signature header', {
      status: 400
    });
  }
  const signingSecret = Deno.env.get('STRIPE_WEBHOOK_SIGNING_SECRET');
  if (!signingSecret) {
    console.error('Missing STRIPE_WEBHOOK_SIGNING_SECRET environment variable');
    return new Response('Webhook signing secret not configured', {
      status: 500
    });
  }
  let event;
  const body = await req.text(); // Read body as text for verification
  try {
    event = await stripe.webhooks.constructEventAsync(body, signature, signingSecret, undefined, Stripe.createSubtleCryptoProvider() // Deno specific
    );
    console.log('Webhook signature verified. Event ID:', event.id);
  } catch (err) {
    console.error(`Webhook signature verification failed: ${err.message}`);
    return new Response(`Webhook Error: ${err.message}`, {
      status: 400
    });
  }
  // --- Handle the payment_intent.succeeded event ---
  if (event.type === 'payment_intent.succeeded') {
    const paymentIntent = event.data.object;
    console.log(`Processing successful PaymentIntent: ${paymentIntent.id}`);
    // Extract relevant data
    const amount = paymentIntent.amount;
    const currency = paymentIntent.currency;
    const status = paymentIntent.status; // Should be 'succeeded'
    const paymentIntentId = paymentIntent.id;
    const eventId = event.id;
    const metadata = paymentIntent.metadata; // Includes our user_id
    const userId = metadata?.user_id || null; // Get user_id from metadata
    console.log(`Amount: ${amount}, Currency: ${currency}, Status: ${status}, UserID: ${userId}`);
    if (!userId) {
      console.warn(`PaymentIntent ${paymentIntentId} succeeded but has no user_id in metadata. Skipping donation table insert.`);
      // Still return 200 to Stripe so it doesn't retry
      return new Response(JSON.stringify({
        received: true,
        message: 'Success (anonymous donation, not tracked)'
      }), {
        status: 200,
        headers: {
          'Content-Type': 'application/json'
        }
      });
    }
    try {
      // Insert into the donations table using the ADMIN client (bypasses RLS)
      const { error: insertError } = await supabaseAdmin.from('donations').insert({
        user_id: userId,
        stripe_payment_intent_id: paymentIntentId,
        amount: amount,
        currency: currency,
        status: status,
        stripe_event_id: eventId,
        metadata: metadata
      });
      if (insertError) {
        // Handle potential unique constraint violation (webhook received twice)
        if (insertError.code === '23505') {
          console.warn(`Donation record for PaymentIntent ${paymentIntentId} already exists. Skipping duplicate insert.`);
        // Return 200 OK as we've already processed this successfully
        } else {
          // Log other database errors but still return 200 if possible
          console.error(`Database insert error for PaymentIntent ${paymentIntentId}:`, insertError);
          // Depending on the error, you might want to return 500, but often it's better
          // to return 200 to prevent Stripe retries for non-critical DB issues.
          // Let's return 200 but log it was an error server-side.
          return new Response(JSON.stringify({
            received: true,
            error: 'Database insert failed',
            details: insertError.message
          }), {
            status: 200,
            headers: {
              'Content-Type': 'application/json'
            }
          });
        }
      } else {
        console.log(`Successfully inserted donation record for PaymentIntent ${paymentIntentId}`);
      }
    } catch (dbErr) {
      // Catch any other unexpected errors during DB interaction
      console.error(`Unexpected error during database operation for PaymentIntent ${paymentIntentId}:`, dbErr);
      return new Response(JSON.stringify({
        received: true,
        error: 'Internal server error during DB operation'
      }), {
        status: 200,
        headers: {
          'Content-Type': 'application/json'
        }
      });
    }
  } else {
    console.log(`Unhandled event type: ${event.type}`);
  }
  // Return a 200 response to acknowledge receipt of the event
  return new Response(JSON.stringify({
    received: true
  }), {
    status: 200,
    headers: {
      'Content-Type': 'application/json'
    }
  });
});
