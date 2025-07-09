import { json } from '@sveltejs/kit';
import type { RequestEvent } from './$types';

export async function GET({ url, locals }: RequestEvent) {
    const { session, supabase } = locals;
    const user = session?.user;

    if (!user) {
        console.error('[API GetUsers] Error: No user session found.');
        return json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Check if user has all power (super admin)
    const { data: userProfile, error: profileError } = await supabase
        .from('user_profiles')
        .select('has_all_power')
        .eq('id', user.id)
        .single();

    if (profileError || !userProfile?.has_all_power) {
        console.error('[API GetUsers] Error: User does not have sufficient privileges.');
        return json({ error: 'Forbidden - Super admin access required' }, { status: 403 });
    }

    try {
        const searchQuery = url.searchParams.get('q') || '';
        const page = parseInt(url.searchParams.get('page') || '1');
        const pageSize = parseInt(url.searchParams.get('pageSize') || '10');
        const offset = (page - 1) * pageSize;

        // Build query for users with optional search (removing created_at since it doesn't exist)
        let query = supabase
            .from('user_profiles')
            .select('id, first_name, last_name, email, is_admin, has_all_power')
            .order('email', { ascending: true });

        // Add search filter if provided
        if (searchQuery.trim()) {
            query = query.or(`first_name.ilike.%${searchQuery}%,last_name.ilike.%${searchQuery}%,email.ilike.%${searchQuery}%`);
        }

        // Apply pagination
        const { data: users, error } = await query
            .range(offset, offset + pageSize - 1);

        if (error) {
            console.error('[API GetUsers] Error fetching users:', error);
            throw error;
        }

        // Get total count for pagination
        let countQuery = supabase
            .from('user_profiles')
            .select('id', { count: 'exact', head: true });

        if (searchQuery.trim()) {
            countQuery = countQuery.or(`first_name.ilike.%${searchQuery}%,last_name.ilike.%${searchQuery}%,email.ilike.%${searchQuery}%`);
        }

        const { count, error: countError } = await countQuery;

        if (countError) {
            console.error('[API GetUsers] Error counting users:', countError);
            throw countError;
        }

        return json({
            users: users || [],
            pagination: {
                total: count || 0,
                page,
                pageSize,
                totalPages: Math.ceil((count || 0) / pageSize)
            }
        });

    } catch (err: any) {
        console.error('[API GetUsers] Error:', err);
        const message = err.message || 'Failed to fetch users';
        const status = err.status || 500;
        return json({ error: message }, { status });
    }
} 