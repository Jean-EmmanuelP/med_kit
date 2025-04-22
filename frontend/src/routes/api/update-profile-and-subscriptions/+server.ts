// src/routes/api/update-profile-and-subscriptions/+server.ts
import { error, json } from '@sveltejs/kit';
import type { RequestEvent } from './$types';

export async function POST(event: RequestEvent) {
	const { request, locals: { supabase, safeGetSession } } = event;

	const { user } = await safeGetSession();
	if (!user) {
		throw error(401, 'Unauthorized');
	}

	let profileData;
    let subscriptionsData: { discipline_id: number; sub_discipline_id: number | null }[];

	try {
		const body = await request.json();
		if (!body || typeof body !== 'object') throw new Error('Invalid JSON body');

		profileData = body.profile; // Expect profile updates under 'profile' key
        subscriptionsData = body.subscriptions; // Expect subscriptions under 'subscriptions' key

		// Basic validation
		if (!profileData || typeof profileData !== 'object') throw new Error('Missing or invalid profile data');
        if (!Array.isArray(subscriptionsData)) throw new Error('Invalid subscriptions data');
        if (!profileData.first_name || !profileData.last_name) throw new Error('First name and last name are required');
        // Add more validation as needed

	} catch (e: any) {
		console.error("Error parsing update request:", e);
		throw error(400, `Bad Request: ${e.message}`);
	}

    console.log(`Updating profile for user: ${user.id}`, profileData);
    console.log(`Updating subscriptions for user: ${user.id}`, subscriptionsData);


	// --- Perform updates in a transaction ---
    // Note: Supabase JS client doesn't directly support multi-statement transactions easily.
    // We'll perform them sequentially and rely on the database/RLS for consistency.
    // For true atomicity, you'd create a PostgreSQL function (RPC).

    try {
        // 1. Update User Profile
        const { error: profileUpdateError } = await supabase
            .from('user_profiles')
            .update({
                first_name: profileData.first_name,
                last_name: profileData.last_name,
                status: profileData.status || null,
                specialty: profileData.specialty || null,
                notification_frequency: profileData.notification_frequency,
                date_of_birth: profileData.date_of_birth || null
                // DO NOT update 'disciplines' here
            })
            .eq('id', user.id);

        if (profileUpdateError) {
            console.error("Error updating profile:", profileUpdateError);
            throw error(500, `Profile update failed: ${profileUpdateError.message}`);
        }
        console.log("Profile updated successfully.");

        // 2. Update Subscriptions (Delete old, Insert new)
        // Delete existing subscriptions for the user
        const { error: deleteError } = await supabase
            .from('user_subscriptions')
            .delete()
            .eq('user_id', user.id);

        if (deleteError) {
            console.error("Error deleting old subscriptions:", deleteError);
            throw error(500, `Subscription cleanup failed: ${deleteError.message}`);
        }
        console.log("Old subscriptions deleted.");

        // Insert new subscriptions if any
        if (subscriptionsData.length > 0) {
             // Add user_id to each subscription object
             const subsToInsert = subscriptionsData.map(sub => ({
                 ...sub,
                 user_id: user.id
             }));

            const { error: insertError } = await supabase
                .from('user_subscriptions')
                .insert(subsToInsert);

            if (insertError) {
                console.error("Error inserting new subscriptions:", insertError);
                // Consider rolling back profile update manually if possible, or log inconsistency
                throw error(500, `Subscription update failed: ${insertError.message}`);
            }
            console.log("New subscriptions inserted successfully.");
        } else {
            console.log("No new subscriptions to insert.");
        }

        return json({ success: true, message: 'Profil et abonnements mis à jour avec succès.' });

    } catch (err) {
         // Catch errors from the try block (thrown Supabase/SvelteKit errors)
        console.error("Error during profile/subscription update:", err);
        if (err && typeof err === 'object' && 'status' in err) {
             throw err; // Re-throw SvelteKit error
        }
        throw error(500, 'An unexpected error occurred during the update.');
    }
}