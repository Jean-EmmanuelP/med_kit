// /routes/account/+page.server.js
import { redirect } from '@sveltejs/kit';
import { error } from '@sveltejs/kit'; // Import error

export async function load({ locals }) {
	const { session, user } = await locals.safeGetSession();

	// console.log('Session in account load:', session);
	// console.log('User in account load:', user);

	if (!session || !user) {
		console.log('No session/user in account load, redirecting');
		throw redirect(302, '/login?redirect=/account');
	}

	try {
		// 1. Fetch user profile (excluding the old 'disciplines' column)
		const { data: userProfile, error: profileError } = await locals.supabase
			.from('user_profiles')
			.select('id, first_name, last_name, email, notification_frequency, date_of_birth, status, specialty') // Removed 'disciplines'
			.eq('id', user.id)
			.single();

		if (profileError) throw profileError; // Throw error to be caught below
		if (!userProfile) throw error(404, 'Profil utilisateur non trouvé.');

		// 2. Fetch all disciplines with their sub-disciplines
		const { data: allDisciplinesData, error: disciplinesError } = await locals.supabase
			.from('disciplines')
			.select(`
                id,
                name,
                sub_disciplines ( id, name )
            `)
			.order('name', { ascending: true }) // Order main disciplines
			.order('name', { referencedTable: 'sub_disciplines', ascending: true }); // Order sub-disciplines

		if (disciplinesError) throw disciplinesError;

		// Structure the data for the frontend
		const allDisciplines = allDisciplinesData || [];

		// 3. Fetch user's current subscriptions
		const { data: userSubsData, error: subsError } = await locals.supabase
			.from('user_subscriptions')
			.select('discipline_id, sub_discipline_id')
			.eq('user_id', user.id);

		if (subsError) throw subsError;

		// Convert subscriptions to a format easy for the frontend to check (e.g., Set of strings)
		const userSubscriptions = new Set();
		(userSubsData || []).forEach(sub => {
			if (sub.sub_discipline_id) {
				userSubscriptions.add(`s:${sub.sub_discipline_id}`); // Mark sub-disciplines with 's:'
			} else {
				userSubscriptions.add(`d:${sub.discipline_id}`); // Mark main disciplines with 'd:'
			}
		});

		// 4. Get status options from i18n data (if possible server-side, else hardcode)
        //    We'll hardcode them here for simplicity, assuming i18n is client-side focused
        const statusOptions = [
             "Pr", "Dr", "Interne", "Étudiant", "Médecine", "Professeur de médecine",
             "Docteur en médecine", "Interne en médecine", "Etudiant en médecine",
             "Diététicien(ne)-nutritionniste", "Infirmier(ère)", "Kinésithérapeute",
             "Pharmaciens", "Professions dentaires", "Psychologue", "Sage-femme", "Autres"
        ];
        const notificationOptions = [
            { value: 'tous_les_jours', label: 'Tous les jours' },
            { value: 'tous_les_2_jours', label: 'Tous les 2 jours' },
            { value: 'tous_les_3_jours', label: 'Tous les 3 jours' },
            { value: '1_fois_par_semaine', label: '1 fois par semaine' },
            { value: 'tous_les_15_jours', label: 'Tous les 15 jours' },
            { value: '1_fois_par_mois', label: '1 fois par mois' }
        ];

		return {
            userProfile,          // Basic profile data
            allDisciplines,       // Full hierarchy for UI [{id, name, sub_disciplines: [{id, name}]}]
            userSubscriptions: Array.from(userSubscriptions), // Pass the Set as an array for serialization ['d:1', 's:5', ...]
            statusOptions,        // List of statuses for dropdown
            notificationOptions,  // List of frequencies for dropdown
			session, // Pass session if needed by layout/page
			user,    // Pass user if needed by layout/page
		};

	} catch (err) {
		console.error('Error loading account data:', err);
		// Check if it's a Supabase error with a message
		if (err && typeof err === 'object' && 'message' in err) {
            throw error(500, `Erreur serveur: ${err.message}`);
        }
        // Check if it's a SvelteKit error object
        if (err && typeof err === 'object' && 'status' in err) {
             throw err; // Re-throw SvelteKit error
        }
		// Throw generic error otherwise
		throw error(500, 'Erreur lors du chargement des données du compte.');
	}
}

// No Actions needed here anymore, we will use an API route
export const actions = undefined;