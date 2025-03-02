import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ locals: { safeGetSession }, cookies }) => {
	const { session } = await safeGetSession();
	const userProfileCookie = cookies.get('userProfile');

	return {
		session,
		cookies: cookies.getAll(),
		userInformation: userProfileCookie ? JSON.parse(userProfileCookie) : null
	};
};
