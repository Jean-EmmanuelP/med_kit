import { writable } from 'svelte/store';
import type { SupabaseClient } from '@supabase/supabase-js';

export const supabaseStore = writable<SupabaseClient | null>(null);
