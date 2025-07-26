// src/routes/api/get_articles_my_veille/+server.ts
import { error, json } from "@sveltejs/kit";

export const GET = async ({ url, locals: { supabase, safeGetSession } }) => {
    // --- Read parameters ---
    const specialty = url.searchParams.get('specialty'); // Might be empty or "__ALL__" if sent from frontend
    const subDiscipline = url.searchParams.get('subDiscipline');
    const offset = parseInt(url.searchParams.get('offset') || '0');
    const search = url.searchParams.get('search');
    const filterByUserSubs = url.searchParams.get('filterByUserSubs') === 'true';
    const isRecommandation = url.searchParams.get('isRecommandation') === 'true';
    const { user } = await safeGetSession();
    const userId = user?.id ?? null;

    // Treat empty specialty as NULL for the RPC call
    const disciplineNameToRPC = (!specialty || specialty === '__ALL__') ? null : specialty; // <<< Handle "All"

    // Sub-discipline only makes sense if a main discipline is selected
    const subDisciplineToRPC = disciplineNameToRPC ? (subDiscipline || null) : null; // <<< Nullify sub if discipline is null

    const { data: articlesData, error: rpcError } = await supabase.rpc(
        'get_all_articles_sub_disciplines',
        {
            p_discipline_name: disciplineNameToRPC, // Pass null if "All"
            p_sub_discipline_name: subDisciplineToRPC,
            p_offset: offset,
            p_search_term: search || null,
            p_user_id: userId,
            p_filter_by_user_subs: filterByUserSubs,
            p_only_recommendations: isRecommandation
        }
    );

    if (rpcError) {
        console.error('Error calling RPC get_all_articles_sub_disciplines:', rpcError);
        throw error(500, `Database RPC error: ${rpcError.message}`);
    }

    return json({ data: articlesData || [], error: null });
}