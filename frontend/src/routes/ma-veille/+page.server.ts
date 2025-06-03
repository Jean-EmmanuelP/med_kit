import { checkUserSubscription } from '$lib/utils/subscriptionUtils';
import { error, redirect } from '@sveltejs/kit';

interface SubDisciplineInfo { id: number; name: string; }
interface DisciplineStructure {
    id: number;
    name: string;
    subscribed_sub_disciplines: SubDisciplineInfo[];
}

export async function load({ locals, url }) {
	const { session, user } = await locals.safeGetSession();

	if (!user || !session) {
		throw redirect(303, '/login?redirect=/ma-veille');
	}
    const { isActive, error: subError } = await checkUserSubscription(locals.supabase, user?.id);

    if (subError) {
        console.error('Subscription check failed:', subError);
        return {
            isSubscribed: false,
            initialMainFilterValue: null,
            initialSubFilterValue: null,
            userSubscriptionStructure: [],
            savedArticleIds: [],
            articleData: null,
            error: subError
        };
    }

    if (false && !isActive) {
        // TODO: change when subscription is implemented
        console.log('User is not subscribed, preparing non-subscribed page data');
        return {
            isSubscribed: false,
            initialMainFilterValue: null,
            initialSubFilterValue: null,
            userSubscriptionStructure: [],
            savedArticleIds: [],
            articleData: null,
            error: 'Utilisateur non abonné.'
        };
    }

	// --- Get URL Parameters ---
	let urlSubDisciplineName = url.searchParams.get('discipline');
	const urlId = urlSubDisciplineName?.includes('?id=') ? urlSubDisciplineName?.split('?id=')[1] || null : 0;
    urlSubDisciplineName = urlSubDisciplineName?.includes('?') ? urlSubDisciplineName?.split('?')[0] || null : urlSubDisciplineName;
    console.log(`URL parameters - discipline: ${urlSubDisciplineName}, id: ${urlId}`);

    let initialMainFilterValue: string | null = null;
    let initialSubFilterValue: string | null = null;

	try {
        // --- Fetch User Subscription Structure (Needed for dropdown options AND default values) ---
        const { data: userSubscriptionStructure, error: structureError } = await locals.supabase.rpc(
            'get_user_subscription_structure_with_subs',
            { p_user_id: user.id }
        );
        if (structureError) throw error(500, `DB Error fetching structure: ${structureError.message}`);
        const structuredData: DisciplineStructure[] = (userSubscriptionStructure || []);
         // Sort main disciplines alphabetically
        structuredData.sort((a, b) => a.name.localeCompare(b.name, 'fr', { sensitivity: 'base' }));
        // Sort sub-disciplines within each main discipline
        structuredData.forEach(d => d.subscribed_sub_disciplines?.sort((a, b) => a.name.localeCompare(b.name, 'fr', { sensitivity: 'base' })));

        // --- Determine Initial Dropdown States ---
        if (urlSubDisciplineName) {
            // --- A specific name (potentially sub) was provided in the URL ---
            console.log(`Attempting to find parent for sub-discipline: ${urlSubDisciplineName}`);
            // Query to find the sub-discipline and its parent
            const { data: parentInfo, error: parentError } = await locals.supabase
                .from('sub_disciplines')
                .select(`
                    name,
                    disciplines ( id, name )
                `)
                .eq('name', urlSubDisciplineName)
                .maybeSingle(); // Use maybeSingle as it might not exist

            if (parentError) {
                console.error(`DB Error finding parent for ${urlSubDisciplineName}:`, parentError);
                // Fallback to default if lookup fails
            } else if (parentInfo && parentInfo.disciplines) {
                 // Check if the user is actually subscribed to this found parent/sub combination
                 const parentId = parentInfo.disciplines.id;
                 const subName = parentInfo.name;
                 const isSubscribed = structuredData.some(main =>
                    main.id === parentId && main.subscribed_sub_disciplines?.some(sub => sub.name === subName)
                 );

                 if (isSubscribed) {
                    initialMainFilterValue = parentInfo.disciplines.name;
                    initialSubFilterValue = parentInfo.name; // The name from the URL param is the sub-filter
                    console.log(`Found parent "${initialMainFilterValue}" for sub "${initialSubFilterValue}". User is subscribed.`);
                 } else {
                    console.warn(`User is not subscribed to the discipline/sub-discipline found for URL param: ${urlSubDisciplineName}`);
                    // Fallback to default
                 }
            } else {
                 console.warn(`Sub-discipline "${urlSubDisciplineName}" not found in database.`);
                 // Fallback to default
            }
        }

        let articleData = null; // Initialize articleData to null
        if (urlId != 0) {
            const { data, error: articleError } = await locals.supabase
                .from('articles')
                .select(`title, id`)
                .eq('id', urlId)
                .single();
            if (articleError) {
                console.error(`DB Error fetching article: ${articleError.message}`);
            } else {
                articleData = data;
            }
        }

        // --- Set Default if Initial Values are Still Null ---
        if (initialMainFilterValue === null && structuredData.length > 0) {
             initialMainFilterValue = structuredData[0].name; // Default to first subscribed main discipline
             initialSubFilterValue = null; // Default sub to null (meaning "All")
             console.log(`Setting default initial filters: Main="${initialMainFilterValue}", Sub=NULL`);
        } else if (structuredData.length === 0) {
             console.log("User has no subscriptions, initial filters remain null.");
             // The page component should handle the empty state
        }

        // --- Fetch saved articles (remains the same) ---
        const { data: savedArticlesData, error: savedArticlesError } = await locals.supabase
            .from('saved_articles').select('article_id').eq('user_id', user.id);
        if (savedArticlesError) throw error(500, `DB Error fetching saved: ${savedArticlesError.message}`);
        const savedArticleIds = savedArticlesData?.map((saved) => saved.article_id) || [];

        return {
            isSubscribed: true,
            initialMainFilterValue,
            initialSubFilterValue,
            userSubscriptionStructure: structuredData,
            savedArticleIds,
            articleData,
            error: null
        };

    } catch (err) {
         console.error('Error in /ma-veille load function:', err);
         if (err && typeof err === 'object' && 'status' in err) throw err;
         throw error(500, 'Une erreur interne est survenue.');
    }
}