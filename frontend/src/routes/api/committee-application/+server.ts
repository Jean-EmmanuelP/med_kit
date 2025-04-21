import { error, json } from '@sveltejs/kit';
import type { RequestEvent } from './$types';

export async function POST({ request, locals: { supabase, safeGetSession } }: RequestEvent) {
    // Get user session - useful if you want to link application to a user later
    // const { user } = await safeGetSession();
    // We don't strictly need the user to be logged in based on the current RLS policy

    let formData;
    try {
        formData = await request.json();
        if (typeof formData !== 'object' || formData === null) {
            throw new Error('Invalid data format');
        }
        // Basic validation for required fields
        if (!formData.prenom || !formData.nom || !formData.statut || !formData.specialite || !formData.centre) {
             throw error(400, 'Missing required fields in application data.');
        }

    } catch (e: any) {
        console.error("Error parsing application JSON:", e);
        if (e.status === 400) throw e; // Re-throw specific validation error
        throw error(400, 'Bad request: Could not parse application data.');
    }

    // Prepare data for insertion (matching table columns)
    const dataToInsert = {
        // user_id: user?.id || null, // Uncomment if you want to link to logged-in user
        first_name: formData.prenom,
        last_name: formData.nom,
        status: formData.statut,
        specialty: formData.specialite,
        sub_specialty: formData.surSpecialite || null, // Handle optional field
        practice_center: formData.centre,
        // created_at is handled by the database default
    };

    try {
        const { error: insertError } = await supabase
            .from('committee_applications')
            .insert(dataToInsert);

        if (insertError) {
            console.error('Supabase insert error:', insertError);
            // Provide a more generic error to the client
            throw error(500, `Database error occurred.`);
        }

        console.log(`Committee application submitted successfully: ${formData.prenom} ${formData.nom}`);
        // Customize success message
        return json({ message: 'Votre candidature a bien été envoyée. Merci !' }, { status: 201 }); // 201 Created

    } catch (err: any) {
        // Catch errors thrown from validation or Supabase
        console.error('Error submitting committee application:', err);
        if (err.status) {
            // Re-throw SvelteKit errors (like the 400 or 500)
            throw err;
        }
        // Generic fallback for unexpected errors
        throw error(500, err.message || 'An unexpected error occurred while saving the application.');
    }
}