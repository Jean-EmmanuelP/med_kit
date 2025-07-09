// API endpoint to fetch a single article by ID
import { error, json } from '@sveltejs/kit';

export const GET = async ({ params, locals: { supabase, safeGetSession } }) => {
	// 1. Check Authentication
	const { user } = await safeGetSession();
	if (!user) {
		throw error(401, 'Unauthorized');
	}

	// 2. Get Article ID from params
	const { id } = params;
	if (!id || isNaN(Number(id))) {
		throw error(400, 'Invalid article ID');
	}

	const articleId = Number(id);

	// 3. Fetch article from database
	const { data: articleData, error: articleError } = await supabase
		.from('articles')
		.select(`
			id,
			title,
			content,
			published_at,
			journal,
			grade,
			link,
			is_recommandation,
			article_disciplines (
				discipline_id,
				disciplines (name)
			)
		`)
		.eq('id', articleId)
		.single();

	if (articleError || !articleData) {
		console.error('Error fetching article:', articleError);
		throw error(404, 'Article not found');
	}

	// 4. Format article data
	const formattedArticle = {
		...articleData,
		disciplines: articleData.article_disciplines.map((ad: any) => ad.disciplines.name)
	};

	// 5. Return article data
	return json(formattedArticle);
}; 