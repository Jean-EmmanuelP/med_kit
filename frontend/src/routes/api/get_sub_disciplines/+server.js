// src/routes/api/get_sub_disciplines/+server.ts
import { error, json } from '@sveltejs/kit';

export const GET = async ({ url, locals: { supabase } }) => {
	const disciplineName = url.searchParams.get('disciplineName');

	if (!disciplineName) {
		throw error(400, 'Missing required query parameter: disciplineName');
	}

    const getDisciplineId = await supabase
        .from('disciplines')
        .select('id')
        .eq('name', disciplineName)
        .single();

    const disciplineId = getDisciplineId.data?.id;
    if (!disciplineId) {
        throw error(404, 'Discipline not found');
    }

	// Fetch sub_disciplines associated with the given discipline name
	const { data: subDisciplines, error: dbError } = await supabase
		.from('sub_disciplines')
		.select('id, name') // Select id and name
		.eq('discipline_id', disciplineId) // Filter by discipline_id
		.order('name', { ascending: true }); // Order alphabetically by name

	if (dbError) {
		console.error('Error fetching sub-disciplines:', dbError);
		throw error(500, 'Database error fetching sub-disciplines');
	}

	return json(subDisciplines || []); // Return array or empty array
};