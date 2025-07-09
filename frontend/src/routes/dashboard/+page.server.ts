// Dashboard server-side loader - replicating articles page structure
import { checkUserSubscription } from '$lib/utils/subscriptionUtils';
import { redirect, error } from '@sveltejs/kit';

export async function load({ locals }) {
    const { session, user } = await locals.safeGetSession();

    // Check if user is logged in
    if (!user || !session) {
        console.log('No user or session found, redirecting to home');
        throw redirect(302, '/');
    }

    // Check if user is admin
    const { data: userProfile, error: profileError } = await locals.supabase
        .from('user_profiles')
        .select('is_admin')
        .eq('id', user.id)
        .single();

    if (profileError) {
        console.error('Error fetching user profile for admin check:', profileError);
        throw error(500, 'Erreur lors de la vérification des permissions');
    }

    if (!userProfile?.is_admin) {
        console.log('User is not admin, redirecting to home');
        throw redirect(302, '/');
    }

    const { isActive, error: subError } = await checkUserSubscription(locals.supabase, user?.id);

    if (subError) {
        console.error('Subscription check failed:', subError);
        return {
            isSubscribed: false,
            disciplines: [],
            error: subError
        };
    }

    if (false && !isActive) {
		// TODO: change when subscription is implemented
        console.log('User is not subscribed, preparing non-subscribed page data');
        return {
            isSubscribed: false,
            disciplines: [],
            error: 'Utilisateur non abonné.' // Message for the page
        };
    }

    const { data: disciplineData, error: disciplineError } = await locals.supabase
        .from('disciplines')
        .select('name');

    if (disciplineError) {
        console.error('Discipline fetch failed:', disciplineError.message);
        return {
            isSubscribed: true,
            disciplines: [],
            error: disciplineError.message || 'Erreur lors de la récupération des disciplines.'
        };
    }

    return {
        isSubscribed: true,
        disciplines: disciplineData || [],
        error: null
    };
} 