import { json } from '@sveltejs/kit';
import Stripe from 'stripe';
// import { SECRET_STRIPE_KEY } from '$env/static/private';

const stripe = new Stripe('sk_test_51PKxSICA4R4AS5AvVkF3adXxxei73iIIBQ5UeEt7HfH4fwHK7tSCC6pcFenpOKjy0uCZPm7fn14mHf1fqKgqZ6jx00mKsSvGcw');

export async function POST({ request }) {
    const { amount, currency, plan } = await request.json();

    // Créer un Payment Intent avec Apple Pay, Revolut Pay, et Link
    const paymentIntent = await stripe.paymentIntents.create({
        amount, // Montant en centimes (ex: 99 pour 0,99 €)
        currency, // Devise (ex: 'eur')
        payment_method_types: ['card', 'apple_pay', 'revolut_pay', 'link'], // Inclure Apple Pay, Revolut Pay, et Link
        metadata: { plan }
    });

    return json({ clientSecret: paymentIntent.client_secret });
}