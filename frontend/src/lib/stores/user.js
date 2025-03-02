import { writable } from 'svelte/store';

const userProfile = writable(null);
export default userProfile;