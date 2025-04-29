// src/routes/api/update-profile-and-subscriptions/+server.ts
import { error, json } from '@sveltejs/kit';
import type { RequestEvent } from './$types';

// Interface for the expected subscription payload (remains the same)
interface SubscriptionPayload {
	discipline_id: number;
	sub_discipline_id: number | null;
}

// Interface for the expected overall request body
interface UpdateRequestBody {
	profile: {
		first_name?: string;
		last_name?: string;
		status?: string | null;
		specialty?: string | null;
		notification_frequency?: string;
		date_of_birth?: string | null;
        // Note: minimum_grade_notification is NO LONGER expected here
	};
	subscriptions: SubscriptionPayload[];
	gradePreferences: string[]; // <-- NEW: Expecting an array of grades like ['A', 'B', 'C']
}

export async function POST({ request, locals }: RequestEvent) {
	const { session, supabase } = locals; // Destructure supabase here
	const user = session?.user; // Get user directly from session

	if (!user) {
		console.error("[API UpdateProfile] Error: No user session found.");
		return json({ error: 'Unauthorized' }, { status: 401 });
	}
    const userId = user.id; // Get user ID for clarity

	try {
		const { profile, subscriptions, gradePreferences }: UpdateRequestBody = await request.json();
		console.log(`[API UpdateProfile] User ${userId}: Received update request`, {
			profile: profile ? Object.keys(profile) : 'null',
			subscriptionsCount: subscriptions?.length ?? 'null',
            gradePreferencesCount: gradePreferences?.length ?? 'null',
            grades: gradePreferences // Log the actual grades received
		});

		// --- 1. Validate Input Data ---
		if (!profile || !subscriptions || !Array.isArray(gradePreferences)) {
			console.error(`[API UpdateProfile] User ${userId}: Missing required data. Profile: ${!!profile}, Subs: ${!!subscriptions}, Grades: ${Array.isArray(gradePreferences)}`);
			return json({ error: 'Missing required data' }, { status: 400 });
		}
        // Optional: Validate grades are only A, B, C
        const validGrades = ['A', 'B', 'C'];
        if (gradePreferences.some(g => !validGrades.includes(g))) {
             console.error(`[API UpdateProfile] User ${userId}: Invalid grade found in preferences:`, gradePreferences);
             return json({ error: 'Invalid grade preference provided.' }, { status: 400 });
        }


		// --- 2. Update User Profile ---
        // Explicitly DO NOT include minimum_grade_notification if it's accidentally sent
        const { minimum_grade_notification, ...profileDataToUpdate } = profile;
        if (Object.keys(profileDataToUpdate).length > 0) {
            console.log(`[API UpdateProfile] User ${userId}: Updating user_profiles table...`, profileDataToUpdate);
            const { error: profileError } = await supabase
                .from('user_profiles')
                .update(profileDataToUpdate)
                .eq('id', userId);

            if (profileError) {
                console.error(`[API UpdateProfile] User ${userId}: Profile update error:`, profileError);
                throw profileError; // Let the main catch block handle it
            }
            console.log(`[API UpdateProfile] User ${userId}: Profile update successful.`);
        } else {
             console.log(`[API UpdateProfile] User ${userId}: No profile fields to update.`);
        }


		// --- 3. Update Grade Preferences ---
        console.log(`[API UpdateProfile] User ${userId}: Deleting existing grade preferences...`);
        const { error: deleteGradesError } = await supabase
            .from('user_grade_preferences')
            .delete()
            .eq('user_id', userId);

        if (deleteGradesError) {
            console.error(`[API UpdateProfile] User ${userId}: Delete grade preferences error:`, deleteGradesError);
            throw deleteGradesError;
        }
         console.log(`[API UpdateProfile] User ${userId}: Existing grade preferences deleted.`);

        if (gradePreferences.length > 0) {
            const gradesToInsert = gradePreferences.map(grade => ({
                user_id: userId,
                grade: grade // Ensure grade is uppercase if needed, but DB check handles 'A','B','C'
            }));
            console.log(`[API UpdateProfile] User ${userId}: Inserting ${gradesToInsert.length} new grade preferences:`, gradesToInsert);
            const { error: insertGradesError } = await supabase
                .from('user_grade_preferences')
                .insert(gradesToInsert);

            if (insertGradesError) {
                console.error(`[API UpdateProfile] User ${userId}: Insert grade preferences error:`, insertGradesError);
                // Check for specific errors like check constraint violation if needed
                throw insertGradesError;
            }
             console.log(`[API UpdateProfile] User ${userId}: New grade preferences inserted successfully.`);
        } else {
             console.log(`[API UpdateProfile] User ${userId}: No new grade preferences to insert (all unchecked).`);
        }


		// --- 4. Update Discipline/Sub-Discipline Subscriptions (Logic remains the same) ---
		console.log(`[API UpdateProfile] User ${userId}: Deleting existing discipline subscriptions...`);
		const { error: deleteSubsError } = await supabase
			.from('user_subscriptions')
			.delete()
			.eq('user_id', userId);

		if (deleteSubsError) {
			console.error(`[API UpdateProfile] User ${userId}: Delete subscriptions error:`, deleteSubsError);
			throw deleteSubsError;
		}
        console.log(`[API UpdateProfile] User ${userId}: Existing discipline subscriptions deleted.`);

        if (subscriptions.length > 0) {
            // Prepare subscription records including main disciplines only if no subs are selected for them
            const subscriptionRecords: { user_id: string; discipline_id: number; sub_discipline_id: number | null }[] = [];
            const mainDisciplinesWithSubs = new Set<number>();
            const allMainDisciplineIds = new Set<number>();

            // First pass: collect main disciplines that have selected subs and all selected main discipline IDs
            subscriptions.forEach(sub => {
                allMainDisciplineIds.add(sub.discipline_id);
                if (sub.sub_discipline_id !== null) {
                    mainDisciplinesWithSubs.add(sub.discipline_id);
                    subscriptionRecords.push({
                        user_id: userId,
                        discipline_id: sub.discipline_id,
                        sub_discipline_id: sub.sub_discipline_id
                    });
                }
            });

            // Second pass: add main discipline records ONLY if they don't have any selected subs
            allMainDisciplineIds.forEach(discId => {
                if (!mainDisciplinesWithSubs.has(discId)) {
                    subscriptionRecords.push({
                        user_id: userId,
                        discipline_id: discId,
                        sub_discipline_id: null
                    });
                }
            });


            console.log(`[API UpdateProfile] User ${userId}: Inserting ${subscriptionRecords.length} new discipline subscriptions:`, subscriptionRecords);
            const { error: insertSubsError } = await supabase
                .from('user_subscriptions')
                .insert(subscriptionRecords);

            if (insertSubsError) {
                console.error(`[API UpdateProfile] User ${userId}: Insert subscriptions error:`, insertSubsError);
                throw insertSubsError;
            }
             console.log(`[API UpdateProfile] User ${userId}: New discipline subscriptions inserted successfully.`);
        } else {
            console.log(`[API UpdateProfile] User ${userId}: No new discipline subscriptions to insert.`);
        }

		console.log(`[API UpdateProfile] User ${userId}: Update successful.`);
		return json({ success: true, message: "Profil et préférences mis à jour avec succès." });

	} catch (err: any) { // Catch any thrown errors
		console.error(`[API UpdateProfile] User ${userId}: Overall update error:`, err);
        const message = err.message || 'Failed to update profile and preferences';
        const status = err.status || (err.code ? 400 : 500); // Use status if available, map code to 400, else 500
		return json({ error: message }, { status });
	}
}