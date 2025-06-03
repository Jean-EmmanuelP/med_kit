// frontend/src/lib/utils/subscriptionUtils.ts
import type { SupabaseClient } from '@supabase/supabase-js';

export interface ActiveSubscription {
    id: number;
    user_profile_id: string;
    stripe_subscription_id: string;
    stripe_customer_id: string;
    stripe_price_id: string;
    status: string;
    current_period_start: string;
    current_period_end: string;
    cancel_at_period_end: boolean;
    canceled_at?: string | null;
    trial_start?: string | null;
    trial_end?: string | null;
    created_at: string;
    updated_at: string;
}

export interface SubscriptionStatus {
    isActive: boolean;
    error: string | null;
}

export interface SubscriptionStatusWithDetails extends SubscriptionStatus {
    activeSubscription: ActiveSubscription | null;
}


export async function checkUserSubscription(
    supabase: SupabaseClient,
    userId: string | null | undefined,
): Promise<SubscriptionStatusWithDetails>;

export async function checkUserSubscription(
    supabase: SupabaseClient,
    userId: string | null | undefined,
): Promise<SubscriptionStatus | SubscriptionStatusWithDetails> {
    if (!userId) {
        console.warn('[SubscriptionUtils] checkUserSubscription called with no userId.');
        const baseReturn: SubscriptionStatus = { isActive: false, error: 'User ID not provided.' };
        return baseReturn;
    }

    if (!supabase) {
        console.error('[SubscriptionUtils] Supabase client not provided.');
        const baseReturn: SubscriptionStatus = { isActive: false, error: 'Supabase client is required.' };
        return baseReturn;
    }

    try {
        const now = new Date().toISOString(); // Get current time in UTC ISO format

        const selectColumns = '*';

        const { data, error: dbError } = await supabase
            .from('user_profile_subscriptions')
            .select(selectColumns)
            .eq('user_profile_id', userId)
            .in('status', ['active', 'trialing'])
            .lte('current_period_start', now)
            .gt('current_period_end', now)
            .order('current_period_end', { ascending: false })
            .maybeSingle();

        if (dbError) {
            console.error('[SubscriptionUtils] Error fetching subscription:', dbError);
            const baseReturn: SubscriptionStatus = { isActive: false, error: dbError.message };
            return baseReturn;
        }

        if (data) {
            const baseReturn: SubscriptionStatus = { isActive: true, error: null };
            return baseReturn;
        } else {
            const baseReturn: SubscriptionStatus = { isActive: false, error: null };
            return baseReturn;
        }
    } catch (err: any) {
        console.error('[SubscriptionUtils] Unexpected error in checkUserSubscription:', err);
        const baseReturn: SubscriptionStatus = { isActive: false, error: err.message || 'An unexpected error occurred.' };
        return baseReturn;
    }
}

/**
 * A simpler utility function that just returns a boolean indicating if the user is subscribed.
 */
export async function isUserSubscribed(
    supabase: SupabaseClient,
    userId: string | null | undefined
): Promise<boolean> {
    const { isActive } = await checkUserSubscription(supabase, userId); // Default is { returnDetails: false }
    return isActive;
}