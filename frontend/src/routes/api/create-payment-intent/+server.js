// src/routes/api/create-payment-intent/+server.js
// OR RENAME TO: src/routes/api/create-subscription/+server.js (and update fetch path in frontend)

import { env } from '$env/dynamic/private';
import { error, json } from '@sveltejs/kit';
import Stripe from 'stripe';

// --- IMPORTANT: Use your SECRET key here ---
const stripeSecretKey = env.STRIPE_SECRET_KEY || process.env.STRIPE_SECRET_KEY; // Fallback for different env setups
const monthlyPriceId = env.STRIPE_MONTHLY_PRICE_ID || process.env.STRIPE_MONTHLY_PRICE_ID;
const yearlyPriceId = env.STRIPE_YEARLY_PRICE_ID || process.env.STRIPE_YEARLY_PRICE_ID;

if (!stripeSecretKey || !monthlyPriceId || !yearlyPriceId) {
    console.error("Stripe configuration error: Missing secret key or price IDs in environment variables.");
    // Avoid throwing here during module load, handle in POST
}

const stripe = new Stripe(stripeSecretKey, {
    apiVersion: '2023-10-16', // Use a specific API version
});

export async function POST({ request }) {
    // --- Check for missing config on request ---
    if (!stripeSecretKey || !monthlyPriceId || !yearlyPriceId) {
        console.error("Stripe configuration missing on request.");
        throw error(500, "Server configuration error: Stripe details not set.");
    }

    try {
        const { plan } = await request.json(); // Read the plan identifier ('monthly' or 'yearly')

        let priceId;
        if (plan === 'monthly') {
            priceId = monthlyPriceId;
        } else if (plan === 'yearly') {
            priceId = yearlyPriceId;
        } else {
            throw error(400, 'Invalid plan selected.'); // Bad request
        }

        // --- 1. Create a Stripe Customer ---
        // In a real app, you'd check if a customer exists for logged-in user
        // You might pass user email/ID from a session/JWT here
        const customer = await stripe.customers.create({
            // email: userEmail, // Example: associate with user email
            // name: userName, // Example
            description: `Customer for ${plan} plan`, // Optional
        });

        // --- 2. Create the Subscription ---
        const subscription = await stripe.subscriptions.create({
            customer: customer.id,
            items: [{ price: priceId }],
            payment_behavior: 'default_incomplete', // Important: Wait for payment method via Elements
            payment_settings: { save_default_payment_method: 'on_subscription' }, // Save PM for future renewals
            expand: ['latest_invoice.payment_intent'], // Expand to get the PI for the first payment
            // Add trial period if needed:
            // trial_period_days: 14,
        });

        // --- 3. Extract Client Secret ---
        // The client secret is needed for the *first* payment confirmation
        const clientSecret = subscription.latest_invoice.payment_intent.client_secret;

        if (!clientSecret) {
             throw new Error('Could not retrieve client secret from subscription.');
        }

        return json({
            clientSecret: clientSecret,
            subscriptionId: subscription.id // Optionally return subscription ID if needed on client
        });

    } catch (err) {
        console.error("Stripe API Error:", err);
        // Distinguish Stripe errors from other errors
        if (err instanceof Stripe.errors.StripeError) {
             throw error(err.statusCode || 500, `Stripe Error: ${err.message}`);
        } else if (err.status === 400) { // Handle specific thrown errors like 'Invalid plan'
             throw error(400, err.body.message || 'Bad Request');
        } else {
             throw error(500, `Error creating subscription: ${err.message || 'Unknown server error'}`);
        }
    }
}