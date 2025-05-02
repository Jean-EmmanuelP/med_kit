// src/routes/api/update-feedback-modal/+server.ts
import { error, json } from '@sveltejs/kit';
import type { RequestEvent } from './$types';

export async function POST({ locals: { supabase, safeGetSession } }: RequestEvent) {
	console.log("API: /api/update-feedback-modal called"); // Log start

	const { user } = await safeGetSession();
	if (!user) {
		console.error("API Error: Unauthorized attempt to update feedback timestamp.");
		throw error(401, 'Unauthorized');
	}
	const userId = user.id;
	console.log(`API: User ID: ${userId}`);

	try {
		// 1. Get the current feedback_modal timestamp for the user
		console.log(`API: Fetching current profile for user ${userId}...`);
		const { data: profileData, error: profileError } = await supabase
			.from('user_profiles')
			.select('feedback_modal')
			.eq('id', userId)
			.maybeSingle(); // Use maybeSingle as profile might not exist (though unlikely for logged-in user)

		if (profileError) {
			console.error(`API DB Error (Fetch Profile):`, profileError);
			throw error(500, `Database error fetching profile: ${profileError.message}`);
		}

		const currentTimestamp = profileData?.feedback_modal;
		console.log(`API: Current feedback_modal timestamp: ${currentTimestamp}`);

		// 2. Determine the new timestamp value
		let newTimestampValue;
		if (currentTimestamp === null || currentTimestamp === undefined) {
			// If NULL (first time showing), set it to 23 days ago
			// Supabase RPC or direct SQL string can be used. Direct string is simpler here.
            // Calculate the date 23 days ago in JS and format as ISO string
            const date23DaysAgo = new Date();
            date23DaysAgo.setDate(date23DaysAgo.getDate() - 23);
            newTimestampValue = date23DaysAgo.toISOString();
			console.log(`API: Timestamp was NULL. Setting new timestamp to 23 days ago: ${newTimestampValue}`);
		} else {
			// If not NULL, update it to the current time
			newTimestampValue = new Date().toISOString();
			console.log(`API: Timestamp exists. Setting new timestamp to now: ${newTimestampValue}`);
		}

		// 3. Update the user_profiles table
		console.log(`API: Updating feedback_modal for user ${userId} to ${newTimestampValue}`);
		const { error: updateError } = await supabase
			.from('user_profiles')
			.update({ feedback_modal: newTimestampValue })
			.eq('id', userId);

		if (updateError) {
			console.error(`API DB Error (Update Timestamp):`, updateError);
			throw error(500, `Database error updating timestamp: ${updateError.message}`);
		}

		console.log(`API: Timestamp update successful for user ${userId}.`);
		return json({ success: true, message: 'Timestamp updated' }, { status: 200 });

	} catch (err: any) {
		console.error("API Exception:", err);
		if (err.status) {
			throw err; // Re-throw SvelteKit errors
		}
		throw error(500, err.message || 'Failed to update feedback modal timestamp');
	}
}