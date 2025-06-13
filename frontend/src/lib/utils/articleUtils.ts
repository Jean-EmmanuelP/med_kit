// src/lib/utils/articleUtils.ts

export interface FilterOption {
	value: string;
	label: string;
}

export interface SubDisciplineOption {
	id: number;
	name: string;
}

export interface Article {
	id: string | number;
	title: string;
	content: string;
	disciplines: string[]; // Keep track of disciplines associated with the article
	published_at: string;
	journal?: string;
	grade?: string;
	link?: string;
	// Add other potential fields if needed from your API response
	article_id?: string | number; // Handle potential variations in ID naming
	is_read?: boolean; // Track if the article has been read by the user
	is_liked?: boolean; // Track if the article has been liked by the user (heart icon)
	like_count?: number; // Track the number of likes for the article (heart icon)
	read_count?: number; // Track total reads for the article
	is_thumbed_up?: boolean; // Track if the article has been thumbed up by the user
	thumbs_up_count?: number; // Track the number of thumbs up for the article
	added_at_out?: string; // Track when the article was added to the system
	is_article_of_the_day?: boolean; // Flag indicating if this is the article of the day
	is_recommandation?: boolean; // Flag indicating if this is a recommendation article
}

export interface ContentSection {
	emoji: string;
	title: string;
	content: string[];
}

export function formatTitle(title: string): string {
	if (!title) return '';
	const words = title.toLowerCase().split(' ');
	if (words.length === 0) return '';
	words[0] = words[0].charAt(0).toUpperCase() + words[0].slice(1);
	return words.join(' ');
}

export function formatDate(publishedAt: string): string {
	if (!publishedAt) return 'Non spécifiée';
	try {
		const date = new Date(publishedAt);
		// Basic validation
		if (isNaN(date.getTime())) {
			return 'Date invalide';
		}
		return `${date.getDate().toString().padStart(2, '0')}/${(date.getMonth() + 1)
			.toString()
			.padStart(2, '0')}/${date.getFullYear()}`;
	} catch (e) {
		console.error('Error formatting date:', publishedAt, e);
		return 'Date invalide';
	}
}

export function extractTitleEmoji(content: string): string {
	if (!content || typeof content !== 'string') return '📝';
	const lines = content.split('\n');
	for (const line of lines) {
		// Check for H1 level emoji title first
		if (
			line.trim().startsWith('# 📝') ||
			line.trim().startsWith('# 📌') ||
			line.trim().startsWith('# 🧪') ||
			line.trim().startsWith('# 📊') ||
			line.trim().startsWith('# 🩺') ||
			line.trim().startsWith('# 📖') ||
			line.trim().startsWith('# 🌟')
		) {
			const parts = line.trim().split(' ');
			if (parts.length > 1) {
				return parts[1] || '📝'; // Return the emoji after '#'
			}
		}
	}
	return '📝'; // Default emoji
}

export function parseContent(content: string): ContentSection[] {
	if (!content || typeof content !== 'string') return [];

	const sections: ContentSection[] = [];
	let currentSection: ContentSection = { emoji: '', title: '', content: [] };
	const lines = content.split('\n');
	let inSection = false;

	for (const line of lines) {
        const trimmedLine = line.trim();

		// Check for standard markdown headers (## emoji title)
		const markdownHeaderMatch = trimmedLine.match(/^##\s*(\p{Emoji})\s*(.+)$/u);
		
		// Check for recommendation format (emoji **title**)
		const recoHeaderMatch = trimmedLine.match(/^(\p{Emoji})\s*\*\*(.+?)\*\*$/u);

		if (markdownHeaderMatch || recoHeaderMatch) {
			// If we were already tracking a section, push the completed one
			if (inSection && (currentSection.title || currentSection.content.length > 0)) {
				sections.push(currentSection);
			}

            // Start a new section
			inSection = true;

			if (markdownHeaderMatch) {
				// Standard markdown format: ## 🎯 Title
				currentSection = {
					emoji: markdownHeaderMatch[1],
					title: markdownHeaderMatch[2].trim(),
					content: []
				};
			} else if (recoHeaderMatch) {
				// Recommendation format: 🎯 **Title**
				currentSection = {
					emoji: recoHeaderMatch[1],
					title: recoHeaderMatch[2].trim(),
					content: []
				};
			}
		} else if (trimmedLine && inSection) {
			// If it's a non-empty line and we are inside a section, add to content
            // Skip horizontal rules and process bullet points
            if (trimmedLine !== '---' && trimmedLine !== '***' && trimmedLine !== '___') {
				// For recommendations, preserve the original line with indentation markers
				// For regular articles, clean up the formatting
				if (line.match(/^ {4}\*/) || trimmedLine.match(/^[•·○]/)) {
					// This is a nested bullet point - mark it as such
					const cleanLine = trimmedLine.replace(/^\*\s*/, '').replace(/^[•·○]\s*/, '');
					// Keep bold formatting for recommendations, remove for regular articles
					if (cleanLine.trim()) {
						currentSection.content.push(`__NESTED__${cleanLine.trim()}`);
					}
				} else if (trimmedLine.startsWith('*')) {
					// Main bullet point
					const cleanLine = trimmedLine.replace(/^\*\s*/, '');
					// Keep bold formatting for recommendations, remove for regular articles
					if (cleanLine.trim()) {
						currentSection.content.push(cleanLine.trim());
					}
				} else {
					// Regular paragraph
					const cleanLine = trimmedLine;
					// Keep bold formatting for recommendations, remove for regular articles
					if (cleanLine.trim()) {
						currentSection.content.push(cleanLine.trim());
					}
				}
            }
		}
	}

	// Push the very last section after the loop finishes
	if (inSection && (currentSection.title || currentSection.content.length > 0)) {
		sections.push(currentSection);
	}

    // Add the fallback just in case this logic *still* fails for some reason
    if (sections.length === 0 && content?.trim()) {
        console.warn("parseContent failed to find sections, returning raw content block.");
        return [{ emoji: '📄', title: 'Contenu', content: content.split('\n').map(l => l.trim()).filter(Boolean) }];
    }

	return sections;
}

// Helper to get a consistent ID, handling both 'id' and 'article_id'
export function getArticleId(article: Article): string | number {
    // Prioritize 'id', then 'article_id', then generate fallback
    const id = article.id ?? article.article_id;
    if (id !== null && id !== undefined) {
        return id;
    }
    // Fallback if no ID is present (should be rare)
    console.warn("Article missing 'id' and 'article_id', generating fallback ID.");
    return Date.now() + Math.random();
}