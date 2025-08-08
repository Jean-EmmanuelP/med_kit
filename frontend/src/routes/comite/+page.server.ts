import type { PageServerLoad } from './$types';
import { supabase } from '$lib/supabase';

export const load: PageServerLoad = async () => {
	try {
		// Load referents from database
		const { data: referents, error } = await supabase
			.from('committee_referents')
			.select('*')
			.order('specialty')
			.order('name');

		if (error) {
			console.error('Error loading referents:', error);
			return {
				referents: []
			};
		}

		return {
			referents: referents || []
		};
	} catch (error) {
		console.error('Error in committee page load:', error);
		return {
			referents: []
		};
	}
}; 