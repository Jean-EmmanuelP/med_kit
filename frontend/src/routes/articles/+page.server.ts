export async function load({ locals }) {
	const { session, user } = await locals.safeGetSession();

	if (!user || !session) {
		console.log('No user or session found, returning empty data');
		return {
			disciplines: [],
			error: 'Utilisateur non connecté.'
		};
	}

	const { data: disciplineData, error: disciplineError } = await locals.supabase
		.from('disciplines')
		.select('name');

	if (disciplineError) {
		console.error('Discipline fetch failed:', disciplineError.message);
		return {
			disciplines: [],
			error: disciplineError.message || 'Profil utilisateur non trouvé.'
		};
	}

	return {
		disciplines: disciplineData,
		error: null
	};
}
