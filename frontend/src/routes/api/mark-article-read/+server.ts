// src/routes/api/mark-article-read/+server.ts
import { error, json } from '@sveltejs/kit';

export const POST = async ({ request, locals: { supabase, safeGetSession } }) => {
	// 1. Check Authentication
	const { user } = await safeGetSession();
	if (!user) {
		throw error(401, 'Unauthorized'); // User must be logged in
	}

	// 2. Get Article ID from request body
	let articleId: number;
	try {
		const body = await request.json();
		if (!body || typeof body.articleId !== 'number') {
			throw new Error('Missing or invalid articleId in request body');
		}
		articleId = body.articleId;
	} catch (e: any) {
		console.error('Error parsing request body:', e);
		throw error(400, `Bad Request: ${e.message || 'Invalid JSON'}`);
	}

	// 3. Perform Upsert operation
	console.log(`User ${user.id} marking article ${articleId} as read.`);

	const { error: dbError } = await supabase
        .from('article_read')
        .upsert(
            {
                user_id: user.id,
                article_id: articleId,
            },
            {
                ignoreDuplicates: true,
            }
        );

	// 4. Handle Database Errors
	if (dbError) {
		console.error(`Database error marking article read for user ${user.id}, article ${articleId}:`, dbError);
		// Check for specific errors if needed (e.g., foreign key violation if articleId is invalid)
		if (dbError.code === '23503') { // Foreign key violation
             throw error(404, 'Article not found');
        }
		throw error(500, `Database error: ${dbError.message}`);
	}

	// 5. Return Success Response
	return json({ success: true, message: 'Article marked as read' }, { status: 200 }); // 200 OK for upsert success
    // Use 201 Created if you only INSERTED and want to signify resource creation
};