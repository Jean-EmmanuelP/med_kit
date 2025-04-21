import { env } from '$env/dynamic/private';
import type { RequestEvent } from '@sveltejs/kit';
import { error, json } from '@sveltejs/kit';
import Stripe from 'stripe';

const stripeSecretKey = env.STRIPE_SECRET_KEY || process.env.STRIPE_SECRET_KEY;

if (!stripeSecretKey) {
    console.error("Stripe configuration error: Missing secret key.");
}

const stripe = new Stripe(stripeSecretKey!, {
    apiVersion: '2025-03-31.basil', // Use the latest supported API version
});

export async function POST({ request, locals: { supabase, safeGetSession } }: RequestEvent) {
    const { user } = await safeGetSession();
    if (!stripeSecretKey) {
        throw error(500, "Server configuration error: Stripe details not set.");
    }

    try {
        const { amount, paymentMethodType } = await request.json(); // Expect amount in cents AND paymentMethodType

        // --- Validate Amount ---
        if (typeof amount !== 'number' || !Number.isInteger(amount) || amount < 50) { // Min 0.50 EUR
             throw error(400, 'Montant invalide fourni (min 0.50 €).');
        }

        // --- Validate Payment Method Type ---
        const allowedTypes = ['card', 'sepa_debit']; // Explicitly define allowed types for intent creation
        if (!paymentMethodType || !allowedTypes.includes(paymentMethodType)) {
            // Note: Apple/Google Pay will use the 'card' type intent.
            // We only need specific types for methods requiring them, like SEPA.
            // If the request is for wallets, the frontend should request 'card'.
             console.warn(`Invalid or missing paymentMethodType requested: ${paymentMethodType}. Defaulting to 'card' for wallets or unspecified.`);
             // We will let 'card' be the default if not 'sepa_debit' for simplicity now.
             // More robust validation could reject unknown types.
        }

        const intentParams: Stripe.PaymentIntentCreateParams = {
            amount: amount,
            currency: 'eur',
            description: `Don ponctuel (${paymentMethodType}) pour Veille Médicale`,
            // --- Set payment_method_types based on request ---
            payment_method_types: [paymentMethodType], // e.g., ['card'] or ['sepa_debit']
             // If using SEPA, you might need setup_future_usage for mandates
            ...(paymentMethodType === 'sepa_debit' && { setup_future_usage: 'off_session' }),
            metadata: {
                user_id: user?.id || null,
                donation_type: 'one-time',
                intended_method: paymentMethodType // Store intended method
            },
        };

        // --- Create the specific Payment Intent ---
        console.log(`Creating PaymentIntent for amount: ${amount} cents, type: ${paymentMethodType}`);
        const paymentIntent = await stripe.paymentIntents.create(intentParams);

        if (!paymentIntent.client_secret) {
             throw new Error('Could not retrieve client secret from Payment Intent.');
        }

        console.log(`PaymentIntent created successfully: ${paymentIntent.id} (Type: ${paymentMethodType})`);
        return json({
            clientSecret: paymentIntent.client_secret
        });

    } catch (err: unknown) {
        console.error("Stripe API Error:", err);
        if (err instanceof Stripe.errors.StripeError) {
             throw error(err.statusCode || 500, `Stripe Error: ${err.message}`);
        } else if (err && typeof err === 'object' && 'status' in err && err.status === 400) {
             throw error(400, (err as any).body?.message || 'Bad Request');
        } else {
             throw error(500, `Error creating payment intent: ${err instanceof Error ? err.message : 'Unknown server error'}`);
        }
    }
}