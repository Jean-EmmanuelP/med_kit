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
	disciplines: string[];
	published_at: string;
	journal?: string;
	grade?: string;
	link?: string;
	article_id?: string | number;
	is_read?: boolean;
	is_liked?: boolean;
	like_count?: number;
	read_count?: number;
	is_thumbed_up?: boolean;
	thumbs_up_count?: number;
	added_at_out?: string;
	is_article_of_the_day?: boolean;
	is_recommandation?: boolean;
}

export interface ContentSection {
	emoji: string;
	title: string;
	content: string[];
	subsections?: ContentSection[];
	level: number;
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
		if (
			line.trim().startsWith('# 📝') ||
			line.trim().startsWith('# 📌') ||
			line.trim().startsWith('# 🧪') ||
			line.trim().startsWith('# 📊') ||
			line.trim().startsWith('# 🩺') ||
			line.trim().startsWith('# 📖') ||
			line.trim().startsWith('# 🌟') ||
			line.trim().startsWith('# 💊')
		) {
			const parts = line.trim().split(' ');
			if (parts.length > 1) {
				return parts[1] || '📝';
			}
		}
	}
	return '📝';
}

export function parseContent(content: string): ContentSection[] {
	if (!content || typeof content !== 'string') return [];

	const sections: ContentSection[] = [];
	const lines = content.split('\n');
	const sectionStack: ContentSection[] = [];

	for (const line of lines) {
		const trimmedLine = line.trim();
		if (!trimmedLine) continue;

		const headerMatch = trimmedLine.match(/^(#{1,6})\s+(.+)$/);

		if (headerMatch) {
			const level = headerMatch[1].length;
			const fullTitle = headerMatch[2].trim();

			if (level === 1) {
				continue;
			}

			const emojiMatch = fullTitle.match(/^(\p{Emoji}(?:\uFE0F)?)\s*(.+)$/u);
			const emoji = emojiMatch ? emojiMatch[1] : '📄';
			const title = emojiMatch ? emojiMatch[2].trim() : fullTitle;

			const newSection: ContentSection = {
				emoji,
				title,
				content: [],
				subsections: [],
				level
			};

			while (sectionStack.length > 0 && sectionStack[sectionStack.length - 1].level >= level) {
				sectionStack.pop();
			}

			if (sectionStack.length > 0) {
				const parent = sectionStack[sectionStack.length - 1];
				if (!parent.subsections) {
					parent.subsections = [];
				}
				parent.subsections.push(newSection);
			} else {
				sections.push(newSection);
			}

			sectionStack.push(newSection);
		} else if (trimmedLine !== '---' && trimmedLine !== '***' && trimmedLine !== '___' && sectionStack.length > 0) {
			const currentSection = sectionStack[sectionStack.length - 1];
			
			if (trimmedLine.startsWith('- ')) {
				const cleanLine = trimmedLine.replace(/^-\s*/, '');
				if (cleanLine.trim()) {
					currentSection.content.push(`__BULLET__${cleanLine.trim()}`);
				}
			} else if (line.match(/^ {2,}/) && !trimmedLine.startsWith('**')) {
				const cleanLine = trimmedLine.replace(/^[•·○*]\s*/, '');
				if (cleanLine.trim()) {
					currentSection.content.push(`__NESTED__${cleanLine.trim()}`);
				}
			} else if (trimmedLine.startsWith('*') && !trimmedLine.startsWith('**')) {
				const cleanLine = trimmedLine.replace(/^\*\s*/, '');
				if (cleanLine.trim()) {
					currentSection.content.push(`__BULLET__${cleanLine.trim()}`);
				}
			} else {
				currentSection.content.push(trimmedLine);
			}
		}
	}

	if (sections.length === 0 && content?.trim()) {
		return [{ emoji: '📄', title: 'Contenu', content: content.split('\n').map(l => l.trim()).filter(Boolean), level: 1, subsections: [] }];
	}

	return sections;
}

export function getArticleId(article: Article): string | number {
	const id = article.id ?? article.article_id;
	if (id !== null && id !== undefined) {
		return id;
	}
	return Date.now() + Math.random();
}