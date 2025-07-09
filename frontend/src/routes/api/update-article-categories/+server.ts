import { error, json } from '@sveltejs/kit';
import type { RequestEvent } from './$types';

export async function POST({ request, locals }: RequestEvent) {
    const { session, supabase } = locals;
    const user = session?.user;

    if (!user) {
        console.error('[API UpdateCategories] Error: No user session found.');
        return json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Check if user is admin
    const { data: userProfile, error: profileError } = await supabase
        .from('user_profiles')
        .select('is_admin')
        .eq('id', user.id)
        .single();

    if (profileError || !userProfile?.is_admin) {
        console.error('[API UpdateCategories] Error: User is not admin.');
        return json({ error: 'Forbidden - Admin access required' }, { status: 403 });
    }

    try {
        const { article_id, discipline_ids, sub_discipline_ids, mode = 'replace' } = await request.json();

        if (!article_id) {
            return json({ error: 'Article ID is required' }, { status: 400 });
        }

        console.log(`[API UpdateCategories] User ${user.id}: Updating article ${article_id} categories`, {
            discipline_ids,
            sub_discipline_ids,
            mode
        });

        // Get current article categories if mode is 'add'
        let finalDisciplineIds = discipline_ids || [];
        let finalSubDisciplineIds = sub_discipline_ids || [];

        if (mode === 'add') {
            // CORRECTION: Faire deux requêtes distinctes pour les disciplines et sous-disciplines
            
            // 1. Obtenir les disciplines actuelles
            const { data: currentDisciplines, error: disciplineError } = await supabase
                .from('article_disciplines')
                .select('discipline_id')
                .eq('article_id', article_id);

            if (disciplineError) {
                console.error('[API UpdateCategories] Error fetching current disciplines:', disciplineError);
                throw disciplineError;
            }

            // 2. Obtenir les sous-disciplines actuelles
            const { data: currentSubDisciplines, error: subDisciplineError } = await supabase
                .from('article_sub_disciplines')
                .select('sub_discipline_id')
                .eq('article_id', article_id);

            if (subDisciplineError) {
                console.error('[API UpdateCategories] Error fetching current sub-disciplines:', subDisciplineError);
                throw subDisciplineError;
            }

            const currentDisciplineIds = currentDisciplines?.map(c => c.discipline_id) || [];
            const currentSubDisciplineIds = currentSubDisciplines?.map(c => c.sub_discipline_id) || [];

            // Merge with existing categories
            finalDisciplineIds = [...new Set([...currentDisciplineIds, ...finalDisciplineIds])];
            finalSubDisciplineIds = [...new Set([...currentSubDisciplineIds, ...finalSubDisciplineIds])];
        }

        // CORRECTION: Supprimer séparément les mappings de disciplines et sous-disciplines
        
        // 1. Supprimer les mappings de disciplines
        const { error: deleteDisciplineError } = await supabase
            .from('article_disciplines')
            .delete()
            .eq('article_id', article_id);

        if (deleteDisciplineError) {
            console.error('[API UpdateCategories] Error deleting existing discipline mappings:', deleteDisciplineError);
            throw deleteDisciplineError;
        }

        // 2. Supprimer les mappings de sous-disciplines
        const { error: deleteSubDisciplineError } = await supabase
            .from('article_sub_disciplines')
            .delete()
            .eq('article_id', article_id);

        if (deleteSubDisciplineError) {
            console.error('[API UpdateCategories] Error deleting existing sub-discipline mappings:', deleteSubDisciplineError);
            throw deleteSubDisciplineError;
        }

        // Préparer les nouveaux mappings
        const disciplineMappings = [];
        const subDisciplineMappings = [];

        // Ajouter les mappings de disciplines principales
        for (const disciplineId of finalDisciplineIds) {
            disciplineMappings.push({
                article_id: article_id,
                discipline_id: disciplineId
            });
        }

        // Ajouter les mappings de sous-disciplines
        for (const subDisciplineId of finalSubDisciplineIds) {
            subDisciplineMappings.push({
                article_id: article_id,
                sub_discipline_id: subDisciplineId
            });
        }

        // Insérer les nouveaux mappings de disciplines
        if (disciplineMappings.length > 0) {
            const { error: insertDisciplineError } = await supabase
                .from('article_disciplines')
                .insert(disciplineMappings);

            if (insertDisciplineError) {
                console.error('[API UpdateCategories] Error inserting discipline mappings:', insertDisciplineError);
                throw insertDisciplineError;
            }
        }

        // Insérer les nouveaux mappings de sous-disciplines
        if (subDisciplineMappings.length > 0) {
            const { error: insertSubDisciplineError } = await supabase
                .from('article_sub_disciplines')
                .insert(subDisciplineMappings);

            if (insertSubDisciplineError) {
                console.error('[API UpdateCategories] Error inserting sub-discipline mappings:', insertSubDisciplineError);
                throw insertSubDisciplineError;
            }
        }

        console.log(`[API UpdateCategories] Successfully updated categories for article ${article_id}`);
        
        return json({ 
            success: true, 
            message: 'Categories updated successfully',
            discipline_ids: finalDisciplineIds,
            sub_discipline_ids: finalSubDisciplineIds
        });

    } catch (err: any) {
        console.error('[API UpdateCategories] Error:', err);
        const message = err.message || 'Failed to update article categories';
        const status = err.status || 500;
        return json({ error: message }, { status });
    }
}