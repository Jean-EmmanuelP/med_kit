// In your +page.server.ts
import { checkUserSubscription } from '$lib/utils/subscriptionUtils';

export async function load({ locals }) {
    const { session, user } = await locals.safeGetSession();

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
    
    if (!user || !session) {
        console.log('No user or session found, returning empty data');
        return {
            isSubscribed: false,
            disciplines: [],
            error: 'Utilisateur non connecté.'
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