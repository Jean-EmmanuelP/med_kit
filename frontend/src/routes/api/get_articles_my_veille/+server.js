import { json } from "@sveltejs/kit";

export async function GET({ url, locals: { supabase } }) {
    const specialty = url.searchParams.get('specialty');
    const offset = parseInt(url.searchParams.get('offset') || '0');
    
    const my_veille_articles = await supabase.rpc('get_all_articles', {
        discipline: specialty,
        p_offset: offset,
    });
    console.log(my_veille_articles);
    return json(my_veille_articles);
} 