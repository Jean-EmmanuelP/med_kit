// src/routes/api/get_articles_my_veille/+server.ts
import { error, json } from "@sveltejs/kit";

export const GET = async ({ url, locals: { supabase } }) => {
    // --- Read parameters ---
    const specialty = url.searchParams.get('specialty');
    const subDiscipline = url.searchParams.get('subDiscipline');
    const offset = parseInt(url.searchParams.get('offset') || '0');
    const search = url.searchParams.get('search'); // <<< Read search term
    // const userId = url.searchParams.get('userId');

    if (!specialty) {
         throw error(400, 'Missing required query parameter: specialty');
    }

    // --- Call the NEW RPC function ---
    console.log(`Calling RPC get_all_articles_sub_disciplines with: discipline=${specialty}, sub_discipline=${subDiscipline || null}, offset=${offset}, search=${search || null}`);

    const { data: articlesData, error: rpcError } = await supabase.rpc(
        'get_all_articles_sub_disciplines', // RPC name
        {
            p_discipline_name: specialty,
            p_sub_discipline_name: subDiscipline || null,
            p_offset: offset,
            p_search_term: search || null // <<< Pass search term (or null)
            // p_user_id: userId || null
        }
    );

    // --- Handle RPC errors ---
    if (rpcError) {
         console.error('Error calling RPC get_all_articles_sub_disciplines:', rpcError);
         throw error(500, `Database RPC error: ${rpcError.message}`);
    }

    // --- Return the data ---
    console.log('RPC Response Data:', articlesData);
    return json({
        data: articlesData || [],
        error: null
    });
}