// /ma-veille/+page.server.ts
export async function load({ locals }) {
	console.log('=== Starting load function for /ma-veille ===');
  
	const { session, user } = await locals.safeGetSession();
	console.log('Session from safeGetSession:', session);
	console.log('User from safeGetSession:', user);
  
	if (!user || !session) {
	  console.log('No user or session found, returning empty data');
	  return {
		recentArticles: [],
		olderArticles: [],
		userDisciplines: [],
		savedArticleIds: [],
		error: 'Utilisateur non connecté.',
	  };
	}
  
	console.log('Fetching user profile for user ID:', user.id);
	const { data: userProfile, error: profileError } = await locals.supabase
	  .from('user_profiles')
	  .select('disciplines, sent_article_ids')
	  .eq('id', user.id)
	  .single();
  
	console.log('User profile data:', userProfile);
	console.log('Profile error:', profileError);
  
	if (profileError || !userProfile) {
	  console.error('Profile fetch failed:', profileError?.message);
	  return {
		recentArticles: [],
		olderArticles: [],
		userDisciplines: [],
		savedArticleIds: [],
		error: profileError?.message || 'Profil utilisateur non trouvé.',
	  };
	}
  
	const userDisciplines = userProfile.disciplines || [];
	const sentArticleIds = userProfile.sent_article_ids || [];
	console.log('User disciplines:', userDisciplines);
	console.log('Sent article IDs:', sentArticleIds);
  
	if (userDisciplines.length === 0) {
	  console.log('No disciplines found for user');
	  return {
		recentArticles: [],
		olderArticles: [],
		userDisciplines: [],
		savedArticleIds: [],
		error: 'Aucune discipline choisie.',
	  };
	}
  
	if (sentArticleIds.length === 0) {
	  console.log('No sent articles found for user');
	  return {
		recentArticles: [],
		olderArticles: [],
		userDisciplines,
		savedArticleIds: [],
		error: 'Aucun article envoyé.',
	  };
	}
  
	console.log('Fetching saved articles for user ID:', user.id);
	const { data: savedArticlesData, error: savedArticlesError } = await locals.supabase
	  .from('saved_articles')
	  .select('article_id')
	  .eq('user_id', user.id);
  
	console.log('Saved articles data:', savedArticlesData);
	console.log('Saved articles error:', savedArticlesError);
  
	const savedArticleIds = savedArticlesData?.map((saved) => saved.article_id) || [];
	console.log('Mapped saved article IDs:', savedArticleIds);
  
	const recentArticleIds = sentArticleIds.slice(-2);
	const olderArticleIds = sentArticleIds.slice(0, -2);
	console.log('Recent article IDs:', recentArticleIds);
	console.log('Older article IDs:', olderArticleIds);
  
	console.log('Fetching recent articles');
	const { data: recentArticlesData, error: recentArticlesError } = await locals.supabase
	  .from('articles')
	  .select(`
		id,
		title,
		content,
		published_at,
		link,
		grade,
		journal,
		article_disciplines(discipline_id, disciplines(name))
	  `)
	  .in('id', recentArticleIds)
	  .order('published_at', { ascending: false });
  
	console.log('Recent articles data:', recentArticlesData);
	console.log('Recent articles error:', recentArticlesError);
  
	if (recentArticlesError || !recentArticlesData) {
	  console.error('Recent articles fetch failed:', recentArticlesError?.message);
	  return {
		recentArticles: [],
		olderArticles: [],
		userDisciplines,
		savedArticleIds,
		error: recentArticlesError?.message || 'Erreur lors du chargement des articles récents.',
	  };
	}
  
	const recentArticles = recentArticlesData.map((article) => ({
	  ...article,
	  disciplines: article.article_disciplines?.map((ad) => ad.disciplines.name) || [],
	  journal: article.journal,
	}));
	console.log('Processed recent articles:', recentArticles);
  
	let olderArticles = [];
	if (olderArticleIds.length > 0) {
	  console.log('Fetching older articles');
	  const { data: olderArticlesData, error: olderArticlesError } = await locals.supabase
		.from('articles')
		.select(`
		  id,
		  title,
		  content,
		  published_at,
		  link,
		  grade,
		  journal,
		  article_disciplines(discipline_id, disciplines(name))
		`)
		.in('id', olderArticleIds)
		.order('published_at', { ascending: false });
  
	  console.log('Older articles data:', olderArticlesData);
	  console.log('Older articles error:', olderArticlesError);
  
	  if (!olderArticlesError && olderArticlesData) {
		olderArticles = olderArticlesData.map((article) => ({
		  ...article,
		  disciplines: article.article_disciplines?.map((ad) => ad.disciplines.name) || [],
		  journal: article.journal,
		}));
		console.log('Processed older articles:', olderArticles);
	  }
	}
  
	console.log('Returning data to client');
	return { recentArticles, olderArticles, userDisciplines, savedArticleIds, session, user };
  }