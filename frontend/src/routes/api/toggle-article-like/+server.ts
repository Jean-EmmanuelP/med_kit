// src/routes/api/toggle-article-like/+server.ts
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
		if (!body || typeof body.articleId !== 'number') {
			throw new Error('Missing or invalid articleId');
		}
		articleId = body.articleId;
	} catch (e: any) {
		throw error(400, `Bad Request: ${e.message || 'Invalid JSON'}`);
	}

	// 3. Attempt to DELETE the like first
	console.log(`User ${user.id} toggling like for article ${articleId}. Attempting delete...`);
	const { count: deleteCount, error: deleteError } = await supabase
		.from('article_likes')
		.delete({ count: 'exact' }) // Request the count of deleted rows
		.eq('user_id', user.id)
		.eq('article_id', articleId);

	if (deleteError) {
		console.error(`Database error deleting like for user ${user.id}, article ${articleId}:`, deleteError);
		throw error(500, `Database error: ${deleteError.message}`);
	}

	// 4. If DELETE affected 0 rows, it means it wasn't liked -> INSERT
	if (deleteCount === 0) {
		console.log(`Article ${articleId} was not liked. Attempting insert...`);
		const { error: insertError } = await supabase
            .from('article_likes')
            .insert({
                user_id: user.id,
                article_id: articleId,
                // created_at defaults to now()
            });

		if (insertError) {
			console.error(`Database error inserting like for user ${user.id}, article ${articleId}:`, insertError);
            // Handle potential race conditions or other errors (e.g., FK violation)
            if (insertError.code === '23503') { throw error(404, 'Article not found'); }
            if (insertError.code === '23505') { /* Unique violation - likely race condition, treat as success? */ console.warn("Race condition likely on like insert"); }
            else { throw error(500, `Database error: ${insertError.message}`); }
		} else {
            // Successfully inserted (liked)
            return json({ success: true, liked: true, message: 'Article liked' }, { status: 201 }); // 201 Created
        }
	}

	// 5. If DELETE affected > 0 rows, it means it was unliked
    if (deleteCount && deleteCount > 0) {
        console.log(`Article ${articleId} successfully unliked.`);
	    return json({ success: true, liked: false, message: 'Article unliked' }, { status: 200 }); // 200 OK
    }

    // Fallback/safety net - should ideally not be reached if deleteCount is exact
    return json({ success: true, message: 'Like status toggled (check state)' }, { status: 200 });
};