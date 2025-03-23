<script lang="ts">
	import * as Select from '$lib/components/ui/select';
	    
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
    const disciplines = data.disciplines;
    
    let articles = $state<Article[]>([]);
    let selectedDiscipline = $state(disciplines.length > 0 ? disciplines[0].name : null);
    let expandedArticleId = $state<string | null>(null);
    let immersiveArticle = $state(null);
    let articleOfTheDay = $state<Article[]>([]);

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

    function parseContent(content: string) {
        if (!content || typeof content !== 'string') return [];
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

    function openImmersive(article) {
        immersiveArticle = article;
        document.body.classList.add('overflow-hidden');
    }

    function closeImmersive() {
        immersiveArticle = null;
        document.body.classList.remove('overflow-hidden');
    }

    $effect(()=>{
        if (!selectedDiscipline) return;
        
        fetch(`/api/get_articles_my_veille?specialty=${selectedDiscipline}`)
            .then((res) => res.json())
            .then((data) => {
                console.log(data.data);
                if (data && data.data) {
                    articleOfTheDay = [data.data[0]];
                    articles = data.data.slice(1);
                }
            })
            .catch(error => {
                console.error("Error fetching articles:", error);
        });
    });
</script>


<div class="min-h-screen bg-black px-4 py-12 text-white">
	<div class="mx-auto max-w-4xl">
        <div class="mb-6">
            {#if disciplines.length > 0}
                <div class="relative w-full max-w-sm">
                    <Select.Root type="single" name="selectedFilter" bind:value={selectedDiscipline} class="w-full">
                        <Select.Trigger
                            class="w-full rounded-lg border-gray-700 bg-gray-800 px-4 py-3 text-sm font-medium text-white shadow-md transition-all duration-300 hover:bg-gray-700 focus:ring-2 focus:ring-teal-500 focus:outline-none"
                        >
                            {selectedDiscipline}
                        </Select.Trigger>
                        <Select.Content
                            class="scrollbar-thin scrollbar-thumb-teal-500 scrollbar-track-gray-800 max-h-60 overflow-y-auto rounded-lg border border-gray-700 bg-gray-900"
                        >
                            <Select.Group>
                                <Select.GroupHeading class="px-4 py-2 font-semibold text-gray-400"
                                    >Spécialités</Select.GroupHeading
                                >
                                {#each disciplines as discipline}
                                    <Select.Item
                                        value={discipline.name}
                                        label={discipline.name}
                                        class="cursor-pointer px-4 py-2 text-white transition-all duration-200 hover:bg-teal-600 hover:text-white"
                                    />
                                {/each}
                            </Select.Group>
                        </Select.Content>
                    </Select.Root>
                </div>
            {:else}
                <p>No disciplines available</p>
            {/if}
        </div>

        <!-- Article du jour -->
        <div class="mb-6">
            {#if articleOfTheDay.length > 0}
            <h2 class="text-2xl font-bold text-teal-500">🔥 Article du jour</h2>
                <p class="mt-2 text-gray-400">Article selectionné aujourd'hui pour {selectedDiscipline} :</p>
                {#each articleOfTheDay as article (article.id)}
                    {#if article }
                        <li
                            on:click={() => openImmersive(article)}
                            class="relative mt-2 list-none cursor-pointer rounded bg-gray-800 p-4 shadow transition-shadow hover:shadow-xl"
                        >
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
            {/if}
        </div>

        <!-- Articles précédents -->
        <div class="mb-6">
            {#if articles.length > 0}
            <h2 class="text-2xl font-bold text-teal-500">📖 Articles des jours précédents</h2>
                <p class="mt-2 text-gray-400">Article pour {selectedDiscipline} :</p>
                {#each articles as article (article.id)}
					{#if article }
						<li
							on:click={() => openImmersive(article)}
							class="relative mt-2 list-none cursor-pointer rounded bg-gray-800 p-4 shadow transition-shadow hover:shadow-xl"
						>
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
			{/if}
		</div>
    </div>

    <!-- Modal Immersif -->
    {#if immersiveArticle}
        <div
            class="fixed inset-0 z-[200] flex items-center justify-center bg-black/30 backdrop-blur-sm"
        >
            <div
                class="relative max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-2xl bg-gray-900 p-8 shadow-2xl"
            >
                <button
                    class="absolute top-4 right-4 text-3xl text-gray-400 hover:text-white focus:outline-none"
                    on:click={closeImmersive}
                >
                    ×
                </button>
                <h2 class="mb-4 text-3xl font-bold text-white">
                    {extractTitleEmoji(immersiveArticle.content)}
                    {formatTitle(immersiveArticle.title)}
                </h2>
                {#if immersiveArticle.grade}
                    <p class="mb-2 text-sm text-green-400">
                        Grade de recommandation : {immersiveArticle.grade}
                    </p>
                {/if}
                <div class="mt-2 flex flex-row items-center text-sm">
                    <span class="mr-1">{immersiveArticle.journal || 'Inconnu'}</span>
                </div>
                <p class="mt-2 mb-4 text-sm text-gray-400">
                    Publié le : {formatDate(immersiveArticle.published_at)}
                </p>
                {#each parseContent(immersiveArticle.content) as section}
                    <div class="mb-6">
                        <h3 class="mb-2 flex items-center text-lg font-semibold text-white">
                            <span class="mr-2">{section.emoji}</span>
                            {section.title}
                        </h3>
                        <ul class="ml-4 list-disc space-y-2 text-gray-300">
                            {#each section.content as paragraph}
                                <li>{paragraph}</li>
                            {/each}
                        </ul>
                    </div>
                {/each}
                {#if immersiveArticle.link}
                    <a href={immersiveArticle.link} target="_blank" class="text-white underline">
                        Accédez à l'article original 🔎
                    </a>
                {/if}
            </div>
        </div>
    {/if}
</div>