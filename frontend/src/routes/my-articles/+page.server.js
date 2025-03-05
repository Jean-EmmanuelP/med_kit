// myArticles/+page.server.ts
import { redirect } from '@sveltejs/kit';

export async function load({ locals }) {
  const { session, user } = await locals.safeGetSession();

  console.log('Session in myArticles:', session);
  console.log('User in myArticles:', user);

  if (!session || !user) {
    throw redirect(302, '/login');
  }

  // Fetch user profile to ensure userProfileStore can be populated client-side
  const { data: userProfile, error: profileError } = await locals.supabase
    .from('user_profiles')
    .select('id, first_name, last_name, notification_frequency, disciplines, date_of_birth, status, specialty')
    .eq('id', user.id)
    .single();

  if (profileError || !userProfile) {
    console.error('Error fetching user profile:', profileError);
    return { articles: [], error: 'Erreur lors de la récupération du profil utilisateur.' };
  }

  // Récupérer les articles enregistrés par l’utilisateur
  const { data: savedData, error: savedError } = await locals.supabase
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
    disciplines: entry.articles.article_disciplines.map(ad => ad.disciplines.name),
  }));

  return {
    articles: formattedArticles,
    userProfile,
    session,
    user,
  };
}