// src/routes/api/get_sub_disciplines/+server.js
import { error, json } from '@sveltejs/kit';

export const GET = async ({ url, locals: { supabase, safeGetSession } }) => {
	console.log('API: /api/get_sub_disciplines called');

    // 1. Get Query Parameters
    const disciplineName = url.searchParams.get('disciplineName');
    const mode = url.searchParams.get('mode') || 'user'; // Default to 'user' mode

    if (!disciplineName) {
		console.error('API Error: Missing disciplineName query parameter');
		throw error(400, 'Missing required query parameter: disciplineName');
	}
    console.log(`API: Requested discipline name: ${disciplineName}, Mode: ${mode}`);

    // 2. Authentication (Required ONLY for 'user' mode)
    const { user } = await safeGetSession();
    const userId = user?.id;
     console.log(`API: User authenticated: ${userId ?? 'No'}`);

    if (mode === 'user' && !userId) {
         console.error('API Error: Unauthorized access to get_sub_disciplines in user mode');
         // If user mode is explicitly requested but user isn't logged in, return error or empty?
         // Returning empty might be safer for the component.
         return json([]);
         // throw error(401, 'Authentication required for user-specific sub-disciplines.');
    }


	try {
        // 3. Find the ID of the requested Discipline
        const { data: disciplineData, error: disciplineError } = await supabase
            .from('disciplines')
            .select('id')
            .eq('name', disciplineName)
            .maybeSingle();

        if (disciplineError) throw error(500, `Database error: ${disciplineError.message}`);
        if (!disciplineData) {
             console.warn(`API Warn: Discipline not found: ${disciplineName}`);
             return json([]); // Return empty if the discipline name doesn't exist
        }
        const disciplineId = disciplineData.id;
        console.log(`API: Found discipline ID: ${disciplineId}`);

        // 4. Fetch sub-disciplines based on mode
        let subDisciplinesToReturn = [];

        if (mode === 'public' || !userId) {
            // --- Public Mode OR User Not Logged In: Return ALL sub-disciplines ---
            console.log(`API: Fetching ALL subs for discipline ${disciplineId} (Mode: ${mode}, User: ${userId ?? 'None'})`);
            const { data: allSubsData, error: allSubsError } = await supabase
                .from('sub_disciplines')
                .select('id, name')
                .eq('discipline_id', disciplineId)
                .order('name', { ascending: true });

            if (allSubsError) throw error(500, `DB error fetching all subs: ${allSubsError.message}`);
            subDisciplinesToReturn = allSubsData || [];

        } else {
            // --- User Mode AND User Logged In: Apply subscription logic ---
            console.log(`API: Fetching USER-SPECIFIC subs for user ${userId}, discipline ${disciplineId}`);
            const { data: userSubs, error: subsError } = await supabase
                .from('user_subscriptions')
                .select('sub_discipline_id')
                .eq('user_id', userId)
                .eq('discipline_id', disciplineId);

            if (subsError) throw error(500, `Database error: ${subsError.message}`);

            if (!userSubs || userSubs.length === 0) {
                console.warn(`API Warn: User ${userId} requested subs for discipline ${disciplineId} but has no subscriptions for it.`);
                return json([]); // Return empty as they are not subscribed
            }

            const hasSpecificSubs = userSubs.some(sub => sub.sub_discipline_id !== null);
            const subscribedToMain = userSubs.some(sub => sub.sub_discipline_id === null);

            if (hasSpecificSubs) {
                // Return ONLY specifically subscribed subs
                const specificSubIds = userSubs.map(sub => sub.sub_discipline_id).filter(id => id !== null);
                console.log(`API: User subscribed to specific subs. Fetching IDs: ${specificSubIds}`);
                if (specificSubIds.length > 0) {
                    const { data: specificSubsData, error: specificSubsError } = await supabase
                        .from('sub_disciplines').select('id, name').in('id', specificSubIds).order('name');
                    if (specificSubsError) throw error(500, `DB error fetching specific subs: ${specificSubsError.message}`);
                    subDisciplinesToReturn = specificSubsData || [];
                }
            } else if (subscribedToMain) {
                // Return ALL subs for the main discipline
                console.log(`API: User subscribed to main ${disciplineName}. Fetching ALL subs.`);
                 const { data: allSubsData, error: allSubsError } = await supabase
                    .from('sub_disciplines').select('id, name').eq('discipline_id', disciplineId).order('name');
                 if (allSubsError) throw error(500, `DB error fetching all subs: ${allSubsError.message}`);
                 subDisciplinesToReturn = allSubsData || [];
            }
            // If neither condition met (shouldn't happen if userSubs has data), returns empty.
        }

        console.log(`API: Returning ${subDisciplinesToReturn.length} sub-disciplines for ${disciplineName} (Mode: ${mode})`);
        return json(subDisciplinesToReturn);

	} catch (err) {
		 // Handle errors
         console.error('API Error in /api/get_sub_disciplines:', err);
         if (err && typeof err === 'object' && 'status' in err) throw err;
         throw error(500, 'An internal server error occurred.');
	}
};