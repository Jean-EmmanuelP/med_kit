// /routes/api/create-customer-portal-session/+server.ts
import { STRIPE_SECRET_KEY, SUPABASE_SERVICE_ROLE_KEY } from '$env/static/private';
import { PUBLIC_SUPABASE_URL as SUPABASE_URL } from '$env/static/public';
import { createClient, type SupabaseClient } from '@supabase/supabase-js';
import { error as svelteKitError, json } from '@sveltejs/kit';
import Stripe from 'stripe';
import type { RequestHandler } from './$types';

let stripe: Stripe;
if (STRIPE_SECRET_KEY) {
	stripe = new Stripe(STRIPE_SECRET_KEY, {
		apiVersion: '2025-03-31.basil',
		typescript: true,
	});
}

let supabaseAdmin: SupabaseClient;
if (SUPABASE_URL && SUPABASE_SERVICE_ROLE_KEY) {
	supabaseAdmin = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, {
		auth: {
			persistSession: false,
			autoRefreshToken: false,
		}
	});
}

export const POST: RequestHandler = async ({ request, locals, url }) => {
	if (!stripe || !supabaseAdmin) {
		console.error('Stripe Customer Portal Error: Stripe or Supabase client not initialized.');
		throw svelteKitError(500, 'Server configuration error.');
	}

	const { session, user } = await locals.safeGetSession();
	if (!session || !user) {
		throw svelteKitError(401, 'User not authenticated.');
	}

	try {
		// Fetch the user's Stripe Customer ID from your database
		const { data: userProfile, error: profileError } = await supabaseAdmin
			.from('user_profiles') // Assuming your table is named 'user_profiles'
			.select('stripe_customer_id')
			.eq('id', user.id)
			.single();

		if (profileError) {
			console.error(`Stripe Customer Portal Error: DB error fetching profile for user ${user.id}:`, profileError);
			throw svelteKitError(500, 'Could not retrieve user payment profile.');
		}

		if (!userProfile?.stripe_customer_id) {
			console.error(`Stripe Customer Portal Error: User ${user.id} does not have a Stripe Customer ID.`);
			throw svelteKitError(404, 'Stripe customer ID not found for this user.');
		}

		const stripeCustomerId = userProfile.stripe_customer_id;

		// Define the return URL for when the user finishes in the portal
		// This should be a page on your site, perhaps the account page itself.
		const returnUrl = `${url.origin}/account`; // Or any other page

		const portalSession = await stripe.billingPortal.sessions.create({
			customer: stripeCustomerId,
			return_url: returnUrl,
		});

		return json({ url: portalSession.url });

	} catch (err: any) {
		console.error(`Stripe Customer Portal Error for user ${user.id}:`, err);
		if (err.status && typeof err.status === 'number' && err.body && typeof err.body.message === 'string') {
			throw err; // Re-throw SvelteKit errors
		}
		if (err.type && err.type.startsWith('Stripe')) {
			throw svelteKitError(err.statusCode || 500, `Stripe Error: ${err.message}`);
		}
		throw svelteKitError(500, `An unexpected error occurred: ${err.message}`);
	}
};