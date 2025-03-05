// /ma-veille/+page.server.js
export async function load({ locals }) {
    const { session, user } = await locals.safeGetSession();
  
    console.log('Session in ma-veille:', session);
    console.log('User in ma-veille:', user);
  
    if (!user) {
      return {
        recentArticles: [],
        olderArticles: [],
        error: 'Utilisateur non connecté.',
      };
    }
  
    // Étape 1 : Récupérer le profil de l'utilisateur pour obtenir sent_article_ids
    const { data: userProfile, error: profileError } = await locals.supabase
      .from('user_profiles')
      .select('sent_article_ids')
      .eq('id', user.id)
      .single();
  
    if (profileError || !userProfile) {
      console.error('Erreur lors de la récupération du profil utilisateur:', profileError);
      return {
        recentArticles: [],
        olderArticles: [],
        error: profileError?.message || 'Profil utilisateur non trouvé.',
      };
    }
  
    const sentArticleIds = userProfile.sent_article_ids || [];
    if (sentArticleIds.length === 0) {
      return {
        recentArticles: [],
        olderArticles: [],
        error: 'Aucun article envoyé à cet utilisateur.',
      };
    }
  
    // Étape 2 : Trier les IDs pour obtenir les deux derniers (les plus récents) et les autres
    const recentArticleIds = sentArticleIds.slice(-2); // Deux derniers IDs
    const olderArticleIds = sentArticleIds.slice(0, -2); // Les autres IDs
  
    // Étape 3 : Récupérer les articles récents (deux derniers)
    const { data: recentArticlesData, error: recentArticlesError } = await locals.supabase
      .from('articles')
      .select(`
        id,
        title,
        content,
        author,
        published_at,
        link,
        grade,
        article_disciplines (
          discipline_id,
          disciplines (name)
        )
      `)
      .in('id', recentArticleIds)
      .order('published_at', { ascending: false });
  
    if (recentArticlesError) {
      console.error('Erreur lors de la récupération des articles récents:', recentArticlesError);
      return {
        recentArticles: [],
        olderArticles: [],
        error: recentArticlesError.message,
      };
    }
  
    // Formatter les articles récents
    const recentArticles = recentArticlesData.map((article) => ({
      ...article,
      disciplines: article.article_disciplines.map((ad) => ad.disciplines.name),
    }));
  
    // Étape 4 : Récupérer les articles plus anciens (si nécessaire)
    let olderArticles = [];
    if (olderArticleIds.length > 0) {
      const { data: olderArticlesData, error: olderArticlesError } = await locals.supabase
        .from('articles')
        .select(`
          id,
          title,
          content,
          author,
          published_at,
          link,
          grade,
          article_disciplines (
            discipline_id,
            disciplines (name)
          )
        `)
        .in('id', olderArticleIds)
        .order('published_at', { ascending: false });
  
      if (olderArticlesError) {
        console.error('Erreur lors de la récupération des articles plus anciens:', olderArticlesError);
        return {
          recentArticles,
          olderArticles: [],
          error: olderArticlesError.message,
        };
      }
  
      olderArticles = olderArticlesData.map((article) => ({
        ...article,
        disciplines: article.article_disciplines.map((ad) => ad.disciplines.name),
      }));
    }
  
    return {
      recentArticles,
      olderArticles,
      session,
      user,
    };
  }