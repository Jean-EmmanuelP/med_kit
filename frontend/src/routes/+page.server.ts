import { error } from '@sveltejs/kit';

/** @type {import('./$types').PageServerLoad} */
export async function load({ locals }) {
  try {
    // Récupérer les disciplines
    const { data: disciplinesData, error: disciplinesError } = await locals.supabase
      .from('disciplines')
      .select('id, name');

    if (disciplinesError) {
      console.error('Erreur lors de la récupération des disciplines:', disciplinesError);
      throw error(500, 'Erreur serveur');
    }

    const specialties = disciplinesData.map((d) => d.name);

    // Récupérer les articles avec leurs disciplines
    const { data: articlesData, error: articlesError } = await locals.supabase
      .from('articles')
      .select(`
        id,
        title,
        content,
        created_at,
        published_at,
        link,
        grade,
        journal,
        article_disciplines (
          discipline_id,
          disciplines (name)
        )
      `)
      .order('published_at', { ascending: false });

    if (articlesError) {
      console.error('Erreur lors de la récupération des articles:', articlesError);
      throw error(500, 'Erreur serveur');
    }

    // Grouper et limiter à 10 articles par discipline côté application
    const articlesByDiscipline = {};
    articlesData.forEach((article) => {
      const disciplineNames = article.article_disciplines.map((ad) => ad.disciplines.name);
      disciplineNames.forEach((disciplineName) => {
        if (!articlesByDiscipline[disciplineName]) {
          articlesByDiscipline[disciplineName] = [];
        }
        if (articlesByDiscipline[disciplineName].length < 3) {
          articlesByDiscipline[disciplineName].push({
            ...article,
            disciplines: disciplineNames
          });
        }
      });
    });

    // Convertir en un tableau plat d'articles avec la limite
    const limitedArticles = Object.values(articlesByDiscipline).flat();

    return {
      articles: limitedArticles,
      specialties
    };
  } catch (err) {
    console.error('Erreur inattendue:', err);
    throw error(500, 'Erreur serveur');
  }
}