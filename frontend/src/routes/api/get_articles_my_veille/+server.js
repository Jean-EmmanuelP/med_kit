import { json } from "@sveltejs/kit";

export async function GET({ url, locals: { supabase } }) {
    const specialty = url.searchParams.get('specialty');
    
    const my_veille_articles = await supabase.rpc('get_all_articles', {
        discipline: specialty,
        p_offset: 0,
    });

    return json(my_veille_articles);
} 