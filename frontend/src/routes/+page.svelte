<script>
	import EmbaseSvg from './../lib/svg/EmbaseSvg.svelte';
	import { i18n } from '$lib/i18n';
	import userProfileStore from '$lib/stores/user';
	import { goto } from '$app/navigation';

	// Récupération des props avec $props rune
	const { data } = $props();

	// Définir les variables réactives avec $state
	let articles = $state(data.articles || []);
	let specialties = $state(data.specialties || []);
	let searchQuery = $state('');
	let selectedSpecialty = $state(specialties[0] || '');
	let expandedArticleId = $state(null);
	let articleSection = $state(null);
	let immersiveArticle = $state(null);

	// Gestion du clic sur le bouton "Ma veille" ou "S'inscrire"
	function handleVeilleClick(event) {
		event.preventDefault();
		if (!$userProfileStore) {
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
		return `${date.getDate().toString().padStart(2, '0')}/${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getFullYear()}`;
	}

	function openImmersive(article) {
		immersiveArticle = article;
		document.body.classList.add('overflow-hidden');
	}

	function closeImmersive() {
		immersiveArticle = null;
		document.body.classList.remove('overflow-hidden');
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
		articles = filtered;
	});

	function selectSpecialty(specialty) {
		selectedSpecialty = specialty;
		if (articleSection) {
			articleSection.scrollIntoView({ behavior: 'smooth' });
		}
	}
</script>

