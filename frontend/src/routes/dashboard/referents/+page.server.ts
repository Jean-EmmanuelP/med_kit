import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ locals }) => {
	// Check if user is authenticated
	const { session, user } = await locals.safeGetSession();
	if (!user || !session) {
		throw redirect(302, '/login');
	}

	// Check if user has admin privileges
	const { data: userProfile, error: profileError } = await locals.supabase
		.from('user_profiles')
		.select('has_all_power, is_admin')
		.eq('id', user.id)
		.single();

	if (profileError) {
		console.error('Error fetching user profile for admin check:', profileError);
		throw redirect(302, '/dashboard');
	}

	if (!userProfile?.has_all_power && !userProfile?.is_admin) {
		throw redirect(302, '/dashboard');
	}

	return {
		data: {
			userProfile
		}
	};
}; 