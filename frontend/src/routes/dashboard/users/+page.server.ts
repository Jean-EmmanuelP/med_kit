import { redirect, error } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ locals }) => {
    const { session, supabase } = locals;
    
    if (!session) {
        throw redirect(303, '/login?redirectTo=/dashboard/users');
    }
    
    // Check if user has all power (super admin)
    const { data: userProfile, error: profileError } = await supabase
        .from('user_profiles')
        .select('has_all_power, is_admin')
        .eq('id', session.user.id)
        .single();
    
    if (profileError) {
        console.error('Error fetching user profile for admin check:', profileError);
        throw error(500, 'Erreur lors de la vérification des permissions');
    }
    
    if (!userProfile?.has_all_power) {
        throw redirect(303, '/');
    }
    
    return {
        user: {
            ...session.user,
            is_admin: userProfile?.is_admin || false,
            has_all_power: userProfile?.has_all_power || false
        }
    };
}; 