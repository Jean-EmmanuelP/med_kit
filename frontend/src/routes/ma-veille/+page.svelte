<script lang="ts">
	import { i18n } from '$lib/i18n';

	let { data } = $props();
	console.log('Received data from server:', data);

	let searchQuery = $state('');
	let showOlderArticles = $state(false);
	let expandedArticleId = $state(null);
	let selectedFilter = $state('Tout');
	let filteredRecentArticles = $state([]);
	let filteredOlderArticles = $state([]);

	const today = new Date();
	const formattedDate = `${today.getDate().toString().padStart(2, '0')}/${(today.getMonth() + 1).toString().padStart(2, '0')}/${today.getFullYear()}`;

	function formatTitle(title: string) {
		if (!title) return '';
		const words = title.toLowerCase().split(' ');
		if (words.length === 0) return '';
		words[0] = words[0].charAt(0).toUpperCase() + words[0].slice(1);
		return words.join(' ');
	}

	function parseContent(content) {
		if (!content) return [];
		const sections = [];
		let currentSection = { emoji: '', title: '', content: [] };
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
				currentSection = { emoji, title: titleParts.join(' ').trim(), content: [] };
			} else if (line.trim() && inSection) {
				currentSection.content.push(line.trim());
			}
		}
		if (inSection && (currentSection.title || currentSection.content.length > 0)) {
			sections.push(currentSection);
		}
		return sections;
	}

	function formatDate(publishedAt) {
		if (!publishedAt) return 'Non spécifiée';
		const date = new Date(publishedAt);
		return `${date.getDate().toString().padStart(2, '0')}/${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getFullYear()}`;
	}

	function extractTitleEmoji(content) {
		if (!content) return '📝';
		const lines = content.split('\n');
		for (const line of lines) {
			if (line.trim().startsWith('# 📝')) {
				const [emoji] = line.trim().split(' ').slice(1);
				return emoji || '📝';
			}
		}
		return '📝';
	}

	function dedupeArticles(articles) {
		const articleMap = new Map();
		for (const article of articles || []) {
			if (!articleMap.has(article.id)) articleMap.set(article.id, article);
		}
		return Array.from(articleMap.values());
	}

	// Filtrer les articles (sans dépendre de showOlderArticles dans cet effet)
	$effect(() => {
		if (!data.recentArticles && !data.olderArticles) return;

		const filterArticles = (articles) =>
			articles.filter(
				(article) =>
					(selectedFilter === 'Tout' ||
						(selectedFilter === 'Favoris' && data.savedArticleIds.includes(article.id)) ||
						article.disciplines.includes(selectedFilter)) &&
					(!searchQuery || article.title.toLowerCase().includes(searchQuery.toLowerCase()))
			);

		filteredRecentArticles = filterArticles(dedupeArticles(data.recentArticles));
		filteredOlderArticles = filterArticles(dedupeArticles(data.olderArticles)); // Toujours filtrer, mais pas assigner si showOlderArticles est faux
	});

	// Mettre à jour showOlderArticles indépendamment
	$effect(() => {
		const shouldShow = filteredRecentArticles.length === 0 && filteredOlderArticles.length > 0;
		if (showOlderArticles !== shouldShow) {
			showOlderArticles = shouldShow;
			console.log('Updated showOlderArticles to:', showOlderArticles);
		}
	});

	function toggleSummary(articleId) {
		expandedArticleId = expandedArticleId === String(articleId) ? null : String(articleId);
	}
</script>

