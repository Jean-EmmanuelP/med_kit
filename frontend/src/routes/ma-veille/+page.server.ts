import type { PageServerLoad } from './$types';
import { supabase } from '$lib/supabase'; // Assurez-vous que ce fichier existe et est configuré correctement

export const load: PageServerLoad = async ({ locals }) => {
    console.log('=== Starting load function for /ma-veille ===');

    // Récupérer la session réelle via locals (fourni par SvelteKit avec un système d'authentification)
    const { session } = await locals.safeGetSession(); // Assurez-vous que cette méthode est configurée dans votre projet

    if (!session || !session.user) {
        console.log('No user or session found, returning empty data');
        return {
            articles: [],
            userDisciplines: [],
            error: 'Utilisateur non connecté.'
        };
    }

    const userId = session.user.id;
    console.log('User ID from session:', userId);

    // Récupérer les disciplines de l'utilisateur depuis une table user_disciplines
    const { data: userDisciplinesData, error: disciplinesError } = await supabase
        .from('user_disciplines') // Table hypothétique contenant les disciplines de l'utilisateur
        .select('discipline')
        .eq('user_id', userId);

    if (disciplinesError || !userDisciplinesData || userDisciplinesData.length === 0) {
        console.log('Error fetching disciplines or no disciplines found:', disciplinesError?.message);
        return {
            articles: [],
            userDisciplines: [],
            error: disciplinesError?.message || 'Aucune discipline choisie.'
        };
    }

    const userDisciplines = userDisciplinesData.map((d) => d.discipline);
    console.log('User disciplines:', userDisciplines);

    // Récupérer les articles liés aux disciplines de l'utilisateur
    const { data: articlesData, error: articlesError } = await supabase
        .from('articles') // Table hypothétique contenant les articles
        .select('id, title, journal, published_at, link, grade, discipline, added_at, is_article_of_the_day')
        .in('discipline', userDisciplines);

    if (articlesError || !articlesData) {
        console.log('Error fetching articles:', articlesError?.message);
        return {
            articles: [],
            userDisciplines,
            error: articlesError?.message || 'Erreur lors de la récupération des articles.'
        };
    }

    // Ajouter un article_id pour correspondre au front-end
    const formattedArticles = articlesData.map((article, index) => ({
        id: article.id,
        article_id: article.id, // Utiliser l'ID réel comme article_id
        title: article.title,
        journal: article.journal,
        published_at: article.published_at,
        link: article.link,
        grade: article.grade,
        discipline: article.discipline,
        added_at: article.added_at,
        is_article_of_the_day: article.is_article_of_the_day
    }));

    console.log('Returning data to client');
    return {
        articles: formattedArticles,
        userDisciplines,
        error: null
    };
};