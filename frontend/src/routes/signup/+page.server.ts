// +page.server.ts (or your relevant server file name)
import { PUBLIC_SUPABASE_ANON_KEY } from '$env/static/public';
import { fail, redirect, type Actions } from '@sveltejs/kit';

export const actions: Actions = {
    default: async ({ request, locals: { supabase } }) => {
        const formData = await request.formData();

        // Get required fields from the simplified form
        const email = formData.get('email')?.toString();
        const password = formData.get('password')?.toString();

        // Get optional/derived fields (might be sent by form or derived here)
        const first_name = formData.get('first_name')?.toString() || email?.split('@')[0] || '';
        const last_name = formData.get('last_name')?.toString() || '';
        const date_of_birth = formData.get('date_of_birth')?.toString() || null;

        // --- Basic Validation ---
        if (!email || !password) {
            return fail(400, { error: 'Email et mot de passe sont requis.', email });
        }
        if (password.length < 6) {
             return fail(400, { error: 'Le mot de passe doit contenir au moins 6 caractères.', email });
        }

        // --- Supabase Auth ---
        const { data: signUpData, error: signUpError } = await supabase.auth.signUp({
            email,
            password,
            // Add options if needed, e.g., for email confirmation redirect
            // options: { emailRedirectTo: `${url.origin}/auth/callback` }
        });

        if (signUpError) {
             if (signUpError.message.includes('User already registered')) {
                 return fail(400, { error: 'Cet email est déjà utilisé.', email });
            }
            console.error('Supabase SignUp Error:', signUpError); // Log unexpected errors
            return fail(500, { error: "Erreur lors de l'inscription.", email });
        }

        // Handle cases where user object might be missing (should be rare if no error)
        // Or if email confirmation is required (session might be null initially)
        if (!signUpData.user) {
             console.error('SignUp successful but no user object returned.');
             // If email confirmation is enabled, maybe redirect to a "check email" page or return success message
             // For now, treat as an internal error if no user object AND no error was thrown
             return fail(500, { error: 'Erreur interne lors de la création de l’utilisateur.', email });
        }

        // --- Create User Profile ---
        const newUserProfile = {
            id: signUpData.user.id,
            first_name,
            last_name,
            email,
            disciplines: [], // Default value
            notification_frequency: 'tous_les_jours', // Default value
            date_of_birth,
        };

        const { error: profileError } = await supabase
            .from('user_profiles')
            .insert(newUserProfile);
            // No .select().single() needed if we don't use profileData afterwards

        if (profileError) {
            console.error('Supabase Profile Insert Error:', profileError);
            // Consider potential cleanup (e.g., delete the auth user?) if profile fails
            return fail(500, { error: 'Erreur lors de la sauvegarde du profil utilisateur.', email });
        }

        // --- Trigger Welcome Email (Optional) ---
        try {
             const welcomeEdgeUrl =
                'https://etxelhjnqbrgwuitltyk.supabase.co/functions/v1/send-welcome-email';
             // Use await but don't block signup return if it fails, just log
             fetch(welcomeEdgeUrl, { // Fire and forget (mostly)
                method: 'POST',
                headers: {
                    // Ensure ANON_KEY has invoke permissions or use service_role key if needed
                    Authorization: `Bearer ${PUBLIC_SUPABASE_ANON_KEY}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: signUpData.user.id,
                    email: email,
                    first_name: first_name
                }),
            }).then(async response => {
                if (!response.ok) {
                    const errorText = await response.text();
                    console.error('Error triggering send-welcome-email (async):', errorText);
                } else {
                    console.log('send-welcome-email triggered successfully (async)');
                }
            }).catch(e => {
                 console.error('Exception calling send-welcome-email (async):', e);
            });
        } catch (e) {
             console.error('Error setting up welcome email fetch:', e); // Should be rare
        }

        // --- Success ---
        // Redirect to the user's dashboard or account page
        // Use 303 See Other for POST -> GET redirect pattern
        throw redirect(303, '/ma-veille');
    },
};