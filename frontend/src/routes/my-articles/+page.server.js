// myArticles/+page.server.js
import { supabase } from '$lib/supabase';

export async function load({ locals }) {
  const { session, user } = await locals.safeGetSession();

  console.log('Session in myArticles:', session);
  console.log('User in myArticles:', user);

  if (!session || !user) {
    return { articles: [], error: 'Vous devez être connecté pour voir vos articles enregistrés.' };
  }

  // Fetch user profile to ensure userProfileStore can be populated client-side
  const { data: userProfile, error: profileError } = await supabase
    .from('user_profiles')
    .select('id, first_name, last_name, notification_frequency, disciplines, date_of_birth, education, status, specialty')
    .eq('id', user.id)
    .single();

  if (profileError || !userProfile) {
    console.error('Error fetching user profile:', profileError);
    return { articles: [], error: 'Erreur lors de la récupération du profil utilisateur.' };
  }

  // Récupérer les articles enregistrés par l’utilisateur
  const { data: savedData, error: savedError } = await supabase
    .from('saved_articles')
    .select(`
      article_id,
      articles (
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
      )
    `)
    .eq('user_id', user.id);

  if (savedError) {
    console.error('Error fetching saved articles:', savedError);
    return { articles: [], error: savedError.message };
  }

  // Formater les articles
  const formattedArticles = savedData.map(entry => ({
    ...entry.articles,
    disciplines: entry.articles.article_disciplines.map(ad => ad.disciplines.name)
  }));

  return {
    articles: formattedArticles,
    userProfile // Pass the user profile to the client
  };
}

export const actions = {
  removeSavedArticle: async ({ request, locals }) => {
    const { session, user } = await locals.safeGetSession();

    if (!session || !user) {
      return { success: false, error: 'Vous devez être connecté.' };
    }

    const formData = await request.formData();
    const articleId = formData.get('articleId');

    if (!articleId) {
      return { success: false, error: 'L’ID de l’article est requis.' };
    }

    const { error } = await supabase
      .from('saved_articles')
      .delete()
      .eq('user_id', user.id)
      .eq('article_id', parseInt(articleId));

    if (error) {
      console.error('Error removing saved article:', error);
      return { success: false, error: error.message };
    }

    return { success: true };
  }
};