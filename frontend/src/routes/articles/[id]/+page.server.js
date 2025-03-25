export async function load({ params, locals }) {
	const { id } = params;
	const { session, user } = await locals.safeGetSession();
  
	const { data: articleData, error: articleError } = await locals.supabase
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
		  article_disciplines (
			discipline_id,
			disciplines (name)
		  )
		`
	  )
	  .eq('id', id)
	  .single();
  
	if (articleError || !articleData) {
	  console.error('Error fetching article:', articleError);
	  return {
		article: null,
		comments: [],
		likesCount: 0,
		dislikesCount: 0,
		userHasLiked: false,
		userHasDisliked: false,
		isSaved: false,
		error: articleError?.message || 'Article non trouvé'
	  };
	}
  
	// Récupérer les commentaires associés à l'article avec les détails de l'utilisateur
	const { data: commentsData, error: commentsError } = await locals.supabase
	  .from('comments')
	  .select(
		`
		  id,
		  content,
		  created_at,
		  user_id,
		  user_profiles (id, first_name, last_name, status, specialty)
		`
	  )
	  .eq('article_id', id)
	  .order('created_at', { ascending: false });
  
	if (commentsError) {
	  console.error('Error fetching comments:', commentsError);
	  return {
		article: null,
		comments: [],
		likesCount: 0,
		dislikesCount: 0,
		userHasLiked: false,
		userHasDisliked: false,
		isSaved: false,
		error: commentsError.message
	  };
	}
  
	// Compter le nombre de likes pour l'article
	const { count: likesCount, error: likesCountError } = await locals.supabase
	  .from('article_likes')
	  .select('id', { count: 'exact' })
	  .eq('article_id', id);
  
	if (likesCountError) {
	  console.error('Error counting likes:', likesCountError);
	  return {
		article: null,
		comments: [],
		likesCount: 0,
		dislikesCount: 0,
		userHasLiked: false,
		userHasDisliked: false,
		isSaved: false,
		error: likesCountError.message
	  };
	}
  
	// Compter le nombre de dislikes pour l'article
	const { count: dislikesCount, error: dislikesCountError } = await locals.supabase
	  .from('article_dislikes')
	  .select('id', { count: 'exact' })
	  .eq('article_id', id);
  
	if (dislikesCountError) {
	  console.error('Error counting dislikes:', dislikesCountError);
	  return {
		article: null,
		comments: [],
		likesCount: 0,
		dislikesCount: 0,
		userHasLiked: false,
		userHasDisliked: false,
		isSaved: false,
		error: dislikesCountError.message
	  };
	}
  
	// Vérifier si l'utilisateur actuel a liké l'article
	let userHasLiked = false;
	if (user) {
	  const { data: likeData, error: likeError } = await locals.supabase
		.from('article_likes')
		.select('id')
		.eq('article_id', id)
		.eq('user_id', user.id)
		.single();
  
	  if (likeError && likeError.code !== 'PGRST116') {
		console.error('Error checking like:', likeError);
		return {
		  article: null,
		  comments: [],
		  likesCount: 0,
		  dislikesCount: 0,
		  userHasLiked: false,
		  userHasDisliked: false,
		  isSaved: false,
		  error: likeError.message
		};
	  }
	  userHasLiked = !!likeData;
	}
  
	// Vérifier si l'utilisateur actuel a disliké l'article
	let userHasDisliked = false;
	if (user) {
	  const { data: dislikeData, error: dislikeError } = await locals.supabase
		.from('article_dislikes')
		.select('id')
		.eq('article_id', id)
		.eq('user_id', user.id)
		.single();
  
	  if (dislikeError && dislikeError.code !== 'PGRST116') {
		console.error('Error checking dislike:', dislikeError);
		return {
		  article: null,
		  comments: [],
		  likesCount: 0,
		  dislikesCount: 0,
		  userHasLiked: false,
		  userHasDisliked: false,
		  isSaved: false,
		  error: dislikeError.message
		};
	  }
	  userHasDisliked = !!dislikeData;
	}
  
	// Vérifier si l'article est enregistré par l'utilisateur via saved_articles
	let isSaved = false;
	if (user) {
	  const { data: savedData, error: savedError } = await locals.supabase
		.from('saved_articles')
		.select('id')
		.eq('article_id', id)
		.eq('user_id', user.id)
		.single();
  
	  if (savedError && savedError.code !== 'PGRST116') {
		console.error('Error checking saved article:', savedError);
		return {
		  article: null,
		  comments: [],
		  likesCount: 0,
		  dislikesCount: 0,
		  userHasLiked: false,
		  userHasDisliked: false,
		  isSaved: false,
		  error: savedError.message
		};
	  }
	  isSaved = !!savedData;
	}
  
	// Formater les données pour inclure les disciplines et les commentaires
	const formattedArticle = {
	  ...articleData,
	  disciplines: articleData.article_disciplines.map((ad) => ad.disciplines.name),
	  journal: articleData.journal
	};
  
	const formattedComments = commentsData.map((comment) => ({
	  id: comment.id,
	  content: comment.content,
	  created_at: comment.created_at,
	  user_id: comment.user_id,
	  user: {
		id: comment.user_profiles.id,
		first_name: comment.user_profiles.first_name || 'Utilisateur',
		last_name: comment.user_profiles.last_name || 'Inconnu',
		status: comment.user_profiles.status,
		specialty: comment.user_profiles.specialty
	  }
	}));
  
	return {
	  article: formattedArticle,
	  comments: formattedComments,
	  likesCount,
	  dislikesCount,
	  userHasLiked,
	  userHasDisliked,
	  isSaved
	};
  }