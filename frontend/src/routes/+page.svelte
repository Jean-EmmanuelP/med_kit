<script>
	import { i18n } from '$lib/i18n';
	import userProfileStore from '$lib/stores/user';
	import { goto } from '$app/navigation';

	// Récupération des props avec $props rune
	const { data } = $props();

	// Définir les variables réactives avec $state
	let articles = $state(data.articles || []); // Initialisé avec les données du serveur
	let specialties = $state(data.specialties || []); // Rempli par le serveur
	let searchQuery = $state('');
	let selectedSpecialty = $state(specialties[0] || ''); // Utilise la première spécialité si disponible
	let expandedArticleId = $state(null);

	// Function to handle the "Ma veille" or "S'inscrire" button click
	function handleVeilleClick(event) {
		event.preventDefault();
		if (!userProfileStore) {
			goto('/signup');
		} else {
			goto('/ma-veille');
		}
	}

	// Fonctions utilitaires pour le formatage
	function formatTitle(title) {
		if (!title) return '';
		const words = title.toLowerCase().split(' ');
		if (words.length === 0) return '';
		words[0] = words[0].charAt(0).toUpperCase() + words[0].slice(1);
		return words.join(' ');
	}

	function parseContent(content) {
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
				currentSection = {
					emoji: emoji || '📝',
					title: titleParts.join(' ').trim(),
					content: []
				};
			} else if (line.trim() && inSection) {
				currentSection.content.push(line.trim());
			}
		}
		if (inSection && (currentSection.title || currentSection.content.length > 0)) {
			sections.push(currentSection);
		}
		return sections;
	}

	function extractTitleEmoji(content) {
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

	function formatDate(publishedAt) {
		if (!publishedAt) return 'Non spécifiée';
		const date = new Date(publishedAt);
		return `${date.getDate().toString().padStart(2, '0')}/${(date.getMonth() + 1)
			.toString()
			.padStart(2, '0')}/${date.getFullYear()}`;
	}

	function toggleSummary(articleId) {
		expandedArticleId = expandedArticleId === articleId ? null : articleId;
	}

	// Filtrer les articles de manière réactive avec $effect
	$effect(() => {
		let filtered = data.articles || [];
		if (searchQuery) {
			filtered = filtered.filter((article) =>
				article.title.toLowerCase().includes(searchQuery.toLowerCase())
			);
		}
		if (selectedSpecialty) {
			filtered = filtered.filter((article) => article.disciplines.includes(selectedSpecialty));
		}
		articles = filtered; // Mise à jour réactive
	});

	function selectSpecialty(specialty) {
		selectedSpecialty = specialty;
	}
</script>

<main
	class="relative flex min-h-screen flex-col bg-gradient-to-br from-gray-900 to-black text-white"
>
	<!-- Hero Section -->
	<div class="relative flex-auto space-y-12 bg-black px-6 py-16 md:px-20 md:py-20 lg:px-32 lg:py-24">
		<!-- Main content -->
		<div
			class="flex max-w-full flex-col items-center gap-10 text-center md:max-w-[70%] md:items-start md:text-left"
		>
			<!-- Subtitle with subtle animation -->
			<p class="font-sans text-lg font-light text-gray-300 md:text-xl">
				{$i18n.home.subtitle ||
					'Restez à jour avec la science médicale, sans vous noyer dans les 1 million d’articles publiés chaque année.'}
			</p>

			<!-- Question with emoji -->
			<p
				class="flex items-center justify-center gap-3 text-base text-gray-200 md:justify-start md:text-lg"
			>
				<span class="animate-bounce text-2xl text-yellow-400">🩺</span>
				{$i18n.home.phrase1 || 'Médecin traitant débordé par les revues scientifiques ?'}
			</p>

			<!-- Highlighted section: La solution pour les médecins -->
			<div class="flex w-full flex-col gap-6">
				<p
					class="flex items-center justify-center gap-3 text-xl font-semibold text-white md:justify-start md:text-2xl"
				>
					<span class="text-2xl text-teal-400">⚡</span>
					{$i18n.home.phrase2 || 'Nous analysons et résumons la science pour vous.'}
				</p>
				<ul class="space-y-4">
					{#each $i18n.home.arguments?.list || ['Tri intelligent des articles de PubMed, Cochrane et plus.', 'Résumés générés par IA, simples et rapides à lire.', 'Suivi personnalisé des sujets qui vous intéressent.', 'Gain de temps pour intégrer la science dans votre pratique.'] as argument}
						<li
							class="flex items-start justify-center gap-3 text-base text-gray-300 md:justify-start md:text-lg"
						>
							<span class="text-xl text-teal-400">✔</span>
							{argument}
						</li>
					{/each}
				</ul>
			</div>

			<!-- Timing note with emoji -->
			<p
				class="flex items-center justify-center gap-3 text-base text-gray-200 md:justify-start md:text-lg"
			>
				<span class="text-2xl text-red-400">📩</span>
				{$i18n.home.arguments?.cta || 'Recevez l’essentiel chaque jour, en 5 minutes de lecture.'}
			</p>

			<!-- CTA Button with Algorand-inspired styling: clean, bold, professional -->
			<div class="mt-8">
				<a
					href={userProfileStore ? '/ma-veille' : '/signup'}
					on:click={handleVeilleClick}
					class="inline-block w-[60vw] rounded-full bg-gradient-to-r from-blue-500 to-teal-500 px-8 py-3 text-center text-base font-semibold text-white shadow-lg transition-all duration-300 hover:from-blue-600 hover:to-teal-600 hover:shadow-xl md:w-auto md:px-12 md:py-4 md:text-lg"
				>
					{userProfileStore
						? $i18n.home.hero?.viewArticles || 'Accéder à ma veille'
						: $i18n.home.hero?.signupForVeille || 'S’inscrire maintenant'}
				</a>
			</div>
		</div>
	</div>

		<!-- Section des spécialités en bulles défilantes adaptée au marquee crypto -->
		<div class="relative bg-black py-8 overflow-hidden">
			<h2 class="mb-4 text-center text-2xl font-bold text-white">Choisissez votre spécialité</h2>
			<div class="marquee-container relative overflow-hidden whitespace-nowrap">
				<div class="marquee-content animate-marquee inline-block">
					{#each specialties as specialty (specialty)}
					<button
						on:click={() => selectSpecialty(specialty)}
						class="mx-4 inline-block rounded-full bg-gray-800 px-6 py-3 text-lg font-medium text-white shadow-md transition-all hover:bg-gray-700 {selectedSpecialty === specialty ? 'bg-gray-600' : ''}"
					>
						{specialty}
					</button>
				{/each}
				<!-- Duplication pour effet de défilement continu -->
				{#each specialties as specialty (specialty)}
					<button
						on:click={() => selectSpecialty(specialty)}
						class="mx-4 inline-block rounded-full bg-gray-800 px-6 py-3 text-lg font-medium text-white shadow-md transition-all hover:bg-gray-700 {selectedSpecialty === specialty ? 'bg-gray-600' : ''}"
						aria-hidden="true"
					>
						{specialty}
					</button>
				{/each}
			</div>
			<div class="absolute inset-0 pointer-events-none bg-gradient-to-r from-black via-transparent to-black"></div>
		</div>
	
		<!-- Section des articles -->
		<div class="bg-black px-6 py-12 text-white">
			<div class="mx-auto max-w-4xl">
				<div class="mb-8 flex flex-col items-start space-y-4 sm:flex-row sm:items-center sm:space-y-0 sm:space-x-4">
					<h2 class="text-3xl font-bold">Découvrez les derniers articles</h2>
					<div class="flex w-full flex-col space-y-2 sm:w-auto sm:flex-row sm:space-y-0 sm:space-x-2">
						<form class="relative w-full sm:w-64">
							<input
								type="text"
							bind:value={searchQuery}
							placeholder="Rechercher un article..."
							class="w-full rounded-full border border-gray-700 bg-gray-800 px-4 py-2 pr-12 text-sm text-white transition-all duration-200 focus:border-gray-600 focus:ring focus:ring-gray-700"
						/>
						<svg class="absolute top-1/2 right-3 h-5 w-5 -translate-y-1/2 transform text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
						</svg>
					</div>
				</div>
	
				<!-- Liste des articles -->
				{#if articles.length === 0}
					<p class="text-gray-400">Aucun article disponible pour {selectedSpecialty}.</p>
				{:else}
					<ul class="space-y-4">
						{#each articles as article}
							<li on:click={() => toggleSummary(article.id)} class="relative rounded bg-gray-800 p-4 shadow transition-shadow hover:shadow-xl">
								<h3 class="text-left text-lg font-bold text-white">
								{extractTitleEmoji(article.content)}
								{formatTitle(article.title)}
							</h3>
							{#if article.grade}
								<p class="text-sm text-green-400">Grade de recommandation : {article.grade}</p>
							{/if}
							<div class="mt-2 flex items-center text-sm text-gray-400">
								<span class="mr-1">{article.journal || 'Inconnu'}</span>
							</div>
							{#if expandedArticleId === article.id}
								<div class="prose mt-2 max-w-none text-gray-200">
									{#each parseContent(article.content) as section}
										<div class="mb-2">
										<h4 class="flex items-center font-semibold text-white">
										<span class="mr-2">{section.emoji}</span>{section.title}
									</h4>
									{#each section.content as paragraph}
										<p class="mt-1 text-sm">{paragraph}</p>
									{/each}
								</div>
							{/each}
							</div>
							{/if}
						</li>
					{/each}
				</ul>
				{/if}
			</div>
		</div>

	<!-- Decorative element inspired by Algorand's sleek footer gradient -->
	<div
		class="absolute right-0 bottom-0 left-0 h-2 bg-gradient-to-r from-blue-500 via-teal-500 to-transparent opacity-60"
	></div>
</main>
<style>
	/* Fade-in animation for subtitle */
	@keyframes fade-in {
		0% { opacity: 0; transform: translateY(15px); }
		100% { opacity: 1; transform: translateY(0); }
	}
	.animate-fade-in { animation: fade-in 1.2s ease-out; }

	/* Bounce animation for emojis */
	@keyframes bounce {
		0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
		40% { transform: translateY(-12px); }
		60% { transform: translateY(-6px); }
	}
	.animate-bounce { animation: bounce 2.5s infinite; }

	/* Marquee animation for specialties */
	@keyframes marquee {
		0% { transform: translateX(0); }
		100% { transform: translateX(-50%); }
	}

	.marquee-container {
		position: relative;
		height: 80px;
	}

	.marquee-content {
		display: inline-block;
		white-space: nowrap;
	}

	.animate-marquee {
		animation: marquee 70s linear infinite;
	}

	.marquee-container:hover .animate-marquee {
		animation-play-state: paused;
	}
</style>
