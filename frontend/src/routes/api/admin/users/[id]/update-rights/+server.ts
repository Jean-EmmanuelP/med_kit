import { json } from '@sveltejs/kit';
import type { RequestEvent } from './$types';

export async function POST({ request, params, locals }: RequestEvent) {
    const { session, supabase } = locals;
    const user = session?.user;
    const targetUserId = params.id;

    if (!user) {
        console.error('[API UpdateUserRights] Error: No user session found.');
        return json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Check if current user has all power (super admin)
    const { data: userProfile, error: profileError } = await supabase
        .from('user_profiles')
        .select('has_all_power, is_admin')
        .eq('id', user.id)
        .single();

    if (profileError) {
        console.error('[API UpdateUserRights] Error fetching user profile:', profileError);
        return json({ error: 'Error fetching user profile' }, { status: 500 });
    }

    if (!userProfile?.has_all_power) {
        console.error('[API UpdateUserRights] Error: User does not have sufficient privileges.');
        return json({ error: 'Forbidden - Super admin access required' }, { status: 403 });
    }

    try {
        const { is_admin, has_all_power } = await request.json();
        
        // Prevent users from modifying their own permissions
        if (user.id === targetUserId) {
            return json({ error: 'You cannot modify your own permissions' }, { status: 400 });
        }

        // Validate input
        if (typeof is_admin !== 'boolean') {
            return json({ error: 'Invalid is_admin value' }, { status: 400 });
        }

        // has_all_power is optional, but if provided must be boolean
        if (has_all_power !== undefined && typeof has_all_power !== 'boolean') {
            return json({ error: 'Invalid has_all_power value' }, { status: 400 });
        }

        // Prepare update object
        const updateData: { is_admin: boolean; has_all_power?: boolean } = { is_admin };
        if (has_all_power !== undefined) {
            updateData.has_all_power = has_all_power;
        }

        const { data, error } = await supabase
            .from('user_profiles')
            .update(updateData)
            .eq('id', targetUserId)
            .select()
            .single();

        if (error) {
            console.error('[API UpdateUserRights] Error updating user rights:', error);
            throw error;
        }

        return json({
            success: true,
            message: 'User rights updated successfully',
            user: data
        });

    } catch (err: any) {
        console.error('[API UpdateUserRights] Error:', err);
        const message = err.message || 'Failed to update user rights';
        const status = err.status || 500;
        return json({ error: message }, { status });
    }
} 