// /ma-veille/+page.server.ts
import { DateTime } from 'luxon';

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
			articleOfTheDay: [],
			error: 'Utilisateur non connecté.'
		};
	}

	console.log('Fetching user profile for user ID:', user.id);
	const { data: userProfile, error: profileError } = await locals.supabase
		.from('user_profiles')
		.select('disciplines, notification_frequency')
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
			articleOfTheDay: [],
			error: profileError?.message || 'Profil utilisateur non trouvé.'
		};
	}

	let userDisciplines = userProfile.disciplines || [];
	const notificationFrequency = userProfile.notification_frequency || 'tous_les_jours'; // Changed to 'tous_les_jours' to match your schema
	console.log('User disciplines:', userDisciplines);
	console.log('Notification frequency:', notificationFrequency);

	if (userDisciplines.length === 0) {
		console.log('No disciplines found for user');
		return {
			recentArticles: [],
			olderArticles: [],
			userDisciplines: [],
			savedArticleIds: [],
			articleOfTheDay: [],
			error: 'Aucune discipline choisie.'
		};
	}

	// Fetch saved articles
	console.log('Fetching saved articles for user ID:', user.id);
	const { data: savedArticlesData, error: savedArticlesError } = await locals.supabase
		.from('saved_articles')
		.select('article_id')
		.eq('user_id', user.id);

	console.log('Saved articles data:', savedArticlesData);
	console.log('Saved articles error:', savedArticlesError);

	const savedArticleIds = savedArticlesData?.map((saved) => saved.article_id) || [];
	console.log('Mapped saved article IDs:', savedArticleIds);

	// Fetch articles sent today for each discipline
	const today = DateTime.now().startOf('day').toISO();
	console.log('Fetching articles sent today:', today);
	const { data: sentArticlesData, error: sentArticlesError } = await locals.supabase
		.from('user_sent_articles')
		.select(
			`
      article_id,
      sent_at,
      discipline,
      articles (
        id,
        title,
        content,
        published_at,
        link,
        grade,
        journal,
        article_disciplines(discipline_id, disciplines(name))
      )
    `
		)
		.eq('user_id', user.id)
		.gte('sent_at', today)
		.order('sent_at', { ascending: false });

	console.log('Sent articles data:', sentArticlesData);
	console.log('Sent articles error:', sentArticlesError);

	let articleOfTheDay = [];
	if (sentArticlesError || !sentArticlesData) {
		console.error('Sent articles fetch failed:', sentArticlesError?.message);
	} else {
		// Group articles by discipline for "article du jour"
		articleOfTheDay = userDisciplines
			.map((discipline) => {
				const articleForDiscipline =
					sentArticlesData
						.filter((sa) => sa.discipline === discipline)
						.map((sa) => ({
							...sa.articles,
							disciplines: sa.articles.article_disciplines?.map((ad) => ad.disciplines.name) || [],
							sent_at: sa.sent_at
						}))[0] || null;
				return articleForDiscipline;
			})
			.filter((a) => a !== null);
	}

	console.log('Articles of the day:', articleOfTheDay);

	// Fetch recent and older articles (last 2 and rest, excluding today's sent articles)
	const allSentArticleIds = sentArticlesData?.map((sa) => sa.article_id) || [];
	const recentArticleIds = allSentArticleIds
		.slice(-2)
		.filter((id) => !articleOfTheDay.some((a) => a.id === id));
	const olderArticleIds = allSentArticleIds
		.slice(0, -2)
		.filter((id) => !articleOfTheDay.some((a) => a.id === id));

	console.log('Recent article IDs:', recentArticleIds);
	console.log('Older article IDs:', olderArticleIds);

	const { data: recentArticlesData, error: recentArticlesError } = await locals.supabase
		.from('articles')
		.select(
			`
      id,
      title,
      content,
      published_at,
      link,
      grade,
      journal,
      article_disciplines(discipline_id, disciplines(name))
    `
		)
		.in('id', recentArticleIds)
		.order('published_at', { ascending: false });

	console.log('Recent articles data:', recentArticlesData);
	console.log('Recent articles error:', recentArticlesError);

	const recentArticles =
		recentArticlesData?.map((article) => ({
			...article,
			disciplines: article.article_disciplines?.map((ad) => ad.disciplines.name) || [],
			journal: article.journal
		})) || [];

	let olderArticles = [];
	if (olderArticleIds.length > 0) {
		const { data: olderArticlesData, error: olderArticlesError } = await locals.supabase
			.from('articles')
			.select(
				`
        id,
        title,
        content,
        published_at,
        link,
        grade,
        journal,
        article_disciplines(discipline_id, disciplines(name))
      `
			)
			.in('id', olderArticleIds)
			.order('published_at', { ascending: false });

		console.log('Older articles data:', olderArticlesData);
		console.log('Older articles error:', olderArticlesError);

		olderArticles =
			olderArticlesData?.map((article) => ({
				...article,
				disciplines: article.article_disciplines?.map((ad) => ad.disciplines.name) || [],
				journal: article.journal
			})) || [];
	}

	console.log('Returning data to client');

	userDisciplines = userDisciplines.sort((a, b) => {
		const disciplineA = a.toLowerCase();
		const disciplineB = b.toLowerCase();
		if (disciplineA < disciplineB) {
			return -1;
		}
		if (disciplineA > disciplineB) {
			return 1;
		}
		return 0;
	});
	return {
		recentArticles,
		olderArticles,
		userDisciplines,
		savedArticleIds,
		articleOfTheDay,
		notification_frequency: notificationFrequency,
		error: null
	};
}