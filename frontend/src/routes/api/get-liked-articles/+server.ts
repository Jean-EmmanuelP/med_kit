// src/routes/api/get-liked-articles/+server.ts
import { error, json } from "@sveltejs/kit";

export const GET = async ({ url, locals: { supabase, safeGetSession } }) => {
    // --- Get User ID (Required) ---
    const { user } = await safeGetSession();
    if (!user) {
        throw error(401, 'Unauthorized');
    }
    const userId = user.id;

    // --- Read parameters ---
    const offset = parseInt(url.searchParams.get('offset') || '0');
    const search = url.searchParams.get('search');
    const specialty = url.searchParams.get('specialty');        // <<< NEW: Discipline filter
    const subDiscipline = url.searchParams.get('subDiscipline'); // <<< NEW: Sub-discipline filter

    // Treat empty specialty as NULL for the RPC call
    const disciplineNameToRPC = (!specialty || specialty === '__ALL__') ? null : specialty; // <<< Handle "All"
    const subDisciplineToRPC = disciplineNameToRPC ? (subDiscipline || null) : null; // <<< Nullify sub if discipline is null

    // --- Call the UPDATED RPC function ---
    console.log(`Calling RPC get_liked_articles with: user=${userId}, discipline=${disciplineNameToRPC}, subDiscipline=${subDisciplineToRPC}, offset=${offset}, search=${search || null}`);

    const { data: articlesData, error: rpcError } = await supabase.rpc(
        'get_liked_articles', // Still calling the same named RPC, but it's the *updated* version
        {
            p_user_id: userId,
            p_discipline_name: disciplineNameToRPC, // Pass null if "All"
            p_sub_discipline_name: subDisciplineToRPC,
            p_offset: offset,
            p_search_term: search || null
        }
    );

    // --- Handle RPC errors ---
    if (rpcError) {
         console.error('Error calling RPC get_liked_articles:', rpcError);
         throw error(500, `Database RPC error: ${rpcError.message}`);
    }

    // --- Return the data ---
    console.log('RPC Response Data (Liked Articles):', articlesData);
    return json({
        data: articlesData || [],
        error: null
    });
}