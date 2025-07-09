import { json } from '@sveltejs/kit';
import type { RequestEvent } from './$types';

export async function GET({ params, locals }: RequestEvent) {
    const { session, supabase } = locals;
    const user = session?.user;
    const articleId = params.id;

    if (!user) {
        console.error('[API GetArticleCategories] Error: No user session found.');
        return json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Check if user is admin
    const { data: userProfile, error: profileError } = await supabase
        .from('user_profiles')
        .select('is_admin')
        .eq('id', user.id)
        .single();

    if (profileError || !userProfile?.is_admin) {
        console.error('[API GetArticleCategories] Error: User is not admin.');
        return json({ error: 'Forbidden - Admin access required' }, { status: 403 });
    }

    if (!articleId) {
        return json({ error: 'Article ID is required' }, { status: 400 });
    }

    try {
        // CORRECTION: Faire deux requêtes distinctes pour les disciplines et sous-disciplines
        
        // 1. Obtenir les disciplines associées à l'article
        const { data: disciplineMappings, error: disciplineError } = await supabase
            .from('article_disciplines')
            .select('discipline_id')
            .eq('article_id', articleId);

        if (disciplineError) {
            console.error('[API GetArticleCategories] Error fetching discipline mappings:', disciplineError);
            throw disciplineError;
        }

        // 2. Obtenir les sous-disciplines associées à l'article
        const { data: subDisciplineMappings, error: subDisciplineError } = await supabase
            .from('article_sub_disciplines')
            .select('sub_discipline_id')
            .eq('article_id', articleId);

        if (subDisciplineError) {
            console.error('[API GetArticleCategories] Error fetching sub-discipline mappings:', subDisciplineError);
            throw subDisciplineError;
        }

        // Extraire les IDs uniques
        const disciplineIds = [...new Set(disciplineMappings?.map(m => m.discipline_id) || [])];
        const subDisciplineIds = [...new Set(subDisciplineMappings?.map(m => m.sub_discipline_id) || [])];

        // Fetch discipline names if we have discipline IDs
        let disciplines: {id: number, name: string}[] = [];
        if (disciplineIds.length > 0) {
            const { data: disciplineData, error: disciplineError } = await supabase
                .from('disciplines')
                .select('id, name')
                .in('id', disciplineIds);

            if (disciplineError) {
                console.error('[API GetArticleCategories] Error fetching disciplines:', disciplineError);
                throw disciplineError;
            }
            disciplines = disciplineData || [];
        }

        // Fetch sub-discipline names if we have sub-discipline IDs
        let subDisciplines: {id: number, name: string, discipline_id: number}[] = [];
        if (subDisciplineIds.length > 0) {
            const { data: subDisciplineData, error: subDisciplineError } = await supabase
                .from('sub_disciplines')
                .select('id, name, discipline_id')
                .in('id', subDisciplineIds);

            if (subDisciplineError) {
                console.error('[API GetArticleCategories] Error fetching sub-disciplines:', subDisciplineError);
                throw subDisciplineError;
            }
            subDisciplines = subDisciplineData || [];
        }

        console.log(`[API GetArticleCategories] Successfully retrieved categories for article ${articleId}`);
        
        return json({
            success: true,
            discipline_ids: disciplineIds,
            sub_discipline_ids: subDisciplineIds,
            disciplines,
            sub_disciplines: subDisciplines
        });

    } catch (err: unknown) {
        console.error('[API GetArticleCategories] Error:', err);
        const message = (err as Error)?.message || 'Failed to get article categories';
        const status = typeof err === 'object' && err !== null && 'status' in err ? (err as {status: number}).status : 500;
        return json({ error: message }, { status });
    }
}