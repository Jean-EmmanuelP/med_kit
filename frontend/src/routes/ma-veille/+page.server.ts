// /ma-veille/+page.server.ts (V4 - Simplified)
import { redirect } from '@sveltejs/kit';
import { error } from '@sveltejs/kit';

export async function load({ locals }) {
	console.log('=== Starting load function for /ma-veille (V4 - Simplified) ===');

	const { session, user } = await locals.safeGetSession();

	if (!user || !session) {
		console.log('No user or session found, redirecting to login');
        throw redirect(303, '/login?redirect=/ma-veille');
	}

	try {
        // 1. Fetch distinct MAIN discipline names user is subscribed to
        console.log(`Fetching distinct subscribed discipline names for user: ${user.id}`);
        // Use RPC for potentially better performance on distinct join
        const { data: disciplineNamesData, error: disciplineNamesError } = await locals.supabase
            .rpc('get_user_subscribed_discipline_names', { p_user_id: user.id });

        if (disciplineNamesError) {
            console.error('Error fetching user subscribed discipline names via RPC:', disciplineNamesError);
            throw error(500, `Database error: ${disciplineNamesError.message}`);
        }

        // RPC returns array of records like { name: '...' }, sort them
        const userDisciplinesNames = (disciplineNamesData || [])
            .map((d: { name: string }) => d.name)
            .sort((a: string, b: string) => a.localeCompare(b, 'fr', { sensitivity: 'base' }));

        console.log('User Main Disciplines for Filter:', userDisciplinesNames);

        if (userDisciplinesNames.length === 0) {
             console.log('User has no subscriptions.');
             // Return empty list, page will show empty state
        }

        // 2. Fetch saved articles (same as before)
        console.log('Fetching saved articles for user ID:', user.id);
        const { data: savedArticlesData, error: savedArticlesError } = await locals.supabase
            .from('saved_articles') // Adjust table name if different
            .select('article_id')
            .eq('user_id', user.id);

        if (savedArticlesError) {
            console.error('Error fetching saved articles:', savedArticlesError);
            throw error(500, `Database error: ${savedArticlesError.message}`);
        }

        const savedArticleIds = savedArticlesData?.map((saved) => saved.article_id) || [];
        console.log('Mapped saved article IDs:', savedArticleIds);

        // 3. Return the necessary data for the page
        console.log('Returning data to /ma-veille page');
        return {
            // Pass the names for the filter dropdown
            userDisciplines: userDisciplinesNames,
            // Pass saved IDs for the ArticleListView component (if it uses them)
            savedArticleIds,
            // No need to pass initial subs or initial filter, ArticleListView handles it
            error: null
        };

    } catch (err) {
         console.error('Error in /ma-veille load function:', err);
         if (err && typeof err === 'object' && 'status' in err) throw err;
         throw error(500, 'Une erreur interne est survenue lors du chargement de votre veille.');
    }
}