// src/routes/api/toggle-article-thumbs-up/+server.ts
import { error, json } from '@sveltejs/kit';

export const POST = async ({ request, locals: { supabase, safeGetSession } }) => {
	// 1. Check Authentication
	const { user } = await safeGetSession();
	if (!user) {
		throw error(401, 'Unauthorized');
	}

	// 2. Get Article ID from request body
	let articleId: number;
	try {
		const body = await request.json();
		if (!body || typeof body.articleId !== 'number' || isNaN(body.articleId)) {
			throw new Error('Missing or invalid articleId');
		}
		articleId = body.articleId;
	} catch (e: any) {
		throw error(400, `Bad Request: ${e.message || 'Invalid JSON'}`);
	}

	// 3. Attempt to DELETE the thumbs-up first
	console.log(`User ${user.id} toggling thumbs-up for article ${articleId}. Attempting delete...`);
	const { count: deleteCount, error: deleteError } = await supabase
		.from('article_thumbs_up')
		.delete({ count: 'exact' }) // Request the count of deleted rows
		.eq('user_id', user.id)
		.eq('article_id', articleId);

	if (deleteError) {
		console.error(`Database error deleting thumbs-up for user ${user.id}, article ${articleId}:`, deleteError);
		throw error(500, `Database error: ${deleteError.message}`);
	}

	// 4. If DELETE affected 0 rows, it means it wasn't thumbed-up -> INSERT
	if (deleteCount === 0) {
		console.log(`Article ${articleId} was not thumbed-up. Attempting insert...`);
		const { error: insertError } = await supabase
            .from('article_thumbs_up')
            .insert({
                user_id: user.id,
                article_id: articleId,
                // thumbed_up_at defaults to now()
            });

		if (insertError) {
			console.error(`Database error inserting thumbs-up for user ${user.id}, article ${articleId}:`, insertError);
            // Handle potential race conditions or other errors (e.g., FK violation)
            if (insertError.code === '23503') { throw error(404, 'Article not found'); }
            if (insertError.code === '23505') { /* Unique violation - likely race condition, treat as success? */ console.warn("Race condition likely on thumbs-up insert"); }
            else { throw error(500, `Database error: ${insertError.message}`); }
		} else {
            // Successfully inserted (thumbed-up)
            return json({ success: true, thumbed_up: true, message: 'Article thumbed up' }, { status: 201 }); // 201 Created
        }
	}

	// 5. If DELETE affected > 0 rows, it means it was un-thumbed-up
    if (deleteCount && deleteCount > 0) {
        console.log(`Article ${articleId} successfully un-thumbed-up.`);
	    return json({ success: true, thumbed_up: false, message: 'Article thumbed down' }, { status: 200 }); // 200 OK (or 204 No Content if preferred)
    }

    // Fallback/safety net - should ideally not be reached if deleteCount is exact
    console.warn(`Unexpected state after toggle for article ${articleId}, user ${user.id}. Delete count was ${deleteCount}`);
    return json({ success: true, message: 'Thumbs-up status toggled (check state)' }, { status: 200 });
};