// src/routes/api/dismiss-feature-notice/+server.ts
import { error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

export const POST: RequestHandler = async ({ locals: { supabase, safeGetSession } }) => {
	const { session } = await safeGetSession();

	if (!session?.user) {
		console.error("API Error: Unauthorized attempt to dismiss notice.");
		throw error(401, 'Authentication required');
	}

	const userId = session.user.id;
	console.log(`API: User ${userId} dismissing feature notice.`);

	try {
		const { error: updateError } = await supabase
			.from('user_profiles')
			.update({ has_seen_tooltip: true })
			.eq('id', userId);

		if (updateError) {
			console.error(`API DB Error: Failed to update has_seen_tooltip for user ${userId}`, updateError);
			throw error(500, 'Database error updating profile');
		}

		console.log(`API: Successfully marked notice as seen for user ${userId}.`);
		// Return 204 No Content for successful updates with no body
		return new Response(null, { status: 204 });

	} catch (err) {
		// Catch potential errors from the update or thrown errors
		console.error(`API Exception: Error dismissing notice for user ${userId}`, err);
		if (err instanceof Error && 'status' in err) {
			// Re-throw SvelteKit errors
			throw err;
		}
		// Throw generic server error
		throw error(500, 'Failed to dismiss notice');
	}
};