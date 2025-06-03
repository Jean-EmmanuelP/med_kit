// frontend/src/routes/api/create-subscription/+server.ts
import { env } from '$env/dynamic/private';
import { error, json, type RequestHandler } from '@sveltejs/kit';
import Stripe from 'stripe';

const stripeSecretKey = env.STRIPE_SECRET_KEY;
const monthlyPriceIdFromEnv = env.STRIPE_MONTHLY_PRICE_ID;
const yearlyPriceIdFromEnv = env.STRIPE_YEARLY_PRICE_ID;

if (!stripeSecretKey || !monthlyPriceIdFromEnv || !yearlyPriceIdFromEnv) {
	console.error(
		'CRITICAL SERVER ERROR: Stripe environment variables (secret key or price IDs) are not set.'
	);
}

const stripe = new Stripe(stripeSecretKey!, {
	apiVersion: '2023-10-16'
});

export const POST: RequestHandler = async ({ request, locals }) => {
	if (!stripeSecretKey || !monthlyPriceIdFromEnv || !yearlyPriceIdFromEnv) {
		console.error('API Call Error: Stripe server configuration is incomplete.');
		throw error(500, 'Server configuration error for payments.');
	}

	const { user, session } = await locals.safeGetSession();

	if (!session || !user || !user.email) {
		console.warn('API Call Error: User not authenticated or email missing.');
		throw error(401, 'Authentication required and user email must be available.');
	}

	let planIdentifier: 'monthly' | 'yearly';
	try {
		const body = await request.json();
		planIdentifier = body.planIdentifier;
		if (planIdentifier !== 'monthly' && planIdentifier !== 'yearly') {
			throw new Error('Invalid plan identifier.');
		}
	} catch (e) {
		console.error('API Call Error: Invalid request body or planIdentifier.', e);
		throw error(400, 'Invalid request data. Please provide a "planIdentifier" as "monthly" or "yearly".');
	}

	const priceId = planIdentifier === 'monthly' ? monthlyPriceIdFromEnv : yearlyPriceIdFromEnv;

	try {
		let stripeCustomerId: string | null = null;

		// Attempt to fetch the user's profile, including stripe_customer_id
		const { data: userProfile, error: profileFetchError } = await locals.supabase
			.from('user_profiles')
			.select('stripe_customer_id, first_name, last_name') // Ensure these columns exist
			.eq('id', user.id)
			.single(); // Use .single() as there should be one profile per user

		// Handle profile fetch errors more gracefully
		if (profileFetchError && profileFetchError.code !== 'PGRST116') { // PGRST116 means "0 rows" which is okay if profile not fully created yet
			console.error(`API DB Error: Could not fetch user profile for user ${user.id}. Error:`, profileFetchError);
			throw error(500, `Database error fetching user profile: ${profileFetchError.message}`);
		}
		
		if (userProfile?.stripe_customer_id) {
			stripeCustomerId = userProfile.stripe_customer_id;
			console.log(`API Info: Found existing Stripe Customer ID: ${stripeCustomerId} for user ${user.id}`);
		} else {
			console.log(`API Info: No Stripe Customer ID found for user ${user.id}. Creating new Stripe customer.`);
			const customerCreateParams: Stripe.CustomerCreateParams = {
				email: user.email,
				// Use names from profile if available, otherwise default to email for name
				name: `${userProfile?.first_name || ''} ${userProfile?.last_name || ''}`.trim() || user.email,
				metadata: {
					supabase_user_id: user.id // Link Stripe customer to your Supabase user ID
				}
			};
			const customer = await stripe.customers.create(customerCreateParams);
			stripeCustomerId = customer.id;
			console.log(`API Info: Created new Stripe Customer ID: ${stripeCustomerId} for user ${user.id}`);

			// Now, update the user_profiles table with the new stripe_customer_id
			// This assumes the user_profiles record was either already there or we are okay with it failing if not.
			// For a robust signup, profile creation should be guaranteed before this point.
			const { error: profileUpdateError } = await locals.supabase
				.from('user_profiles')
				.update({ stripe_customer_id: stripeCustomerId })
				.eq('id', user.id);

			if (profileUpdateError) {
				console.error(`API DB Error: Could not update user profile for user ${user.id} with Stripe Customer ID ${stripeCustomerId}. Error:`, profileUpdateError);
				// This is a critical error if the profile exists but couldn't be updated.
                // If the profile didn't exist, it's also an issue with your user creation flow.
				throw error(500, `Failed to save Stripe customer reference: ${profileUpdateError.message}`);
			}
            console.log(`API Info: Successfully updated profile for user ${user.id} with Stripe Customer ID.`);
		}

		if (!stripeCustomerId) {
			console.error(`API Logic Error: Stripe Customer ID is unexpectedly null for user ${user.id} after get/create attempt.`);
			throw error(500, 'Failed to obtain a Stripe Customer ID for the user.');
		}

		// Create the Stripe Subscription
		console.log(`API Info: Creating Stripe subscription for customer ${stripeCustomerId} with price ${priceId}`);
		const subscription = await stripe.subscriptions.create({
			customer: stripeCustomerId,
			items: [{ price: priceId }],
			payment_behavior: 'default_incomplete',
			payment_settings: {
				save_default_payment_method: 'on_subscription'
			},
			expand: ['latest_invoice.payment_intent'],
			metadata: {
				supabase_user_id: user.id,
				plan_identifier: planIdentifier // Storing the plan type can be useful
			}
		});

		if (
			!subscription.latest_invoice ||
			typeof subscription.latest_invoice === 'string' || // Type guard for expanded object
			!subscription.latest_invoice.payment_intent ||
			typeof subscription.latest_invoice.payment_intent === 'string' || // Type guard
			!subscription.latest_invoice.payment_intent.client_secret
		) {
			console.error('API Stripe Error: Could not retrieve client_secret from created subscription. Subscription object:', JSON.stringify(subscription, null, 2));
			throw error(500, 'Failed to get payment details from the Stripe subscription. The subscription might have been created without a pending payment.');
		}
		
		const clientSecret = subscription.latest_invoice.payment_intent.client_secret;
		const createdSubscriptionId = subscription.id;

		console.log(`API Success: Subscription ${createdSubscriptionId} created for user ${user.id}. Client Secret ready.`);
		return json({
			subscriptionId: createdSubscriptionId,
			clientSecret: clientSecret
		});

	} catch (e: any) {
		console.error(`API Stripe/DB Call Error for user ${user.id}:`, e);
		if (e instanceof Stripe.errors.StripeError) {
			throw error(e.statusCode || 500, `Stripe Error: ${e.message}`);
		}
		if (e.status && typeof e.status === 'number') {
			throw e;
		}
		throw error(500, `Server error processing subscription: ${e.message || 'An unknown error occurred'}`);
	}
};