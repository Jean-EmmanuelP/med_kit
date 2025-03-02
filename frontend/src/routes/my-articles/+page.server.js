import { supabase } from '$lib/supabase';

export async function load({ locals }) {
  const user = locals.user; // Remplacez par votre méthode d’authentification

  if (!user) {
    return { articles: [], error: 'Vous devez être connecté pour voir vos articles enregistrés.' };
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
        article_disciplines (
          discipline_id,
          disciplines (name)
        )
      )
    `)
    .eq('user_id', user.id);

  if (savedError) {
    return { articles: [], error: savedError.message };
  }

  // Formater les articles
  const formattedArticles = savedData.map(entry => ({
    ...entry.articles,
    disciplines: entry.articles.article_disciplines.map(ad => ad.disciplines.name)
  }));

  return { articles: formattedArticles };
}

export const actions = {
  removeSavedArticle: async ({ request, locals }) => {
    const formData = await request.formData();
    const articleId = formData.get('articleId');

    if (!articleId) {
      return { success: false, error: 'L’ID de l’article est requis.' };
    }

    const user = locals.user;
    if (!user) {
      return { success: false, error: 'Vous devez être connecté.' };
    }

    const { error } = await supabase
      .from('saved_articles')
      .delete()
      .eq('user_id', user.id)
      .eq('article_id', parseInt(articleId));

    if (error) {
      return { success: false, error: error.message };
    }

    return { success: true };
  }
};