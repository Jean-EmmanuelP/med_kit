import { error } from '@sveltejs/kit';

/** @type {import('./$types').PageServerLoad} */
export async function load({ locals }) {
  try {
    const { data: disciplinesData, error: disciplinesError } = await locals.supabase
      .from('disciplines')
      .select('id, name');

    if (disciplinesError) {
      console.error('Erreur lors de la récupération des disciplines:', disciplinesError);
      throw error(500, 'Erreur serveur lors de la récupération des disciplines.');
    }

    if (!disciplinesData || disciplinesData.length === 0) {
      console.warn('Aucune discipline trouvée.');
      return { articles: [], specialties: [] };
    }

    const disciplines = disciplinesData;
    const specialties = disciplines.map((d) => d.name);

    const articlePromises = disciplines.map(discipline => {
      return locals.supabase
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
          article_disciplines!inner (
            discipline_id,
            disciplines (name)
          )
        `)
        .eq('article_disciplines.discipline_id', discipline.id)
        .order('created_at', { ascending: true })
        .limit(3)
        .then(({ data, error: articleError }) => {
           if (articleError) {
             console.error(`Erreur lors de la récupération des articles pour la discipline ${discipline.name} (ID: ${discipline.id}):`, articleError);
             return [];
           }
           const processedArticles = (data || []).map(article => ({
                ...article,
                disciplines: article.article_disciplines.map(ad => ad.disciplines.name)
           }));
           return processedArticles;
        });
    });
    const resultsPerDiscipline = await Promise.all(articlePromises);
    const combinedArticles = resultsPerDiscipline.flat();

    return {
      articles: combinedArticles,
      specialties: specialties
    };

  } catch (err) {
    // Handle potential errors from Promise.all or the initial disciplines fetch
    if (err.status && typeof err.status === 'number') {
        // It's likely a SvelteKit error object, re-throw it
        throw err;
    } else {
        // Otherwise, log and throw a generic 500 error
        console.error('Erreur inattendue dans la fonction load:', err);
        throw error(500, 'Erreur serveur inattendue.');
    }
  }
}