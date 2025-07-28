<!--- File Path: frontend/src/routes/+page.svelte --->
<script lang="ts">
	// --- IMPORTS ---
	import { goto } from '$app/navigation';
	import ArticleImmersiveModal from '$lib/components/articles/ArticleImmersiveModal.svelte';
	import ArticleEditModal from '$lib/components/articles/ArticleEditModal.svelte';
	import ArticleSearchById from '$lib/components/articles/ArticleSearchById.svelte';
	import * as Select from '$lib/components/ui/select/index.js';
	import userProfileStore from '$lib/stores/user';
	import EmbaseSvg from '../lib/svg/EmbaseSvg.svelte';
// Import modal
	import type { Article } from '$lib/utils/articleUtils'; // Import Article type
	// Import Lucide icons for features & pipeline
	import { Brain, Clock, FileText, Link, Mail, Users, Zap } from 'lucide-svelte'; // Added Brain, Users, Mail for pipeline

	// --- PROPS & STATE ---
	const { data } = $props();

	let articles = $state(data.articles || []);
	let specialties = $state(data.specialties || []);
	let selectedSpecialty = $state(data.specialties?.[0] || '');
	let immersiveArticle = $state<Article | null>(null);
	let isPlaying = $state(false);

	// Edit modal state
	let showEditModal = $state(false);
	let editingArticle = $state<Article | null>(null);

	// --- DERIVED & COMPUTED ---
	specialties = specialties.sort((a, b) => a.localeCompare(b, 'fr', { sensitivity: 'base' }));
	const triggerContent = $derived(
		specialties.find((s) => s === selectedSpecialty) ?? 'Choisissez une spécialité'
	);

	// Check if user is admin
	const isAdmin = $derived($userProfileStore?.is_admin ?? false);

	// --- UTILITY FUNCTIONS (unchanged) ---
	function handleVeilleClick(event: MouseEvent) {
		event.preventDefault();
		if (!$userProfileStore) { goto('/signup'); } else { goto('/ma-veille'); }
	}
	function formatTitle(title: string | undefined): string {
		if (!title) return '';
		const words = title.toLowerCase().split(' ');
		if (words.length === 0) return '';
		words[0] = words[0].charAt(0).toUpperCase() + words[0].slice(1);
		return words.join(' ');
	}
	interface ContentSection { emoji: string; title: string; content: string[]; }
	function parseContent(content: string | undefined): ContentSection[] {
		if (!content || typeof content !== 'string') return [];
		const sections: ContentSection[] = [];
		let currentSection: ContentSection = { emoji: '', title: '', content: [] };
		const lines = content.split('\n');
		let inSection = false;
		for (const line of lines) {
			if (line.trim().startsWith('## 📝') || line.trim().startsWith('## 📌') || line.trim().startsWith('## 🧪') || line.trim().startsWith('## 📊') || line.trim().startsWith('## 🩺') || line.trim().startsWith('## 📖')) {
				if (inSection && (currentSection.title || currentSection.content.length > 0)) { sections.push(currentSection); }
				inSection = true;
				const parts = line.trim().replace(/^##\s*/, '').split(' ');
				const emoji = parts[0] || '📝';
				const titleParts = parts.slice(1);
				currentSection = { emoji: emoji, title: titleParts.join(' ').trim(), content: [] };
			} else if (line.trim() && inSection) {
                if (line.trim() !== '---' && line.trim() !== '***' && line.trim() !== '___') { currentSection.content.push(line.trim()); }
			}
		}
		if (inSection && (currentSection.title || currentSection.content.length > 0)) { sections.push(currentSection); }
		return sections;
	}
	function extractTitleEmoji(content: string | undefined): string {
		if (!content || typeof content !== 'string') return '📝';
		const lines = content.split('\n');
		for (const line of lines) {
            if (line.trim().startsWith('# 📝') || line.trim().startsWith('# 📌') || line.trim().startsWith('# 🧪') || line.trim().startsWith('# 📊') || line.trim().startsWith('# 🩺') || line.trim().startsWith('# 📖')) {
				const parts = line.trim().split(' ');
                if(parts.length > 1) { return parts[1] || '📝'; }
			}
		}
		return '📝';
	}
	function formatDate(publishedAt: string | undefined): string {
		if (!publishedAt) return 'Non spécifiée';
		try {
			const date = new Date(publishedAt);
			if (isNaN(date.getTime())) { return 'Date invalide'; }
			return `${date.getDate().toString().padStart(2, '0')}/${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getFullYear()}`;
		} catch (e) { console.error('Error formatting date:', publishedAt, e); return 'Date invalide'; }
	}
	function openImmersive(article: Article) { immersiveArticle = article; document.body.classList.add('overflow-hidden'); }
	function closeImmersive() { immersiveArticle = null; document.body.classList.remove('overflow-hidden'); }
	function toggleAudio() {
		const audio = document.getElementById('myAudio') as HTMLAudioElement | null;
		if (!audio) return;
		if (isPlaying) { audio.pause(); } else { audio.play().catch(error => console.error("Audio playback error:", error)); }
		isPlaying = !isPlaying;
	}

	// Function to handle edit article
	function handleEditArticle(article: Article) {
		editingArticle = article;
		showEditModal = true;
	}

	// Function to close edit modal
	function closeEditModal() {
		showEditModal = false;
		editingArticle = null;
	}

	// --- EFFECTS (unchanged) ---
	$effect(() => {
		let filtered: Article[] = data.articles || [];
		// Keep filtering logic if needed for the bottom section
		if (selectedSpecialty) {
			filtered = filtered.filter((article) => article.disciplines?.includes(selectedSpecialty));
		}
		articles = filtered;
	});

</script>

<svelte:head>
	<title>Veille Médicale - Votre veille scientifique simplifiée</title>
	<meta name="description" content="Restez à jour avec les dernières études de votre spécialité. Résumés clairs, accès direct aux articles. Conçu par et pour les professionnels de santé." />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
	<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
	<link
		href="https://fonts.googleapis.com/css2?family=Montserrat:ital,wght@0,100..900;1,100..900&display=swap"
		rel="stylesheet"
	/>
</svelte:head>

<main class="min-h-screen bg-black text-white">
	<!-- Admin Search by ID Component -->
	<!-- <ArticleSearchById onArticleFound={handleEditArticle} /> -->

	<!-- ==================================================== -->
	<!-- HERO SECTION (Keep as is)                           -->
	<!-- ==================================================== -->
	<section class="relative pt-28 pb-24 md:pt-28 md:pb-24 overflow-hidden bg-gradient-to-b from-gray-950 via-black to-black">
        <div class="absolute inset-0 bg-center [mask-image:linear-gradient(180deg,white,rgba(255,255,255,0))] opacity-5"></div>
        <div class="container relative z-10 mx-auto max-w-5xl px-4 text-center">

            <!-- Main Headline -->
            <h1 class="text-4xl font-extrabold tracking-tight text-white sm:text-5xl md:text-6xl lg:text-7xl">
                La <span class="text-teal-400">veille scientifique</span>, simplifiée.
            </h1>

            <!-- Core Problem -->
			<p class="mt-8 text-xl font-medium text-gray-400 sm:text-lg md:text-xl">
				Trop d’<span class="font-semibold text-white">études</span> ? Pas assez de <span class="font-semibold text-white">temps</span> ?
			</p>

			<!-- Sub-headline -->
			<p class="mt-6 max-w-xl mx-auto text-lg leading-8 text-gray-300 sm:text-xl md:text-2xl">
				Recevez les résumés essentiels des dernières <span class="font-semibold text-teal-400"> études</span> et <span class="font-semibold text-teal-400">recommandations</span> de <span class="font-semibold text-teal-400">votre spécialité</span>.
			</p>


             <!-- Audio Button -->
            <div class="mt-10 mb-12 flex justify-center">
                <audio id="myAudio" preload="auto">
                    <source src="/audio/welcome.m4a" type="audio/mp4" />
                    Votre navigateur ne supporte pas l'élément audio.
                </audio>
                <button
                    onclick={toggleAudio}
                    class="play-button group relative flex items-center gap-2.5 rounded-full bg-gradient-to-r from-blue-600 to-teal-600 px-6 py-2.5 text-sm font-semibold text-white shadow-lg transition-all duration-300 hover:shadow-xl focus:outline-none focus:ring-2 focus:ring-teal-400 focus:ring-offset-2 focus:ring-offset-black"
                    aria-label={isPlaying ? 'Mettre en pause la présentation audio' : 'Écouter la présentation audio'}
                >
                    <span class="text-xl transition-transform duration-300 group-hover:scale-110">
                        {#if isPlaying}
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" /></svg>
                        {:else}
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clip-rule="evenodd" /></svg>
                        {/if}
                    </span>
                    <span class="whitespace-nowrap">{isPlaying ? 'Lecture en cours...' : 'Découvrez Veille en 1 min'}</span>
                </button>
            </div>

            <!-- Main CTA Button -->
            <div class="mt-10">
                <a
                    href={$userProfileStore ? '/ma-veille' : '/signup'}
                    onclick={handleVeilleClick}
                    class="group inline-flex items-center justify-center gap-2 rounded-full bg-orange-600 px-8 py-3 text-base font-semibold text-white shadow-lg transition-all duration-300 hover:bg-orange-700 hover:shadow-xl focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2 focus:ring-offset-black transform hover:scale-105"
                >
                    <span>{$userProfileStore ? 'Accéder à Ma Veille' : 'S’inscrire Gratuitement'}</span>
                    <svg class="h-5 w-5 transition-transform duration-300 group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"></path></svg>
                </a>
            </div>

            <!-- Pipeline Visualization Removed from Hero -->

        </div>
	</section>

    <!-- Feature Highlights Section -->
    <section class="py-16 sm:py-20 bg-gray-900">
        <div class="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
            <div class="grid grid-cols-1 gap-x-6 gap-y-10 sm:grid-cols-2 lg:grid-cols-4 lg:gap-x-8">
                <div class="flex flex-col items-center text-center group">
                    <div class="flex h-12 w-12 items-center justify-center rounded-lg bg-teal-500/10 border border-teal-500/30 mb-4 feature-icon">
                        <Zap class="h-6 w-6 text-teal-400" />
                    </div>
                    <h3 class="text-lg font-semibold text-white">Restez à jour</h3>
                    <p class="mt-1 text-sm text-gray-400">Recevez l'essentiel sur votre mail.</p>
                </div>
                <div class="flex flex-col items-center text-center group">
                     <div class="flex h-12 w-12 items-center justify-center rounded-lg bg-teal-500/10 border border-teal-500/30 mb-4 feature-icon">
                        <Clock class="h-6 w-6 text-teal-400" />
                    </div>
                    <h3 class="text-lg font-semibold text-white">Gagnez du temps</h3>
                    <p class="mt-1 text-sm text-gray-400">Synthèses claires, lecture rapide.</p>
                </div>
                <div class="flex flex-col items-center text-center group">
                    <div class="flex h-12 w-12 items-center justify-center rounded-lg bg-teal-500/10 border border-teal-500/30 mb-4 feature-icon">
                        <FileText class="h-6 w-6 text-teal-400" />
                    </div>
                    <h3 class="text-lg font-semibold text-white">L'essentiel</h3>
                    <p class="mt-1 text-sm text-gray-400">Articles et recommandations.</p>
                </div>
                 <div class="flex flex-col items-center text-center group">
                    <div class="flex h-12 w-12 items-center justify-center rounded-lg bg-teal-500/10 border border-teal-500/30 mb-4 feature-icon">
                        <Link class="h-6 w-6 text-teal-400" />
                    </div>
                    <h3 class="text-lg font-semibold text-white">Accès direct</h3>
                    <p class="mt-1 text-sm text-gray-400">Lien vers l'article original.</p>
                </div>
            </div>
        </div>
    </section>
	<!-- ======================== -->
	<!--   END NEW HERO SECTION   -->
	<!-- ======================== -->
	<div class="bg-gray-900 py-16 sm:py-20">
		<div class="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
			<h2 class="text-center text-3xl font-bold tracking-tight text-white mb-12 sm:mb-16">Veille Médicale en chiffres</h2>
			<dl class="grid grid-cols-1 gap-y-10 gap-x-6 text-center sm:grid-cols-3 lg:gap-x-8">
				<div class="flex flex-col items-center">
					<dt class="text-base leading-7 text-gray-400">Spécialités couvertes</dt>
					<dd class="order-first text-4xl font-semibold tracking-tight text-teal-400 sm:text-5xl">+35</dd>
					<p class="mt-1 text-s text-gray-500">(et +300 sous-spécialités)</p> <!-- Changed text-s to text-xs -->
				</div>
				<div class="flex flex-col items-center">
					<dt class="text-base leading-7 text-gray-400">Professionnels inscrits</dt>
					<dd class="order-first text-4xl font-semibold tracking-tight text-teal-400 sm:text-5xl">+1000</dd>
				</div>
				<div class="flex flex-col items-center">
					<dt class="text-base leading-7 text-gray-400">Recherches hebdomadaires</dt>
					<dd class="order-first text-4xl font-semibold tracking-tight text-teal-400 sm:text-5xl">+60 000</dd>
				</div>
			</dl>
		</div>
	</div>

    <!-- ======================== -->
	<!--    NOTRE PROCESSUS       -->
	<!-- ======================== -->
	<section class="py-16 sm:py-20 bg-gray-900">
        <div class="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 text-center">
            <h2 class="text-3xl font-bold tracking-tight text-white mb-12 sm:mb-16">
                Processus en 4 étapes
            </h2>
            <div class="flex flex-col md:flex-row md:items-start md:justify-between gap-y-8 md:gap-x-4 lg:gap-x-6">
                <!-- Step 1 -->
                <div class="flex-1 flex flex-col items-center text-center">
                    <div class="flex h-12 w-12 items-center justify-center rounded-full bg-teal-500/10 border border-teal-500/30 mb-4 shrink-0">
                        <FileText class="h-6 w-6 text-teal-400" />
                    </div>
                    <h3 class="text-lg font-semibold text-white mb-1">1. Sélection des Sources</h3>
                    <p class="text-sm text-gray-400">Notre algorithme sélectionne les meilleures études issues de PubMed et Cochrane.</p>
                </div>

                <!-- Arrow for mobile -->
                <div class="md:hidden flex justify-center items-center text-teal-400 my-2">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M16 17l-4 4m0 0l-4-4m4 4V3" />
                    </svg>
                </div>
                <!-- Arrow for desktop -->
                <div class="hidden md:flex justify-center items-center text-teal-400 shrink-0 pt-5">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 lg:h-10 lg:w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" />
                    </svg>
                </div>

                <!-- Step 2 -->
                <div class="flex-1 flex flex-col items-center text-center">
                    <div class="flex h-12 w-12 items-center justify-center rounded-full bg-teal-500/10 border border-teal-500/30 mb-4 shrink-0">
                        <Brain class="h-6 w-6 text-teal-400" />
                    </div>
                    <h3 class="text-lg font-semibold text-white mb-1">2. Analyse par IA</h3>
                    <p class="text-sm text-gray-400">Chaque article est synthétisé puis classé par spécialité médicale.</p>
                </div>

                <!-- Arrow for mobile -->
                <div class="md:hidden flex justify-center items-center text-teal-400 my-2">
                     <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M16 17l-4 4m0 0l-4-4m4 4V3" />
                    </svg>
                </div>
                <!-- Arrow for desktop -->
                <div class="hidden md:flex justify-center items-center text-teal-400 shrink-0 pt-5">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 lg:h-10 lg:w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" />
                    </svg>
                </div>

                <!-- Step 3 -->
                <div class="flex-1 flex flex-col items-center text-center">
                    <div class="flex h-12 w-12 items-center justify-center rounded-full bg-teal-500/10 border border-teal-500/30 mb-4 shrink-0">
                        <Users class="h-6 w-6 text-teal-400" />
                    </div>
                    <h3 class="text-lg font-semibold text-white mb-1">3. Validation Médicale</h3>
                    <p class="text-sm text-gray-400">Relecture par des experts, et proposition de nouvelles publications.</p>
                </div>

                <!-- Arrow for mobile -->
                <div class="md:hidden flex justify-center items-center text-teal-400 my-2">
                     <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M16 17l-4 4m0 0l-4-4m4 4V3" />
                    </svg>
                </div>
                <!-- Arrow for desktop -->
                <div class="hidden md:flex justify-center items-center text-teal-400 shrink-0 pt-5">
                     <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 lg:h-10 lg:w-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" />
                    </svg>
                </div>

                <!-- Step 4 -->
                <div class="flex-1 flex flex-col items-center text-center">
                    <div class="flex h-12 w-12 items-center justify-center rounded-full bg-teal-500/10 border border-teal-500/30 mb-4 shrink-0">
                        <Mail class="h-6 w-6 text-teal-400" />
                    </div>
                    <h3 class="text-lg font-semibold text-white mb-1">4. Votre Veille Prête</h3>
                    <p class="text-sm text-gray-400">Des synthèses claires et concises, directement dans votre boîte mail.</p>
                </div>
            </div>
        </div>
    </section>

	<!-- ==================================================== -->
	<!-- Spécialités et Articles SECTION (Keep as is) -->
	<!-- ==================================================== -->
	<div class="relative flex flex-col gap-4 overflow-hidden px-4 py-12 sm:mx-[10vw] sm:px-0 md:py-16">
		<div class="w-full text-white">
			<div class="flex flex-col gap-6">
				<h2 class="text-3xl font-bold">Découvrez certains de nos articles</h2>
				<div class="relative w-full max-w-sm">
					<Select.Root type="single" name="selectedSpecialty" bind:value={selectedSpecialty}>
						<Select.Trigger class="w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-3 text-sm font-medium text-white shadow-md transition-all duration-300 hover:bg-gray-700 focus:border-teal-500 focus:ring-2 focus:ring-teal-500 focus:outline-none">
							{triggerContent}
						</Select.Trigger>
						<Select.Content class="scrollbar-thin scrollbar-thumb-teal-500 scrollbar-track-gray-800 z-10 max-h-60 overflow-y-auto rounded-lg border border-gray-700 bg-gray-900 shadow-lg">
							<Select.Group>
								<Select.GroupHeading class="px-4 py-2 font-semibold text-gray-400">Spécialités</Select.GroupHeading>
								{#each specialties as specialty (specialty)}
									<Select.Item value={specialty} label={specialty} class="cursor-pointer px-4 py-2 text-white transition-all duration-200 hover:bg-teal-600/80 data-[highlighted]:bg-teal-600/80 data-[highlighted]:text-white data-[state=checked]:font-medium" />
								{/each}
							</Select.Group>
						</Select.Content>
					</Select.Root>
				</div>
				{#if articles.length === 0}
					<p class="mt-4 text-gray-400 italic">Aucun article disponible pour {selectedSpecialty || 'toutes les spécialités'}.</p>
				{:else}
					<ul class="space-y-4">
						{#each articles.slice(0,3) as article (article.id)}
							<li role="button" tabindex="0" onclick={() => openImmersive(article)} onkeydown={(e) => e.key === 'Enter' && openImmersive(article)} class="relative cursor-pointer rounded-lg bg-gray-800 p-4 shadow-md transition-all duration-200 hover:bg-gray-700 hover:shadow-xl focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 focus:ring-offset-black">
								<!-- Edit Button for Admins -->
								{#if isAdmin}
									<button
										type="button"
										aria-label="Modifier l'article"
										title="Modifier l'article"
										onclick={(e) => {
											e.stopPropagation();
											handleEditArticle(article);
										}}
										class="absolute top-2 right-2 focus:outline-none rounded-full p-1 transition-colors duration-150 hover:bg-gray-600 focus-visible:ring-2 focus-visible:ring-yellow-500 focus-visible:ring-offset-2 focus-visible:ring-offset-gray-800 z-10"
									>
										<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="w-4 h-4 text-yellow-400 hover:text-yellow-300 pointer-events-none">
											<path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
										</svg>
									</button>
								{/if}
								
								<h3 class="text-left text-lg font-bold text-white pr-5">
									<span class="mr-1.5">{extractTitleEmoji(article.content)}</span>
									{formatTitle(article.title)}
								</h3>
								{#if article.grade}
									<p class="mt-1 text-sm {article.grade == 'A' ? 'text-green-400' : article.grade == 'B' ? 'text-yellow-400' : article.grade == 'C' ? 'text-orange-400' : 'text-red-400'}">
                                        Grade de recommandation : <span class="font-medium">{article.grade}</span>
                                    </p>
								{/if}
								<div class="mt-2 flex items-center text-sm text-gray-400"><span class="mr-1">{article.journal || 'Journal inconnu'}</span></div>
								<p class="mt-1 text-xs text-gray-500">Publié le {formatDate(article.published_at)}</p>
							</li>
						{/each}
					</ul>
				{/if}
				{#if !$userProfileStore}
					<div class="mt-8 flex justify-center">
						<a href="/signup" class="flex flex-col items-center text-orange-500 transition-colors duration-200 hover:text-orange-400 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2 focus:ring-offset-black rounded-md p-1">
							<span class="text-lg font-semibold">Voir plus d'articles</span>
							<svg class="mt-2 h-6 w-6 animate-bounce" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3" /></svg>
						</a>
					</div>
				{/if}
			</div>
		</div>
	</div>
	<!-- ==================================================== -->
	<!-- END Spécialités/Articles                         -->
	<!-- ==================================================== -->


	<!-- ==================================================== -->
	<!-- Partenaires SECTION (Keep as is)                  -->
	<!-- ==================================================== -->
	<div class="relative flex flex-col gap-6 overflow-hidden px-4 py-8 sm:mx-[10vw] sm:px-0 md:py-12">
		<h2 class="mb-4 text-left text-2xl font-bold text-white">Nos partenaires</h2>
		<div class="flex flex-wrap items-center justify-center gap-8 md:justify-start">
			<a href="https://pubmed.ncbi.nlm.nih.gov/" target="_blank" rel="noopener noreferrer" class="flex flex-col items-center gap-2 opacity-80 transition-opacity hover:opacity-100"><img src="https://cdn.ncbi.nlm.nih.gov/pubmed/277eb475-38df-4990-a0ee-0080b04e86fc/core/images/pubmed-logo-white.svg" alt="PubMed" class="h-10 w-auto" loading="lazy" /></a>
			<a href="https://www.embase.com" target="_blank" rel="noopener noreferrer" class="flex items-center gap-2 opacity-80 transition-opacity hover:opacity-100"><EmbaseSvg /></a>
			<a href="https://www.cochranelibrary.com" target="_blank" rel="noopener noreferrer" class="flex items-center gap-2 opacity-80 transition-opacity hover:opacity-100"><img src="https://www.cochrane.org/sites/default/files/public/cochrane-57-old.png" alt="Cochrane Library" class="h-10 w-auto" loading="lazy" /></a>
		</div>
	</div>
	<!-- ==================================================== -->
	<!-- END Partenaires                                   -->
	<!-- ==================================================== -->


	<!-- ==================================================== -->
	<!-- STATS SECTION (Commented out - Keep as is)          -->
	<!-- ==================================================== -->
	<!-- <div class="bg-gray-900 py-16 sm:py-20">
		... content ...
	</div> -->
	<!-- ==================================================== -->
	<!-- END STATS SECTION                                  -->
	<!-- ==================================================== -->

</main>

<!-- Modal Immersif (Keep outside main) -->
{#if immersiveArticle}
	<ArticleImmersiveModal article={immersiveArticle} on:close={closeImmersive} />
{/if}

<!-- Modal d'édition d'articles -->
<ArticleEditModal 
	showModal={showEditModal} 
	article={editingArticle} 
	onClose={closeEditModal} 
/>

<style>
	/* Reuse styles from previous version */
	button:focus-visible, a:focus-visible {
		outline: 2px solid #2dd4bf; /* Teal 400 */
        outline-offset: 2px;
        border-radius: 4px;
	}
	.animate-bounce { animation: bounce 2s infinite; }
	@keyframes bounce { 0%, 20%, 50%, 80%, 100% { transform: translateY(0); } 40% { transform: translateY(-10px); } 60% { transform: translateY(-5px); } }
	.modal-enter-active { animation: fadeIn 0.3s ease-out; }
	@keyframes fadeIn { 0% { opacity: 0; transform: scale(0.95); } 100% { opacity: 1; transform: scale(1); } }
	.scrollbar-thin { scrollbar-width: thin; scrollbar-color: #14b8a6 #1f2937; }
	.scrollbar-thin::-webkit-scrollbar { width: 8px; }
	.scrollbar-thin::-webkit-scrollbar-track { background: #1f2937; border-radius: 4px;}
	.scrollbar-thin::-webkit-scrollbar-thumb { background-color: #14b8a6; border-radius: 4px; border: 2px solid #1f2937;}
	.scrollbar-thin::-webkit-scrollbar-thumb:hover { background-color: #0f766e;}
    .play-button:hover span:first-child { transform: scale(1.15); }

    /* Add subtle hover effect to feature icons */
    .group:hover .feature-icon {
        transform: translateY(-2px);
        /* Optional: Add a subtle glow or scale */
        /* box-shadow: 0 0 15px rgba(45, 212, 191, 0.3); */
        /* transform: scale(1.05) translateY(-2px); */
    }
    .feature-icon {
        transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
    }
</style>