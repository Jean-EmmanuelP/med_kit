import { serve } from 'https://deno.land/std@0.177.0/http/server.ts';
import { createClient } from 'npm:@supabase/supabase-js@^2.0.0';
import Stripe from 'npm:stripe@^14.0.0';
const STRIPE_SECRET_KEY = "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";
const SUPABASE_URL = Deno.env.get('SUPABASE_URL');
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
const STRIPE_WEBHOOK_SIGNING_SECRET = "whsec_0iZyhJQeeHZZaxW8b7gvm8VHt8I6tGsP";
const MONTHLY_PRICE_ID_FROM_ENV = "price_1RWFkCCkHiGS8lZz5O5MRk5r";
const YEARLY_PRICE_ID_FROM_ENV = "price_1RVoCuCkHiGS8lZzLvI7uF1d";
if (!STRIPE_SECRET_KEY || !SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY || !STRIPE_WEBHOOK_SIGNING_SECRET || !MONTHLY_PRICE_ID_FROM_ENV || !YEARLY_PRICE_ID_FROM_ENV) {
  console.error("FATAL: Missing one or more required environment variables for the webhook handler. Check Supabase Edge Function secrets if deployed, or hardcoded values if local.");
}
const stripe = new Stripe(STRIPE_SECRET_KEY, {
  apiVersion: '2025-03-31.basil',
  httpClient: Stripe.createFetchHttpClient(),
  typescript: true
});
const supabaseAdmin = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, {
  auth: {
    persistSession: false,
    autoRefreshToken: false
  }
});
console.log('Stripe TEST Subscription Webhook Handler (Basil API Version). Signing secret ends with:', STRIPE_WEBHOOK_SIGNING_SECRET?.slice(-6));
console.log('Expecting Monthly Price ID:', MONTHLY_PRICE_ID_FROM_ENV);
console.log('Expecting Yearly Price ID:', YEARLY_PRICE_ID_FROM_ENV);
const safeConvertToISODate = (unixTimestamp)=>{
  if (typeof unixTimestamp === 'number' && !isNaN(unixTimestamp) && isFinite(unixTimestamp)) {
    return new Date(unixTimestamp * 1000).toISOString();
  }
  return null;
};
serve(async (req)=>{
  const signature = req.headers.get('Stripe-Signature');
  const body = await req.text();
  if (!signature) {
    console.error('Webhook Error: Missing Stripe-Signature header');
    return new Response('Missing Stripe-Signature header', {
      status: 400
    });
  }
  if (!STRIPE_WEBHOOK_SIGNING_SECRET || STRIPE_WEBHOOK_SIGNING_SECRET === 'whsec_YOUR_TEST_MODE_SIGNING_SECRET_FOR_THIS_ENDPOINT') {
    console.error('Webhook Error: Signing secret is not configured correctly on the server.');
    return new Response('Webhook signing secret not configured.', {
      status: 500
    });
  }
  let event;
  try {
    event = await stripe.webhooks.constructEventAsync(body, signature, STRIPE_WEBHOOK_SIGNING_SECRET);
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
    let priceIdFromInvoice = undefined;
    const lineItem = invoice.lines?.data?.[0];
    if (lineItem) {
      if (lineItem.price && typeof lineItem.price === 'object' && lineItem.price !== null && 'id' in lineItem.price) {
        priceIdFromInvoice = lineItem.price.id;
      } else if (typeof lineItem.price === 'string') {
        priceIdFromInvoice = lineItem.price;
      } else if (lineItem.pricing?.price_details?.price && typeof lineItem.pricing.price_details.price === 'string') {
        priceIdFromInvoice = lineItem.pricing.price_details.price;
      }
    }
    if (priceIdFromInvoice !== MONTHLY_PRICE_ID_FROM_ENV && priceIdFromInvoice !== YEARLY_PRICE_ID_FROM_ENV) {
      console.log(`Webhook Info: Received invoice.payment_succeeded for an unhandled or undefined price ID: ${priceIdFromInvoice}. This webhook only handles configured monthly/yearly subscriptions. Ignoring.`);
      return new Response(JSON.stringify({
        received: true,
        ignored: 'unknown_or_undefined_price_id',
        debug_price_received: priceIdFromInvoice
      }), {
        status: 200
      });
    }
    let stripeSubscriptionId = null;
    if (typeof invoice.subscription === 'string') {
      stripeSubscriptionId = invoice.subscription;
    } else if (lineItem?.subscription) {
      stripeSubscriptionId = lineItem.subscription;
    } else if (invoice.parent && typeof invoice.parent === 'object' && invoice.parent.subscription_details?.subscription) {
      stripeSubscriptionId = invoice.parent.subscription_details.subscription;
    }
    if (typeof stripeSubscriptionId !== 'string' || !stripeSubscriptionId) {
      console.error('Webhook Error: Subscription ID could not be reliably determined from invoice object for a known price.', JSON.stringify(invoice, null, 2));
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
    const planType = priceIdFromInvoice === MONTHLY_PRICE_ID_FROM_ENV ? 'Monthly' : 'Yearly';
    console.log(`Processing ${planType} subscription: ${stripeSubscriptionId}, customer: ${stripeCustomerId}`);
    try {
      const subscription = await stripe.subscriptions.retrieve(stripeSubscriptionId);
      if (!subscription) {
        console.error(`Webhook Error: Could not retrieve subscription ${stripeSubscriptionId} from Stripe.`);
        return new Response('Subscription not found in Stripe', {
          status: 404
        });
      }
      console.log(`Retrieved Stripe Subscription (Type: ${planType}, Status: ${subscription.status}) Full object logged previously or next if error.`);
      const { data: userProfile, error: profileError } = await supabaseAdmin.from('user_profiles').select('id').eq('stripe_customer_id', stripeCustomerId).single();
      if (profileError || !userProfile) {
        console.error(`Webhook DB Error: User profile not found for Stripe customer ${stripeCustomerId}. Error:`, profileError?.message);
        return new Response(`User profile not found for customer ${stripeCustomerId}`, {
          status: 404
        });
      }
      const userProfileId = userProfile.id;
      console.log(`Found user_profile_id: ${userProfileId} for Stripe customer ${stripeCustomerId}`);
      const firstItem = subscription.items?.data?.[0];
      const subscriptionDataForDb = {
        user_profile_id: userProfileId,
        stripe_subscription_id: subscription.id,
        stripe_customer_id: typeof subscription.customer === 'string' ? subscription.customer : subscription.customer.id,
        stripe_price_id: firstItem?.price?.id,
        status: subscription.status,
        current_period_start: safeConvertToISODate(firstItem?.current_period_start),
        current_period_end: safeConvertToISODate(firstItem?.current_period_end),
        cancel_at_period_end: subscription.cancel_at_period_end || false,
        canceled_at: safeConvertToISODate(subscription.canceled_at),
        trial_start: safeConvertToISODate(subscription.trial_start),
        trial_end: safeConvertToISODate(subscription.trial_end)
      };
      if (!subscriptionDataForDb.current_period_start || !subscriptionDataForDb.current_period_end) {
        console.error(`Webhook Critical Error: current_period_start or current_period_end is null for subscription ${subscription.id}. This is unexpected for an invoice.payment_succeeded event.`, `Stripe subscription item current_period_start: ${firstItem?.current_period_start} (type: ${typeof firstItem?.current_period_start})`, `Stripe subscription item current_period_end: ${firstItem?.current_period_end} (type: ${typeof firstItem?.current_period_end})`, `Full subscription object:`, JSON.stringify(subscription, null, 2));
        return new Response('Critical date information (current_period_start or current_period_end) missing or invalid from Stripe subscription item.', {
          status: 500
        });
      }
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
      console.log(`Subscription ${subscription.id} (Type: ${planType}) successfully processed and upserted for user ${userProfileId}.`);
    } catch (processingError) {
      console.error(`Webhook Error: Error processing ${planType} subscription:`, processingError);
      return new Response(`Error processing subscription: ${processingError.message}`, {
        status: 500
      });
    }
  } else {
    console.log(`Webhook Info: Received event type ${event.type}, not handling in this function.`);
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
