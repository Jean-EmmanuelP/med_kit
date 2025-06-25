// supabase/functions/stripe-webhook-handler-monthly/index.ts
import { serve } from 'https://deno.land/std@0.177.0/http/server.ts';
import { createClient } from 'npm:@supabase/supabase-js@^2.0.0';
import Stripe from 'npm:stripe@^14.0.0'; // Using npm specifier for Deno
// --- CONFIGURATION (HARDCODED FOR NOW - MOVE TO ENV VARS FOR PRODUCTION) ---
const STRIPE_SECRET_KEY = 'sk_test_51RGM76CkHiGS8lZzmjBfgoQ8w64Dmz5yoL2mqP73VCWJoumRKKNgCMCBQgbzjgdEFAAwMasmkrz36BglNnmAxmeO00jgoPz9za';
const SUPABASE_URL = 'https://etxelhjnqbrgwuitltyk.supabase.co';
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY'); // Use Service Role Key for server-side operations
const STRIPE_WEBHOOK_SIGNING_SECRET_MONTHLY = 'whsec_X8I7Sz8wI9WIt5lBYG1c2Zo00xAwSRWE'; // Get this from Stripe Dashboard
if (!STRIPE_SECRET_KEY || !SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY || !STRIPE_WEBHOOK_SIGNING_SECRET_MONTHLY) {
  console.error("FATAL: Missing one or more required environment variables for the webhook handler.");
}
const stripe = new Stripe(STRIPE_SECRET_KEY, {
  apiVersion: '2023-10-16',
  httpClient: Stripe.createFetchHttpClient(),
  typescript: true
});
const supabaseAdmin = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, {
  auth: {
    persistSession: false,
    autoRefreshToken: false
  }
});
console.log('Stripe Webhook Handler function started. Using signing secret ending with:', STRIPE_WEBHOOK_SIGNING_SECRET_MONTHLY?.slice(-6));
serve(async (req)=>{
  const signature = req.headers.get('Stripe-Signature');
  const body = await req.text();
  if (!signature) {
    console.error('Webhook Error: Missing Stripe-Signature header');
    return new Response('Missing Stripe-Signature header', {
      status: 400
    });
  }
  if (!STRIPE_WEBHOOK_SIGNING_SECRET_MONTHLY) {
    console.error('Webhook Error: Signing secret is not configured on the server.');
    return new Response('Webhook signing secret not configured.', {
      status: 500
    });
  }
  let event;
  try {
    event = await stripe.webhooks.constructEventAsync(body, signature, STRIPE_WEBHOOK_SIGNING_SECRET_MONTHLY);
    console.log('Webhook event successfully constructed:', event.id, event.type);
  } catch (err) {
    console.error('Webhook signature verification failed:', err.message);
    return new Response(`Webhook signature verification failed: ${err.message}`, {
      status: 400
    });
  }
  if (event.type === 'invoice.payment_succeeded') {
    const invoice = event.data.object;
    console.log('Handling invoice.payment_succeeded for invoice ID:', invoice.id);
    // --- CORRECTED SUBSCRIPTION ID EXTRACTION ---
    let stripeSubscriptionId = null;
    // Option 1: Check the invoice's top-level 'subscription' field (less common for first invoice)
    if (typeof invoice.subscription === 'string') {
      stripeSubscriptionId = invoice.subscription;
    } else if (invoice.lines?.data?.[0]?.subscription) {
      stripeSubscriptionId = invoice.lines.data[0].subscription;
    } else if (invoice.parent && typeof invoice.parent === 'object' && invoice.parent.subscription_details?.subscription) {
      stripeSubscriptionId = invoice.parent.subscription_details.subscription;
    }
    if (typeof stripeSubscriptionId !== 'string' || !stripeSubscriptionId) {
      console.error('Webhook Error: Subscription ID could not be reliably determined from invoice object.', invoice);
      return new Response('Subscription ID missing or invalid in invoice', {
        status: 400
      });
    }
    const stripeCustomerId = invoice.customer;
    if (typeof stripeCustomerId !== 'string' || !stripeCustomerId) {
      console.error('Webhook Error: Customer ID missing or not a string in invoice object.', invoice);
      return new Response('Customer ID missing in invoice', {
        status: 400
      });
    }
    console.log(`Processing subscription: ${stripeSubscriptionId}, customer: ${stripeCustomerId}`);
    try {
      const subscription = await stripe.subscriptions.retrieve(stripeSubscriptionId);
      if (!subscription) {
        console.error(`Webhook Error: Could not retrieve subscription ${stripeSubscriptionId} from Stripe.`);
        return new Response('Subscription not found in Stripe', {
          status: 404
        });
      }
      console.log('Retrieved Stripe Subscription Status:', subscription.status);
      console.log('Subscription current_period_end (unix):', subscription.current_period_end);
      const { data: userProfile, error: profileError } = await supabaseAdmin.from('user_profiles').select('id').eq('stripe_customer_id', stripeCustomerId).single();
      if (profileError || !userProfile) {
        console.error(`Webhook DB Error: User profile not found for Stripe customer ${stripeCustomerId}. Error:`, profileError?.message);
        return new Response(`User profile not found for customer ${stripeCustomerId}`, {
          status: 404
        });
      }
      const userProfileId = userProfile.id;
      console.log(`Found user_profile_id: ${userProfileId} for Stripe customer ${stripeCustomerId}`);
      const subscriptionDataForDb = {
        user_profile_id: userProfileId,
        stripe_subscription_id: subscription.id,
        stripe_customer_id: typeof subscription.customer === 'string' ? subscription.customer : subscription.customer.id,
        stripe_price_id: subscription.items.data[0]?.price.id,
        status: subscription.status,
        current_period_start: new Date(subscription.current_period_start * 1000).toISOString(),
        current_period_end: new Date(subscription.current_period_end * 1000).toISOString(),
        cancel_at_period_end: subscription.cancel_at_period_end || false,
        canceled_at: subscription.canceled_at ? new Date(subscription.canceled_at * 1000).toISOString() : null,
        trial_start: subscription.trial_start ? new Date(subscription.trial_start * 1000).toISOString() : null,
        trial_end: subscription.trial_end ? new Date(subscription.trial_end * 1000).toISOString() : null
      };
      console.log('Data to upsert into user_profile_subscriptions:', subscriptionDataForDb);
      const { error: upsertError } = await supabaseAdmin.from('user_profile_subscriptions').upsert(subscriptionDataForDb, {
        onConflict: 'stripe_subscription_id',
        ignoreDuplicates: false
      });
      if (upsertError) {
        console.error('Webhook DB Error: Failed to upsert subscription data:', upsertError);
        return new Response(`Database error: ${upsertError.message}`, {
          status: 500
        });
      }
      console.log(`Subscription ${subscription.id} successfully processed and upserted for user ${userProfileId}.`);
    } catch (processingError) {
      console.error('Webhook Error: Error processing subscription:', processingError);
      return new Response(`Error processing subscription: ${processingError.message}`, {
        status: 500
      });
    }
  } else {
    console.log(`Webhook Info: Received event type ${event.type}, not handling.`);
  }
  return new Response(JSON.stringify({
    received: true
  }), {
    headers: {
      'Content-Type': 'application/json'
    },
    status: 200
  });
});
