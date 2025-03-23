<script lang="ts">
	import { goto } from '$app/navigation';
	import * as Select from '$lib/components/ui/select';
	import { i18n } from '$lib/i18n';
	import userProfileStore from '$lib/stores/user';

	// Define article interface
	interface Article {
		id: string | number;
		title: string;
		content: string;
		disciplines: string[];
		published_at: string;
		journal?: string;
		grade?: string;
		link?: string;
	}

	const { data } = $props();
	console.log('Received data from server:', data);

	let searchQuery = $state('');
	let showOlderArticles = $state(false);
	let expandedArticleId = $state<string | null>(null);
	let selectedFilter = $state('Tout');
	let filteredRecentArticles = $state<Article[]>([]);
	let filteredOlderArticles = $state<Article[]>([]);
	let articleOfTheDay = $state<Article[]>([]);
	let showSignupPrompt = $state(false);

	let specialties = $state<string[]>(
		[
			...new Set<string>([
				...(data.userDisciplines || []),
				...(data.recentArticles?.flatMap((a: any) => a.disciplines) || []),
				...(data.olderArticles?.flatMap((a: any) => a.disciplines) || [])
			])
		].sort((a, b) => a.localeCompare(b, 'fr', { sensitivity: 'base' }))
	);
	let triggerContent = $derived(
		specialties.find((s) => s === selectedFilter) ?? 'Choisis une spécialité'
	);

	const today = new Date();
	const formattedDate = `${today.getDate().toString().padStart(2, '0')}/${(today.getMonth() + 1)
		.toString()
		.padStart(2, '0')}/${today.getFullYear()}`;

	interface ContentSection {
		emoji: string;
		title: string;
		content: string[];
	}

	function parseContent(content: string): ContentSection[] {
		if (!content || typeof content !== 'string') return [];
		const sections: ContentSection[] = [];
		let currentSection: ContentSection = { emoji: '', title: '', content: [] };
		const lines = content.split('\n');
		let inSection = false;

		for (const line of lines) {
			if (
				line.trim().startsWith('## 📝') ||
				line.trim().startsWith('## 📌') ||
				line.trim().startsWith('## 🧪') ||
				line.trim().startsWith('## 📊') ||
				line.trim().startsWith('## 🩺') ||
				line.trim().startsWith('## 📖')
			) {
				if (inSection && (currentSection.title || currentSection.content.length > 0)) {
					sections.push(currentSection);
				}
				inSection = true;
				const [emoji, ...titleParts] = line
					.trim()
					.replace(/^##\s*/, '')
					.split(' ');
				currentSection = { emoji: emoji || '📝', title: titleParts.join(' ').trim(), content: [] };
			} else if (line.trim() && inSection) {
				currentSection.content.push(line.trim());
			}
		}
		if (inSection && (currentSection.title || currentSection.content.length > 0)) {
			sections.push(currentSection);
		}
		return sections;
	}

	function formatTitle(title: string) {
		if (!title) return '';
		const words = title.toLowerCase().split(' ');
		if (words.length === 0) return '';
		words[0] = words[0].charAt(0).toUpperCase() + words[0].slice(1);
		return words.join(' ');
	}

	function formatDate(publishedAt: string) {
		if (!publishedAt) return 'Non spécifiée';
		const date = new Date(publishedAt);
		return `${date.getDate().toString().padStart(2, '0')}/${(date.getMonth() + 1)
			.toString()
			.padStart(2, '0')}/${date.getFullYear()}`;
	}

	function extractTitleEmoji(content: string) {
		if (!content || typeof content !== 'string') return '📝';
		const lines = content.split('\n');
		for (const line of lines) {
			if (
				line.trim().startsWith('# 📝') ||
				line.trim().startsWith('# 📌') ||
				line.trim().startsWith('# 🧪') ||
				line.trim().startsWith('# 📊') ||
				line.trim().startsWith('# 🩺') ||
				line.trim().startsWith('# 📖')
			) {
				const [emoji] = line.trim().split(' ').slice(1);
				return emoji || '📝';
			}
		}
		return '📝';
	}

	function dedupeArticles(articles: Article[]) {
		const articleMap = new Map<string | number, Article>();
		for (const article of articles || []) {
			if (!articleMap.has(article.id)) articleMap.set(article.id, article);
		}
		return Array.from(articleMap.values());
	}

	$effect(() => {
		if (!data.recentArticles && !data.olderArticles) return;

		const filterArticles = (articles: Article[]) =>
			articles.filter(
				(article) =>
					(selectedFilter === 'Tout' ||
						(selectedFilter === 'Favoris' && data.savedArticleIds.includes(article.id)) ||
						article.disciplines.includes(selectedFilter)) &&
					(!searchQuery || article.title.toLowerCase().includes(searchQuery.toLowerCase()))
			);

		filteredRecentArticles = filterArticles(dedupeArticles(data.recentArticles));
		filteredOlderArticles = filterArticles(dedupeArticles(data.olderArticles));
	});

	$effect(() => {
		const shouldShow = filteredRecentArticles.length === 0 && filteredOlderArticles.length > 0;
		if (showOlderArticles !== shouldShow) {
			showOlderArticles = shouldShow;
			console.log('Updated showOlderArticles to:', showOlderArticles);
		}
	});

	$effect(() => {
		const timer = setTimeout(() => {
			showSignupPrompt = true;
		}, 2000);
		return () => clearTimeout(timer);
	});

	$effect(() => {
		if ($userProfileStore) {
			showSignupPrompt = false;
		}
	});

	$effect(() => {
		if (selectedFilter != "Tout" && selectedFilter != "Favoris") {
			fetch(`/api/get_articles_my_veille?specialty=${selectedFilter}`)
				.then((res) => res.json())
				.then((data) => {
					console.log(data.data);
					if (data && data.data) {
						// Set the first article as article of the day
						articleOfTheDay = [data.data[0]];
						console.log(articleOfTheDay)
						
						const remainingArticles = data.data.slice(1);
						filteredRecentArticles = remainingArticles;
					}
				})
				.catch(error => {
					console.error("Error fetching articles:", error);
				});
		}
	});

	function toggleSummary(articleId: string | number) {
		expandedArticleId = expandedArticleId === String(articleId) ? null : String(articleId);
	}

	function handleSignup() {
		goto('/signup');
	}
</script>

<div class="min-h-screen bg-black px-4 py-12 text-white">
	<div class="mx-auto max-w-4xl">
		<!-- Signup Prompt -->
		{#if showSignupPrompt && !$userProfileStore}
			<div
				class="mb-6 flex items-center justify-between rounded-lg bg-teal-600/20 p-4 shadow-md transition-all duration-300 hover:bg-teal-600/30"
			>
				<p class="text-sm font-medium">S'inscrire maintenant pour plus de fonctionnalités !</p>
				<button
					on:click={handleSignup}
					class="group flex inline-block items-center justify-center gap-2 rounded-full bg-teal-500 px-4 py-2 text-xs font-semibold text-white transition-all duration-200 hover:bg-teal-600"
				>
					<span>S'inscrire</span>
					<svg
						class="h-5 w-5 transition-transform duration-300 group-hover:translate-x-1"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
						xmlns="http://www.w3.org/2000/svg"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M9 5l7 7m0 0l-7 7m7-7H3"
						/>
					</svg>
				</button>
			</div>
		{/if}

		<div class="mb-4 flex items-center">
			<svg
				class="mr-2 h-6 w-6 text-gray-400"
				fill="none"
				stroke="currentColor"
				viewBox="0 0 24 24"
				xmlns="http://www.w3.org/2000/svg"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
				/>
			</svg>
			<span class="text-lg text-gray-400">Date / {formattedDate}</span>
		</div>
		<h1 class="mb-4 text-3xl font-bold text-white">{$i18n.header.myVeille}</h1>

		<!-- Replace Tabs with Dropdown -->
		<div class="mb-6">
			<div class="relative w-full max-w-sm">
				<Select.Root type="single" name="selectedFilter" bind:value={selectedFilter}>
					<Select.Trigger
						class="w-full rounded-lg border-gray-700 bg-gray-800 px-4 py-3 text-sm font-medium text-white shadow-md transition-all duration-300 hover:bg-gray-700 focus:ring-2 focus:ring-teal-500 focus:outline-none"
					>
						{triggerContent}
					</Select.Trigger>
					<Select.Content
						class="scrollbar-thin scrollbar-thumb-teal-500 scrollbar-track-gray-800 max-h-60 overflow-y-auto rounded-lg border border-gray-700 bg-gray-900"
					>
						<Select.Group>
							<Select.GroupHeading class="px-4 py-2 font-semibold text-gray-400"
								>Spécialités</Select.GroupHeading
							>
							<!-- <Select.Item
								value="Tout"
								label="Tout"
								class="cursor-pointer px-4 py-2 text-white transition-all duration-200 hover:bg-teal-600 hover:text-white"
							/>
							<Select.Item
								value="Favoris"
								label="Favoris"
								class="cursor-pointer px-4 py-2 text-white transition-all duration-200 hover:bg-teal-600 hover:text-white"
							/> -->
							{#each data.userDisciplines as discipline}
								<Select.Item
									value={discipline}
									label={discipline}
									class="cursor-pointer px-4 py-2 text-white transition-all duration-200 hover:bg-teal-600 hover:text-white"
								/>
							{/each}
						</Select.Group>
					</Select.Content>
				</Select.Root>
			</div>
		</div>

		<!-- Nouveaux Articles Section -->
		<div class="mb-6">
			<h2 class="text-2xl font-bold text-teal-500">🔥 Les nouveaux articles</h2>
			{#if articleOfTheDay.length > 0}
				<p class="mt-2 text-gray-400">Article du jour pour {selectedFilter} :</p>
				{#each articleOfTheDay as article (article.id)}
					{#if article }
						<li
							on:click={() => toggleSummary(article.id)}
							class="relative mt-2 list-none rounded bg-gray-800 p-4 shadow transition-shadow hover:shadow-lg"
						>
							<div
								class={`absolute ${String(article.id) === expandedArticleId ? 'top-[12%]' : 'top-1/2'} right-4 -translate-y-1/2`}
							>
								{#if expandedArticleId === String(article.id)}
									<svg
										class="h-4 w-4 text-white"
										fill="none"
										stroke="currentColor"
										viewBox="0 0 24 24"
										xmlns="http://www.w3.org/2000/svg"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M5 15l7-7 7 7"
										/>
									</svg>
								{:else}
									<svg
										class="h-4 w-4 text-white"
										fill="none"
										stroke="currentColor"
										viewBox="0 0 24 24"
										xmlns="http://www.w3.org/2000/svg"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M19 9l-7 7-7-7"
										/>
									</svg>
								{/if}
							</div>
							<h2 class="text-left text-lg font-bold text-white">
								{extractTitleEmoji(article.content)}
								{formatTitle(article.title)}
							</h2>
							{#if article.grade}
								<p class="mt-1 text-sm text-green-400">Grade de recommandation : {article.grade}</p>
							{/if}
							<div class="mt-2 flex items-center text-sm text-gray-400">
								<span class="mr-1">{article.journal || 'Inconnu'}</span>
							</div>
							{#if expandedArticleId === String(article.id)}
								<div class="prose mt-2 max-w-none text-gray-200">
									{#each parseContent(article.content) as section}
										<div class="mb-2">
											<h3 class="text-md flex items-center font-semibold text-white">
												<span class="mr-2">{section.emoji}</span>
												{section.title}
											</h3>
											{#each section.content as paragraph}
												<p class="mt-1 text-sm">{paragraph}</p>
											{/each}
										</div>
									{/each}
								</div>
								<div class="mt-4 flex flex-col items-center gap-4 sm:flex-row">
									{#if article.link}
										<div class="flex items-center text-sm text-gray-400">
											<svg
												class="mr-1 h-4 w-4"
												fill="none"
												stroke="currentColor"
												viewBox="0 0 24 24"
												xmlns="http://www.w3.org/2000/svg"
											>
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
												/>
											</svg>
											<span class="mr-1">Lien :</span>
											<a
												href={article.link}
												target="_blank"
												rel="noopener noreferrer"
												class="max-w-xs truncate text-teal-400 hover:underline"
											>
												{article.link}
											</a>
										</div>
									{/if}
									{#if $userProfileStore}
										<a
											href={`/articles/${article.id}`}
											class="group flex inline-block items-center justify-center gap-2 rounded bg-teal-500 px-4 py-2 text-white transition-all duration-200 hover:bg-teal-600"
										>
											<span>Voir l'article</span>
											<svg
												class="h-5 w-5 transition-transform duration-300 group-hover:translate-x-1"
												fill="none"
												stroke="currentColor"
												viewBox="0 0 24 24"
												xmlns="http://www.w3.org/2000/svg"
											>
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													d="M9 5l7 7m0 0l-7 7m7-7H3"
												/>
											</svg>
										</a>
									{/if}
								</div>
							{/if}
							<div class="mt-2 flex items-center text-sm text-gray-400">
								<svg
									class="mr-1 h-4 w-4"
									fill="none"
									stroke="currentColor"
									viewBox="0 0 24 24"
									xmlns="http://www.w3.org/2000/svg"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
									/>
								</svg>
								<span class="mr-1">Date :</span>
								<span>{formatDate(article.published_at)}</span>
							</div>
						</li>
					{/if}
				{/each}
			{:else}
				<p class="mt-2 text-gray-400">Aucun article du jour pour {selectedFilter}.</p>
			{/if}
		</div>

		<!-- Barre de recherche -->
		<div
			class="mb-8 flex flex-col items-start space-y-4 sm:flex-row sm:items-center sm:space-y-0 sm:space-x-4"
		>
			<div class="flex w-full flex-col space-y-2 sm:w-auto sm:flex-row sm:space-y-0 sm:space-x-2">
				<form class="relative w-full sm:w-64">
					<input
						type="text"
						bind:value={searchQuery}
						placeholder={$i18n.header.searchPlaceholder}
						class="w-full rounded-full border border-gray-700 bg-gray-800 px-4 py-2 pr-12 text-sm text-white transition-all duration-200 focus:border-teal-500 focus:ring focus:ring-teal-700"
					/>
					<svg
						class="absolute top-1/2 right-3 h-5 w-5 -translate-y-1/2 transform text-gray-400"
						fill="none"
						stroke="currentColor"
						viewBox="0 0 24 24"
						xmlns="http://www.w3.org/2000/svg"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
						/>
					</svg>
				</form>
			</div>
		</div>

		{#if data.error}
			<p class="text-red-500">Erreur : {data.error}</p>
		{:else if filteredRecentArticles.length === 0 && filteredOlderArticles.length === 0}
			<p class="text-gray-400">
				Aucun article disponible pour {selectedFilter === 'Favoris'
					? 'vos favoris'
					: selectedFilter === 'Tout'
						? 'toutes les disciplines'
						: selectedFilter}.
			</p>
		{:else}
			<ul class="space-y-4">
				{#each filteredRecentArticles as article}
					<li
						on:click={() => toggleSummary(article.id)}
						class="relative rounded bg-gray-800 p-4 shadow transition-shadow hover:shadow-lg"
					>
						<div
							class={`absolute ${String(article.id) === expandedArticleId ? 'top-[12%]' : 'top-1/2'} right-4 -translate-y-1/2`}
						>
							{#if expandedArticleId === String(article.id)}
								<svg
									class="h-4 w-4 text-white"
									fill="none"
									stroke="currentColor"
									viewBox="0 0 24 24"
									xmlns="http://www.w3.org/2000/svg"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M5 15l7-7 7 7"
									/>
								</svg>
							{:else}
								<svg
									class="h-4 w-4 text-white"
									fill="none"
									stroke="currentColor"
									viewBox="0 0 24 24"
									xmlns="http://www.w3.org/2000/svg"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M19 9l-7 7-7-7"
									/>
								</svg>
							{/if}
						</div>
						<h2 class="text-left text-lg font-bold text-white">
							{extractTitleEmoji(article.content)}
							{formatTitle(article.title)}
						</h2>
						{#if article.grade}
							<p class="mt-1 text-sm text-green-400">Grade de recommandation : {article.grade}</p>
						{/if}
						<div class="mt-2 flex items-center text-sm text-gray-400">
							<span class="mr-1">{article.journal || 'Inconnu'}</span>
						</div>
						{#if expandedArticleId === String(article.id)}
							<div class="prose mt-2 max-w-none text-gray-200">
								{#each parseContent(article.content) as section}
									<div class="mb-2">
										<h3 class="text-md flex items-center font-semibold text-white">
											<span class="mr-2">{section.emoji}</span>
											{section.title}
										</h3>
										{#each section.content as paragraph}
											<p class="mt-1 text-sm">{paragraph}</p>
										{/each}
									</div>
								{/each}
							</div>
							<div class="mt-4 flex flex-col items-center gap-4 sm:flex-row">
								{#if article.link}
									<div class="flex items-center text-sm text-gray-400">
										<svg
											class="mr-1 h-4 w-4"
											fill="none"
											stroke="currentColor"
											viewBox="0 0 24 24"
											xmlns="http://www.w3.org/2000/svg"
										>
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												stroke-width="2"
												d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
											/>
										</svg>
										<span class="mr-1">Lien :</span>
										<a
											href={article.link}
											target="_blank"
											rel="noopener noreferrer"
											class="max-w-xs truncate text-teal-400 hover:underline"
										>
											{article.link}
										</a>
									</div>
								{/if}
								{#if $userProfileStore}
									<a
										href={`/articles/${article.id}`}
										class="group flex inline-block items-center justify-center gap-2 rounded bg-teal-500 px-4 py-2 text-white transition-all duration-200 hover:bg-teal-600"
									>
										<span>Voir l'article</span>
										<svg
											class="h-5 w-5 transition-transform duration-300 group-hover:translate-x-1"
											fill="none"
											stroke="currentColor"
											viewBox="0 0 24 24"
											xmlns="http://www.w3.org/2000/svg"
										>
											<path
												stroke-linecap="round"
												stroke-linejoin="round"
												stroke-width="2"
												d="M9 5l7 7m0 0l-7 7m7-7H3"
											/>
										</svg>
									</a>
								{/if}
							</div>
						{/if}
						<div class="mt-2 flex items-center text-sm text-gray-400">
							<svg
								class="mr-1 h-4 w-4"
								fill="none"
								stroke="currentColor"
								viewBox="0 0 24 24"
								xmlns="http://www.w3.org/2000/svg"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
								/>
							</svg>
							<span class="mr-1">Date :</span>
							<span>{formatDate(article.published_at)}</span>
						</div>
					</li>
				{/each}

				{#if showOlderArticles}
					{#each filteredOlderArticles as article}
						<li
							on:click={() => toggleSummary(article.id)}
							class="relative rounded bg-gray-800 p-4 shadow transition-shadow hover:shadow-lg"
						>
							<div
								class={`absolute ${String(article.id) === expandedArticleId ? 'top-[12%]' : 'top-1/2'} right-4 -translate-y-1/2`}
							>
								{#if expandedArticleId === String(article.id)}
									<svg
										class="h-4 w-4 text-white"
										fill="none"
										stroke="currentColor"
										viewBox="0 0 24 24"
										xmlns="http://www.w3.org/2000/svg"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M5 15l7-7 7 7"
										/>
									</svg>
								{:else}
									<svg
										class="h-4 w-4 text-white"
										fill="none"
										stroke="currentColor"
										viewBox="0 0 24 24"
										xmlns="http://www.w3.org/2000/svg"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											stroke-width="2"
											d="M19 9l-7 7-7-7"
										/>
									</svg>
								{/if}
							</div>
							<h2 class="text-left text-lg font-bold text-white">
								{extractTitleEmoji(article.content)}
								{formatTitle(article.title)}
							</h2>
							{#if article.grade}
								<p class="mt-1 text-sm text-green-400">Grade de recommandation : {article.grade}</p>
							{/if}
							<div class="mt-2 flex items-center text-sm text-gray-400">
								<span class="mr-1">{article.journal || 'Inconnu'}</span>
							</div>
							{#if expandedArticleId === String(article.id)}
								<div class="prose mt-2 max-w-none text-gray-200">
									{#each parseContent(article.content) as section}
										<div class="mb-2">
											<h3 class="text-md flex items-center font-semibold text-white">
												<span class="mr-2">{section.emoji}</span>
												{section.title}
											</h3>
											{#each section.content as paragraph}
												<p class="mt-1 text-sm">{paragraph}</p>
											{/each}
										</div>
									{/each}
								</div>
								<div class="mt-4 flex flex-col items-center gap-4 sm:flex-row">
									{#if article.link}
										<div class="flex items-center text-sm text-gray-400">
											<svg
												class="mr-1 h-4 w-4"
												fill="none"
												stroke="currentColor"
												viewBox="0 0 24 24"
												xmlns="http://www.w3.org/2000/svg"
											>
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
												/>
											</svg>
											<span class="mr-1">Lien :</span>
											<a
												href={article.link}
												target="_blank"
												rel="noopener noreferrer"
												class="max-w-xs truncate text-teal-400 hover:underline"
											>
												{article.link}
											</a>
										</div>
									{/if}
									{#if $userProfileStore}
										<a
											href={`/articles/${article.id}`}
											class="group flex inline-block items-center justify-center gap-2 rounded bg-teal-500 px-4 py-2 text-white transition-all duration-200 hover:bg-teal-600"
										>
											<span>Voir l'article</span>
											<svg
												class="h-5 w-5 transition-transform duration-300 group-hover:translate-x-1"
												fill="none"
												stroke="currentColor"
												viewBox="0 0 24 24"
												xmlns="http://www.w3.org/2000/svg"
											>
												<path
													stroke-linecap="round"
													stroke-linejoin="round"
													stroke-width="2"
													d="M9 5l7 7m0 0l-7 7m7-7H3"
												/>
											</svg>
										</a>
									{/if}
								</div>
							{/if}
							<div class="mt-2 flex items-center text-sm text-gray-400">
								<svg
									class="mr-1 h-4 w-4"
									fill="none"
									stroke="currentColor"
									viewBox="0 0 24 24"
									xmlns="http://www.w3.org/2000/svg"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
									/>
								</svg>
								<span class="mr-1">Date :</span>
								<span>{formatDate(article.published_at)}</span>
							</div>
						</li>
					{/each}
				{/if}
			</ul>
			{#if filteredOlderArticles.length > 0 && filteredRecentArticles.length > 0}
				{#if showOlderArticles}
					<button
						on:click={() => (showOlderArticles = false)}
						class="mt-6 rounded bg-gray-700 px-4 py-2 text-white transition-colors duration-200 hover:bg-gray-600"
					>
						Voir moins
					</button>
				{:else}
					<button
						on:click={() => (showOlderArticles = true)}
						class="mt-6 rounded bg-gray-700 px-4 py-2 text-white transition-colors duration-200 hover:bg-gray-600"
					>
						Faites défiler pour voir les articles précédents
					</button>
				{/if}
			{/if}
		{/if}
	</div>
</div>

<style>
	button:focus {
		outline: none;
	}
	.animate-bounce {
		animation: bounce 2s infinite;
	}

	@keyframes bounce {
		0%,
		20%,
		50%,
		80%,
		100% {
			transform: translateY(0);
		}
		40% {
			transform: translateY(-10px);
		}
		60% {
			transform: translateY(-5px);
		}
	}

	.modal-enter-active {
		animation: fadeIn 0.3s ease-out;
	}

	@keyframes fadeIn {
		0% {
			opacity: 0;
			transform: scale(0.95);
		}
		100% {
			opacity: 1;
			transform: scale(1);
		}
	}

	.scrollbar-thin {
		scrollbar-width: thin;
		scrollbar-color: #14b8a6 #1f2937;
	}

	.scrollbar-thin::-webkit-scrollbar {
		width: 8px;
	}

	.scrollbar-thin::-webkit-scrollbar-track {
		background: #1f2937;
	}

	.scrollbar-thin::-webkit-scrollbar-thumb {
		background-color: #14b8a6;
		border-radius: 6px;
		border: 2px solid #1f2937;
	}
</style>
