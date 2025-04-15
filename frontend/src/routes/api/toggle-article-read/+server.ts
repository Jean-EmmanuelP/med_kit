// src/routes/api/toggle-article-read/+server.ts
import { error, json } from '@sveltejs/kit';

export const POST = async ({ request, locals: { supabase, safeGetSession } }) => {
	console.log('--- API /api/toggle-article-read START ---'); // Log start

	// 1. Check Authentication
	const { user } = await safeGetSession();
	if (!user) {
        console.error('API Error: User not authenticated');
		throw error(401, 'Unauthorized');
	}
    console.log(`API: Authenticated user ID: ${user.id}`);

	// 2. Get Article ID from request body
	let articleId: number;
	try {
		const body = await request.json();
        console.log('API: Received request body:', body); // Log received body
		if (!body || typeof body.articleId !== 'number' || isNaN(body.articleId)) { // Add NaN check
			throw new Error('Missing or invalid articleId');
		}
		articleId = body.articleId;
        console.log(`API: Parsed articleId: ${articleId}`);
	} catch (e: any) {
        console.error('API Error: Failed to parse request body:', e);
		throw error(400, `Bad Request: ${e.message || 'Invalid JSON'}`);
	}

	// 3. Check current read status
	console.log(`API: Checking read status for user ${user.id}, article ${articleId}...`);
	const { data: existingRead, error: checkError } = await supabase
		.from('article_read')
		.select('user_id', { count: 'exact' }) // Get count to be sure
		.eq('user_id', user.id)
		.eq('article_id', articleId);
		// Removed maybeSingle, checking count is safer

	if (checkError) {
		console.error(`API DB Error (Check Read Status):`, checkError);
		throw error(500, `Database error: ${checkError.message}`);
	}

    const isCurrentlyRead = existingRead && existingRead.length > 0; // Check if array has items
    console.log(`API: Article ${articleId} is currently read: ${isCurrentlyRead}`);

	// 4. Perform INSERT or DELETE based on current status
	if (isCurrentlyRead) {
		// --- Article is currently READ, so MARK AS UNREAD (DELETE) ---
		console.log(`API: Deleting read record for article ${articleId}...`);
		const { error: deleteError } = await supabase
			.from('article_read')
			.delete()
			.eq('user_id', user.id)
			.eq('article_id', articleId);

		if (deleteError) {
			console.error(`API DB Error (Delete Read Status):`, deleteError);
			throw error(500, `Database error: ${deleteError.message}`);
		}
		console.log(`API: Successfully marked article ${articleId} as UNREAD.`);
		console.log('--- API /api/toggle-article-read END ---');
		return json({ success: true, read: false, message: 'Article marked as unread' }, { status: 200 });

	} else {
		// --- Article is currently UNREAD, so MARK AS READ (INSERT) ---
		console.log(`API: Inserting read record for article ${articleId}...`);
		const { error: insertError } = await supabase
			.from('article_read')
			.insert({
				user_id: user.id,
				article_id: articleId,
			});

		if (insertError) {
			console.error(`API DB Error (Insert Read Status):`, insertError);
			if (insertError.code === '23503') { // Foreign key violation likely means articleId doesn't exist
                console.error(`API Error Detail: Article ID ${articleId} might not exist.`);
				throw error(404, 'Article not found');
			}
			throw error(500, `Database error: ${insertError.message}`);
		}
		console.log(`API: Successfully marked article ${articleId} as READ.`);
		console.log('--- API /api/toggle-article-read END ---');
		return json({ success: true, read: true, message: 'Article marked as read' }, { status: 201 }); // 201 Created
	}
};