<div class="min-h-screen bg-gray-50 px-4 py-12">
	<div class="mx-auto max-w-4xl">
		<div class="mb-4 flex items-center">
			<svg
				class="mr-2 h-6 w-6 text-gray-600"
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
			<span class="text-lg text-gray-600">Date / {formattedDate}</span>
		</div>
		<h1 class="mb-4 text-3xl font-bold text-gray-800">{$i18n.header.myVeille}</h1>
		<h2 class="max-w-3xl">
			description de la page: voir ses articles favoris et specialites choisis. feature: section
			nouvel article (article du jour) et en bas tout les articles selon le filtre quil a rempli.
		</h2>

		<div
			class="mb-8 flex flex-col items-start space-y-4 sm:flex-row sm:items-center sm:space-y-0 sm:space-x-4"
		>
			<div class="flex w-full flex-col space-y-2 sm:w-auto sm:flex-row sm:space-y-0 sm:space-x-2">
				<form class="relative w-full sm:w-64">
					<input
						type="text"
						bind:value={searchQuery}
						placeholder={$i18n.header.searchPlaceholder}
						class="w-full rounded-full border border-gray-300 px-4 py-2 pr-12 font-sans text-sm transition-all duration-200 focus:border-gray-500 focus:ring focus:ring-gray-200"
					/>
					<svg
						class="absolute top-1/2 right-3 h-5 w-5 -translate-y-1/2 transform text-gray-500"
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
				<select
					bind:value={selectedFilter}
					class="w-full rounded border px-3 py-2 transition-all duration-200 focus:border-gray-500 focus:ring focus:ring-gray-200 sm:w-48"
				>
					<option value="Tout">Tout</option>
					<option value="Favoris">Favoris</option>
					{#each data.userDisciplines as discipline}
						<option value={discipline}>{discipline}</option>
					{/each}
				</select>
			</div>
		</div>

		{#if data.error}
			<p class="text-red-500">Erreur : {data.error}</p>
		{:else if filteredRecentArticles.length === 0 && filteredOlderArticles.length === 0}
			<p class="text-gray-600">
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
						class="relative rounded bg-white p-4 shadow transition-shadow hover:shadow-md"
					>
						<div
							class={`absolute ${String(article.id) === expandedArticleId ? 'top-[12%]' : 'top-1/2'} right-4 -translate-y-1/2`}
						>
							{#if expandedArticleId === String(article.id)}
								<svg
									class="h-4 w-4"
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
									class="h-4 w-4"
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
						<h2 class="text-left text-lg font-bold text-gray-800">
							{extractTitleEmoji(article.content)}
							{formatTitle(article.title)}
						</h2>
						{#if article.grade}
							<p class="mt-1 text-sm text-green-600">Grade de recommandation : {article.grade}</p>
						{/if}
						<button class="mt-2 flex items-center text-sm text-gray-600">
							<span class="mr-1">{article.journal || 'Inconnu'}</span>
						</button>
						{#if expandedArticleId === String(article.id)}
							<div class="prose mt-2 max-w-none text-gray-700">
								{#each parseContent(article.content) as section}
									<div class="mb-2">
										<h3 class="text-md flex items-center font-semibold text-gray-800">
											<span class="mr-2">{section.emoji}</span>
											{section.title}
										</h3>
										{#each section.content as paragraph}
											<p class="mt-1 text-sm">{paragraph}</p>
										{/each}
									</div>
								{/each}
							</div>
							<a
								href={`/articles/${article.id}`}
								class="mt-3 inline-block rounded bg-blue-600 px-4 py-2 text-white transition-colors duration-200 hover:bg-blue-700"
							>
								Voir l'article
							</a>
						{/if}
						<div class="mt-2 flex items-center text-sm text-gray-600">
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
						<li class="relative rounded bg-white p-4 shadow transition-shadow hover:shadow-md">
							<h2 class="text-left text-lg font-bold text-gray-800">
								{extractTitleEmoji(article.content)}
								{formatTitle(article.title)}
							</h2>
							{#if article.grade}
								<p class="mt-1 text-sm text-green-600">Grade de recommandation : {article.grade}</p>
							{/if}
							<button
								on:click={() => toggleSummary(article.id)}
								class="mt-2 flex items-center text-sm text-gray-600 hover:underline"
							>
								<span class="mr-1">{article.journal || 'Inconnu'}</span>
							</button>
							{#if expandedArticleId === String(article.id)}
								<div class="prose mt-2 max-w-none text-gray-700">
									{#each parseContent(article.content) as section}
										<div class="mb-2">
											<h3 class="text-md flex items-center font-semibold text-gray-800">
												<span class="mr-2">{section.emoji}</span>
												{section.title}
											</h3>
											{#each section.content as paragraph}
												<p class="mt-1 text-sm">{paragraph}</p>
											{/each}
										</div>
									{/each}
								</div>
								<a
									href={`/articles/${article.id}`}
									class="mt-3 inline-block rounded bg-blue-600 px-4 py-2 text-white transition-colors duration-200 hover:bg-blue-700"
								>
									Voir l'article
								</a>
							{/if}
							<div class="mt-2 flex items-center text-sm text-gray-600">
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
								<span class="mr-1">Date de parution :</span>
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
						class="mt-6 rounded bg-gray-200 px-4 py-2 text-gray-800 transition-colors duration-200 hover:bg-gray-300"
					>
						Voir moins
					</button>
				{:else}
					<button
						on:click={() => (showOlderArticles = true)}
						class="mt-6 rounded bg-gray-200 px-4 py-2 text-gray-800 transition-colors duration-200 hover:bg-gray-300"
					>
						Faites défiler pour voir les articles précédents
					</button>
				{/if}
			{/if}
		{/if}
	</div>
</div>
