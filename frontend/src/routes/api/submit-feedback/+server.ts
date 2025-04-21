import { error, json } from '@sveltejs/kit';
import type { RequestEvent } from './$types';

export async function POST({ request, locals: { supabase, safeGetSession } }: RequestEvent) {
	const { user } = await safeGetSession();
	if (!user) {
		throw error(401, 'Authentication required to submit feedback.');
	}

	let feedbackData;
	try {
		feedbackData = await request.json();
		if (typeof feedbackData !== 'object' || feedbackData === null) {
			throw new Error('Invalid data format');
		}
	} catch (e) {
		console.error("Error parsing feedback JSON:", e);
		throw error(400, 'Bad request: Could not parse feedback data.');
	}

	// Prepare data for insertion (matching table columns)
	const dataToInsert = {
		user_id: user.id,
		content_useful: feedbackData.contentUseful || null,
		format_suitable: feedbackData.formatSuitable || null,
		desired_features: feedbackData.desiredFeatures || null,
		willing_to_pay: feedbackData.willingToPay || null, // Will contain "Oui" or "Non"
		price_suggestion: feedbackData.willingToPay === 'Oui' ? (feedbackData.priceSuggestion || null) : null,
		reason_not_to_pay: feedbackData.willingToPay === 'Non' ? (feedbackData.reasonNotToPay || null) : null,
		improvements: feedbackData.improvements || null,
	};

	try {
		const { error: insertError } = await supabase
			.from('feedback')
			.insert(dataToInsert);

		if (insertError) {
			console.error('Supabase insert error:', insertError);
			throw error(500, `Database error: ${insertError.message}`);
		}

		console.log(`Feedback submitted successfully by user ${user.id}`);
		return json({ message: 'Merci, votre retour a bien été envoyé !' }, { status: 201 });

	} catch (err: any) {
		console.error('Error submitting feedback:', err);
		if (err.status) {
			throw err;
		}
		throw error(500, err.message || 'An unexpected error occurred while saving feedback.');
	}
}