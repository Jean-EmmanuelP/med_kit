import { writable } from 'svelte/store';

export interface UserProfile {
    id: string;
    first_name: string | null;
    last_name: string | null;
    email: string;
    disciplines: string[] | null;
    notification_frequency: string | null;
    date_of_birth: string | null;
    status: string | null;
    specialty: string | null;
}

const userProfile = writable<UserProfile | null>(null);
export default userProfile; 