import { env } from '$env/dynamic/private';
import { error, json } from '@sveltejs/kit';
import Stripe from 'stripe';
import type { RequestEvent } from '@sveltejs/kit';

const stripeSecretKey = env.STRIPE_SECRET_KEY || process.env.STRIPE_SECRET_KEY;

if (!stripeSecretKey) {
    console.error("Stripe configuration error: Missing secret key in environment variables.");
    // Avoid throwing here during module load, handle in POST
}

const stripe = new Stripe(stripeSecretKey!, {
    apiVersion: '2025-03-31.basil', // Use the latest supported API version
});

export async function POST({ request, locals: { supabase, safeGetSession } }: RequestEvent) {
    // --- Get User for Metadata ---
    const { user } = await safeGetSession();
    // Allow anonymous donations, but log if user isn't logged in
    if (!user) {
        console.warn("Creating donation intent for anonymous user.");
    }
    // --- Check for missing config on request ---
    if (!stripeSecretKey) {
        console.error("Stripe configuration missing on request.");
        throw error(500, "Server configuration error: Stripe details not set.");
    }

    try {
        const { amount } = await request.json(); // Expect amount in cents

        // --- Validate Amount ---
        if (typeof amount !== 'number' || !Number.isInteger(amount) || amount <= 0) {
            // Stripe minimum amount is typically around 50 cents (0.50 EUR)
            if (amount < 50) {
                 throw error(400, 'Le montant minimum de don est de 0.50 €.');
            }
            throw error(400, 'Montant invalide fourni.');
        }

        // --- Create the Payment Intent ---
        console.log(`Creating PaymentIntent for amount: ${amount} cents`);
        const paymentIntent = await stripe.paymentIntents.create({
            amount: amount,
            currency: 'eur',
            description: 'Don ponctuel pour Veille Médicale', // Customize description
            // Enable automatic capture and common payment methods
            automatic_payment_methods: {
                enabled: true,
            },
            // Optionally add metadata
            metadata: {
                // Add user ID if available
                user_id: user?.id || null,
                donation_type: 'one-time',
            },
        });

        // --- Return the Client Secret ---
        if (!paymentIntent.client_secret) {
             throw new Error('Could not retrieve client secret from Payment Intent.');
        }

        console.log(`PaymentIntent created successfully: ${paymentIntent.id}`);
        return json({
            clientSecret: paymentIntent.client_secret
        });

    } catch (err: unknown) {
        console.error("Stripe API Error:", err);
        // Distinguish Stripe errors from other errors
        if (err instanceof Stripe.errors.StripeError) {
             throw error(err.statusCode || 500, `Stripe Error: ${err.message}`);
        } else if (err && typeof err === 'object' && 'status' in err && err.status === 400) {
             throw error(400, (err as any).body?.message || 'Bad Request');
        } else {
             throw error(500, `Error creating payment intent: ${err instanceof Error ? err.message : 'Unknown server error'}`);
        }
    }
}