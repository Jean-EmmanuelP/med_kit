// src/routes/api/update-profile-and-subscriptions/+server.ts
import { json } from '@sveltejs/kit';
import type { RequestEvent } from './$types';

interface Subscription {
	discipline_id: number;
	sub_discipline_id: number;
}

export async function POST({ request, locals }: RequestEvent) {
	const { session } = locals;
	if (!session?.user) {
		console.error("No session or user found");
		return json({ error: 'Unauthorized' }, { status: 401 });
	}

	try {
		const { profile, subscriptions } = await request.json();
		console.log("Received update request:", {
			userId: session.user.id,
			profile,
			subscriptions
		});

		// Validate the data
		if (!profile || !subscriptions) {
			console.error("Missing required data:", { profile, subscriptions });
			return json({ error: 'Missing required data' }, { status: 400 });
		}

		// Update user profile
		console.log("Updating user profile:", profile);
		const { error: profileError } = await locals.supabase
			.from('user_profiles')
			.update(profile)
			.eq('id', session.user.id);

		if (profileError) {
			console.error("Profile update error:", profileError);
			throw profileError;
		}

		// Update subscriptions
		console.log("Updating subscriptions:", subscriptions);
		// First, delete existing subscriptions
		const { error: deleteError } = await locals.supabase
			.from('user_subscriptions')
			.delete()
			.eq('user_id', session.user.id);

		if (deleteError) {
			console.error("Delete subscriptions error:", deleteError);
			throw deleteError;
		}

		// Then insert new subscriptions
		// Create a Set to track unique discipline_ids
		const disciplineIds = new Set(subscriptions.map((sub: Subscription) => sub.discipline_id));
		
		// Create subscription records including both sub-disciplines and main disciplines
		const subscriptionRecords = [
			// Add records for each sub-discipline
			...subscriptions.map((sub: Subscription) => ({
				user_id: session.user.id,
				discipline_id: sub.discipline_id,
				sub_discipline_id: sub.sub_discipline_id
			})),
			// Add records for main disciplines with null sub_discipline_id
			...Array.from(disciplineIds).map(disciplineId => ({
				user_id: session.user.id,
				discipline_id: disciplineId,
				sub_discipline_id: null
			}))
		];

		console.log("Inserting new subscriptions:", subscriptionRecords);
		const { error: insertError } = await locals.supabase
			.from('user_subscriptions')
			.insert(subscriptionRecords);

		if (insertError) {
			console.error("Insert subscriptions error:", insertError);
			throw insertError;
		}

		console.log("Update successful");
		return json({ success: true });
	} catch (error) {
		console.error("Update error:", error);
		return json({ error: 'Failed to update profile and subscriptions' }, { status: 500 });
	}
}