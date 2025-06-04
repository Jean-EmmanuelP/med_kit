// src/routes/favoris/+page.server.ts
import { checkUserSubscription } from '$lib/utils/subscriptionUtils';
import { error, redirect } from '@sveltejs/kit';

export const load = async ({ locals: { supabase, safeGetSession } }) => {
    const { user } = await safeGetSession();

    if (!user) {
        throw redirect(303, '/login?redirect=/favoris');
    }

    let { isActive, error: subError } = await checkUserSubscription(supabase, user?.id);

    if (subError) {
        isActive = false;
    }

    // --- Fetch distinct disciplines for liked articles ---
    const { data: disciplineData, error: dbError } = await supabase
        .from('article_likes')
        .select(`
            articles!inner (
                article_disciplines!inner (
                    disciplines!inner ( id, name )
                )
            )
        `)
        .eq('user_id', user.id); // Filter by the current user

    if (dbError) {
        console.error("Error fetching liked disciplines:", dbError);
        throw error(500, "Could not load disciplines for liked articles.");
    }

    // --- Process data to get unique, sorted disciplines ---
    const likedDisciplinesMap = new Map<number, { value: string; label: string }>();
    if (disciplineData) {
        for (const like of disciplineData) {
            // Navigate through the nested structure
            const discipline = like.articles?.article_disciplines[0]?.disciplines;
            if (discipline && !likedDisciplinesMap.has(discipline.id)) {
                likedDisciplinesMap.set(discipline.id, { value: discipline.name, label: discipline.name });
            }
        }
    }

    const likedFilters = Array.from(likedDisciplinesMap.values())
                              .sort((a, b) => a.label.localeCompare(b.label, 'fr', { sensitivity: 'base' }));

    console.log("Liked Filters for User:", likedFilters);

    return {
        isSubscribed: isActive,
        likedFilters: likedFilters
    };
};