// /routes/account/+page.server.js
import { checkUserSubscription } from '$lib/utils/subscriptionUtils';
import { error, redirect } from '@sveltejs/kit';

export async function load({ locals }) {
	const { session, user } = await locals.safeGetSession();

	if (!session || !user) {
		console.log('No session/user in account load, redirecting');
		throw redirect(302, '/login?redirect=/account');
	}

    const { activeSubscription, error: subError } = await checkUserSubscription(locals.supabase, user?.id, true);

	if (subError) {
		console.error('Error fetching subscription:', subError);
		throw error(500, `Erreur serveur: ${subError.message}`);
	}

	try {
		// 1. Fetch user profile (excluding the old 'minimum_grade_notification')
		const { data: userProfile, error: profileError } = await locals.supabase
			.from('user_profiles')
			.select('id, first_name, last_name, email, notification_frequency, date_of_birth, status, specialty, has_seen_tooltip, feedback_modal')
			.eq('id', user.id)
			.single();

		if (profileError) throw profileError;
		if (!userProfile) throw error(404, 'Profil utilisateur non trouvé.');

		// 2. Fetch all disciplines with their sub-disciplines (remains the same)
		const { data: allDisciplinesData, error: disciplinesError } = await locals.supabase
			.from('disciplines')
			.select(`
                id,
                name,
                sub_disciplines ( id, name )
            `)
			.order('name', { ascending: true })
			.order('name', { referencedTable: 'sub_disciplines', ascending: true });

		if (disciplinesError) throw disciplinesError;
		const allDisciplines = allDisciplinesData || [];

		// 3. Fetch user's current subscriptions (main/sub disciplines - remains the same)
		const { data: userSubsData, error: subsError } = await locals.supabase
			.from('user_subscriptions')
			.select('discipline_id, sub_discipline_id')
			.eq('user_id', user.id);

		if (subsError) throw subsError;
		const userSubscriptions = new Set();
		(userSubsData || []).forEach(sub => {
			if (sub.sub_discipline_id) {
				userSubscriptions.add(`s:${sub.sub_discipline_id}`);
			} else {
				userSubscriptions.add(`d:${sub.discipline_id}`);
			}
		});

		// Debug logs for subscriptions
		console.log('=== SERVER: USER SUBSCRIPTIONS ===');
		console.log('userSubsData from DB:', userSubsData);
		console.log('userSubscriptions Set:', Array.from(userSubscriptions));

        // **** NEW: Fetch user's selected grades ****
        const { data: userGradesData, error: gradesError } = await locals.supabase
            .from('user_grade_preferences')
            .select('grade')
            .eq('user_id', user.id);

        if (gradesError) throw gradesError;
        const userGradePreferences = (userGradesData || []).map(g => g.grade); // -> ['A', 'C'] etc.
        
        // Debug logs for grades
        console.log('=== SERVER: USER GRADE PREFERENCES ===');
        console.log('userGradesData from DB:', userGradesData);
        console.log('userGradePreferences array:', userGradePreferences);
        // **** END NEW ****

		// 4. Get status options (remains the same)
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
		// REMOVED minimumGradeOptions

		return {
			activeSubscription,
            userProfile,
            allDisciplines,
            userSubscriptions: Array.from(userSubscriptions),
            userGradePreferences,
            statusOptions,
            notificationOptions,
			session,
			user,
		};

	} catch (err) {
		console.error('Error loading account data:', err);
		if (err && typeof err === 'object' && 'message' in err) {
            throw error(500, `Erreur serveur: ${err.message}`);
        }
        if (err && typeof err === 'object' && 'status' in err) {
             throw err;
        }
		throw error(500, 'Erreur lors du chargement des données du compte.');
	}
}

export const actions = undefined; // Keep actions undefined