<main class="relative flex min-h-screen flex-col bg-black text-white">
	<!-- Hero Section -->
	<div class="relative flex-auto space-y-12 px-6 py-16 sm:mx-[19vw] sm:px-0 md:py-20">
		<div
			class="flex max-w-full flex-col items-center gap-10 text-center md:max-w-[70%] md:items-start md:text-left"
		>
			<p class="text-left font-sans text-lg font-bold text-gray-300 uppercase md:text-xl">
				{$i18n.home.subtitle ||
					'Restez à jour avec la science médicale, sans vous noyer dans les 1 million d’articles publiés chaque année.'}
			</p>
			<p class="flex items-center justify-start gap-3 text-left text-base text-gray-200 md:text-lg">
				{$i18n.home.phrase1 || 'Médecin traitant débordé par les revues scientifiques ?'}
			</p>
			<div class="flex w-full flex-col gap-6">
				<p
					class="flex items-center justify-start gap-3 text-xl font-semibold text-white md:text-2xl"
				>
					<span class="text-2xl text-teal-400">⚡</span>
					{$i18n.home.phrase2 || 'Nous analysons et résumons la science pour vous.'}
				</p>
				<ul class="space-y-4">
					{#each $i18n.home.arguments?.list || ['Tri intelligent des articles de PubMed, Cochrane et plus.', 'Résumés générés par IA, simples et rapides à lire.', 'Suivi personnalisé des sujets qui vous intéressent.', 'Gain de temps pour intégrer la science dans votre pratique.'] as argument}
						<li
							class="flex items-start justify-start gap-3 text-base text-gray-300 md:justify-start md:text-lg"
						>
							<span class="text-xl text-teal-400">✔</span>
							{argument}
						</li>
					{/each}
				</ul>
			</div>
			<p
				class="flex items-center justify-center gap-3 text-base text-gray-200 md:justify-start md:text-lg"
			>
				<span class="text-2xl text-red-400">📩</span>
				{$i18n.home.arguments?.cta || 'Recevez l’essentiel chaque jour, en 5 minutes de lecture.'}
			</p>
			<div class="mt-8">
				<a
					href={$userProfileStore ? '/ma-veille' : '/signup'}
					on:click={handleVeilleClick}
					class="inline-block w-[60vw] bg-gradient-to-r from-blue-500 to-teal-500 px-8 py-3 text-center text-base font-semibold text-white shadow-lg transition-all duration-300 hover:from-blue-600 hover:to-teal-600 hover:shadow-xl md:w-auto md:px-12 md:py-4 md:text-lg"
				>
					{$userProfileStore
						? $i18n.home.hero?.viewArticles || 'Accéder à ma veille'
						: $i18n.home.hero?.signupForVeille || 'S’inscrire maintenant'}
				</a>
			</div>
		</div>
	</div>

	<!-- Partenaires -->
	<div class="relative flex flex-col gap-6 overflow-hidden px-6 py-8 sm:mx-[19vw] sm:px-0">
		<h2 class="mb-4 text-left text-2xl font-bold text-white">Nos partenaires de confiance</h2>
		<div class="flex flex-wrap items-center justify-start gap-8">
			<a
				href="https://pubmed.ncbi.nlm.nih.gov/"
				target="_blank"
				class="flex flex-col items-center gap-2"
			>
				<img
					src="https://cdn.ncbi.nlm.nih.gov/pubmed/277eb475-38df-4990-a0ee-0080b04e86fc/core/images/pubmed-logo-white.svg"
					alt="PubMed"
					class="h-10 w-auto"
				/>
			</a>
			<a href="https://www.embase.com" target="_blank" class="flex items-center gap-2">
				<EmbaseSvg />
				<span class="text-lg font-medium text-white">Embase</span>
			</a>
			<a href="https://www.cochranelibrary.com" target="_blank" class="flex items-center gap-2">
				<img
					src="https://www.cochrane.org/sites/default/files/public/cochrane-57-old.png"
					alt="Cochrane Library"
					class="h-10 w-auto"
				/>
				<span class="text-lg font-medium text-white">Cochrane Library</span>
			</a>
			<!-- <a href="" target="_blank">
				<img
					src="https://www.has-sante.fr/plugins/ModuleHAS2019/images/logo-has-mobile.png"
					alt=""
				/>
			</a> -->
		</div>
		<div class="mt-4">
			<p class="text-lg text-white sm:max-w-[50vw]">
				Nous sélectionnons pour vous les meilleurs articles médicaux provenant de ces plateformes
				reconnues, classés par grades de recommandation, et nous vous les présentons sous un format
				lisible et rapide.
			</p>
		</div>
	</div>

	<!-- Spécialités et Articles -->
	<div class="relative flex flex-col gap-4 overflow-hidden px-6 py-8 sm:mx-[19vw] sm:px-0">
		<div bind:this={articleSection} class="w-full py-12 text-white">
			<div class="flex flex-col gap-6">
				<h2 class="text-3xl font-bold">Découvrez certains de nos articles</h2>
				<h2 class="mb-4 text-left text-2xl font-bold text-white">1. Choisissez votre spécialité</h2>
				<div class="marquee-container relative overflow-hidden whitespace-nowrap">
					<div class="marquee-content animate-marquee inline-block">
						{#each specialties as specialty (specialty)}
							<button
								on:click={() => selectSpecialty(specialty)}
								class="mx-4 inline-block rounded-full bg-gray-800 px-6 py-3 text-lg font-medium text-white shadow-md transition-all hover:bg-gray-700 {selectedSpecialty ===
								specialty
									? 'bg-gray-600'
									: ''}"
							>
								{specialty}
							</button>
						{/each}
						{#each specialties as specialty (specialty)}
							<button
								on:click={() => selectSpecialty(specialty)}
								class="mx-4 inline-block rounded-full bg-gray-800 px-6 py-3 text-lg font-medium text-white shadow-md transition-all hover:bg-gray-700 {selectedSpecialty ===
								specialty
									? 'bg-gray-600'
									: ''}"
								aria-hidden="true"
							>
								{specialty}
							</button>
						{/each}
					</div>
					<div
						class="pointer-events-none absolute inset-0 bg-gradient-to-r from-black via-transparent to-black"
					></div>
				</div>
				<h2 class="mb-4 text-left text-2xl font-bold text-white">
					2. Explorez : {selectedSpecialty}
				</h2>
				<!-- <div
					class="mb-8 flex flex-col items-start space-y-4 sm:flex-row sm:items-center sm:space-y-0 sm:space-x-4"
				>
					<form class="relative ml-1 w-full sm:w-[30vw]">
						<input
							type="text"
							bind:value={searchQuery}
							placeholder="Rechercher un article..."
							class="w-full rounded-full border border-gray-700 bg-gray-800 px-6 py-4 pr-12 text-sm text-white transition-all duration-200 focus:border-gray-600 focus:ring focus:ring-gray-700"
						/>
						<svg
							class="absolute top-1/2 right-3 h-5 w-5 -translate-y-1/2 transform text-gray-400"
							fill="none"
							stroke="currentColor"
							viewBox="0 0 24 24"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
							/>
						</svg>
					</form>
				</div> -->

				{#if articles.length === 0}
					<p class="text-gray-400">Aucun article disponible pour {selectedSpecialty}.</p>
				{:else}
					<ul class="space-y-4">
						{#each articles as article}
							<li
								on:click={() => openImmersive(article)}
								class="relative cursor-pointer rounded bg-gray-800 p-4 shadow transition-shadow hover:shadow-xl"
							>
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
								<h3 class="mt-2 text-xs text-gray-400">
									Publié le {formatDate(article.published_at)}
								</h3>
							</li>
						{/each}
					</ul>
				{/if}

				{#if !userProfileStore}
					<!-- Call to Action avec flèche vers le bas -->
					<div class="mt-8 flex justify-center">
						<a
							href="/signup"
							class="flex flex-col items-center text-teal-400 transition-colors duration-200 hover:text-teal-300"
						>
							<span class="text-lg font-semibold">Voir plus</span>
							<svg
								class="mt-2 h-8 w-8 animate-bounce"
								fill="none"
								stroke="currentColor"
								viewBox="0 0 24 24"
								xmlns="http://www.w3.org/2000/svg"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M19 14l-7 7m0 0l-7-7m7 7V3"
								/>
							</svg>
						</a>
					</div>
				{/if}
			</div>
		</div>

		<div
			class="absolute right-0 bottom-0 left-0 h-2 bg-gradient-to-r from-blue-500 via-teal-500 to-transparent opacity-60"
		></div>
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
				<p class="mt-2 text-sm text-gray-400 mb-4">
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
				<!-- Bouton "Voir l'article ainsi que les recommandations IA" -->
				<!-- {#if !$userProfileStore}
					<div class="mt-6 flex justify-center">
						<button
							on:click={() => goto('/login')}
							class="rounded-full bg-gradient-to-r from-blue-500 to-teal-500 px-6 py-2 font-semibold
						text-white shadow-md transition-all duration-200 hover:from-blue-600
						hover:to-teal-600"
						>
							Voir l'article ainsi que les recommandations IA
						</button>
					</div>
				{/if} -->
			</div>
		</div>
	{/if}
</main>

<style>
	@keyframes marquee {
		0% {
			transform: translateX(0);
		}
		100% {
			transform: translateX(-50%);
		}
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

	/* Animation d'entrée pour le modal */
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

	/* Style général */
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
</style>
