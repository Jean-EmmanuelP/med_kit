import { error, json } from '@sveltejs/kit';
import type { RequestEvent } from './$types';

export async function POST({ locals }: RequestEvent) {
    try {
        const session = await locals.supabase.auth.getSession();
        if (!session?.data?.session?.user) {
            throw error(401, 'Unauthorized');
        }

        const { error: updateError } = await locals.supabase
            .from('user_profiles')
            .update({ feedback_modal: new Date().toISOString() })
            .eq('id', session.data.session.user.id);

        if (updateError) {
            console.error("Update feedback modal timestamp error:", updateError);
            throw updateError;
        }

        return json({ success: true });
    } catch (err) {
        console.error("Update feedback modal error:", err);
        return json({ error: 'Failed to update feedback modal timestamp' }, { status: 500 });
    }
} 