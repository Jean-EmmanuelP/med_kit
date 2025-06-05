// /routes/api/cancel-stripe-subscription/+server.ts

import { STRIPE_SECRET_KEY, SUPABASE_SERVICE_ROLE_KEY } from '$env/static/private';
import { PUBLIC_SUPABASE_URL as SUPABASE_URL } from '$env/static/public';
import { createClient, type SupabaseClient } from '@supabase/supabase-js';
import { json, error as svelteKitError } from '@sveltejs/kit';
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
console.log("STRIPE_SECRET_KEY", STRIPE_SECRET_KEY);
console.log("SUPABASE_URL", SUPABASE_URL);
console.log("SUPABASE_SERVICE_ROLE_KEY", SUPABASE_SERVICE_ROLE_KEY);

export const POST: RequestHandler = async ({ request, locals }) => {
	if (!stripe || !supabaseAdmin) {
		throw svelteKitError(500, 'Server configuration error. Please try again later.');
	}

	const { session, user } = await locals.safeGetSession();
	if (!session || !user) {
		throw svelteKitError(401, 'User not authenticated.');
	}

	let stripeSubscriptionIdFromRequest: string;
	try {
		const body = await request.json();
		stripeSubscriptionIdFromRequest = body.stripeSubscriptionId;
		if (!stripeSubscriptionIdFromRequest || typeof stripeSubscriptionIdFromRequest !== 'string') {
			throw new Error('stripeSubscriptionId is required and must be a string.');
		}
	} catch (e: any) {
		throw svelteKitError(400, `Invalid request body: ${e.message}`);
	}

	try {
		const { data: storedSubscription, error: dbFetchError } = await supabaseAdmin
			.from('user_profile_subscriptions')
			.select('id, user_profile_id, stripe_subscription_id, status, cancel_at_period_end')
			.eq('stripe_subscription_id', stripeSubscriptionIdFromRequest)
			.eq('user_profile_id', user.id)
            .order('current_period_end', { ascending: false })
            .limit(1)
            .maybeSingle();

		if (dbFetchError) {
			if (dbFetchError.code === 'PGRST116') {
				throw svelteKitError(403, 'Subscription not found or you do not have permission to modify it.');
			}
			throw svelteKitError(500, 'Could not retrieve subscription details.');
		}

		if (!storedSubscription) {
			throw svelteKitError(403, 'Subscription not found or access denied.');
		}

		if (storedSubscription.cancel_at_period_end || storedSubscription.status === 'canceled') {
			return json({
				message: 'This subscription is already canceled or pending cancellation at the end of the period.',
				subscription: storedSubscription,
			}, { status: 200 });
		}

		const updatedStripeSubscription = await stripe.subscriptions.update(
			stripeSubscriptionIdFromRequest,
			{
				cancel_at_period_end: true,
			}
		);

		const { data: updatedDbSubscription, error: dbUpdateError } = await supabaseAdmin
			.from('user_profile_subscriptions')
			.update({
				cancel_at_period_end: updatedStripeSubscription.cancel_at_period_end,
				status: updatedStripeSubscription.status,
			})
			.eq('stripe_subscription_id', stripeSubscriptionIdFromRequest)
			.select()
			.single();

		if (dbUpdateError) {
			throw svelteKitError(500, 'Subscription canceled with Stripe, but failed to update local records. Please contact support if issues persist.');
		}

		return json({
			message: 'Subscription successfully set to cancel at the end of the current billing period.',
			stripeResponse: updatedStripeSubscription,
			databaseRecord: updatedDbSubscription,
		}, { status: 200 });

	} catch (err: any) {
		if (err.status && typeof err.status === 'number' && err.body && typeof err.body.message === 'string') {
			throw err;
		}
		
		if (err.type && err.type.startsWith('Stripe')) {
			throw svelteKitError(err.statusCode || 400, `Stripe Error: ${err.message}`);
		}
		
		throw svelteKitError(500, `An unexpected error occurred: ${err.message}`);
	}
};