<script lang="ts">
	import EmbaseSvg from '../lib/svg/EmbaseSvg.svelte';
	import { i18n } from '$lib/i18n';
	import userProfileStore from '$lib/stores/user';
	import { goto } from '$app/navigation';
	import * as Select from "$lib/components/ui/select/index.js";
  
	// Récupération des props avec $props rune
	const { data } = $props();
  
	// Définir les variables réactives avec $state
	let articles = $state(data.articles || []);
	let specialties = $state(data.specialties || []);
	let searchQuery = $state('');
	let selectedSpecialty = $state(data.specialties?.[0] || ''); // Fallback to empty string if undefined
	let articleSection = $state(null);
	let immersiveArticle = $state(null);
	let isPlaying = $state(false);
	let currentStep = $state(0); // Pour gérer l'affichage progressif des arguments
  
	// Sort specialties alphabetically on initialization
	specialties = specialties.sort((a, b) => a.localeCompare(b, 'fr', { sensitivity: 'base' }));
  
	// Compute the display label for the selected specialty
	const triggerContent = $derived(
	  specialties.find(s => s === selectedSpecialty) ?? "Choisissez une spécialité"
	);
  
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
  
	function toggleAudio() {
	  const audio = document.getElementById('myAudio');
	  if (isPlaying) {
		audio.pause();
	  } else {
		audio.play();
	  }
	  isPlaying = !isPlaying;
	}
  
	// Avancer automatiquement ou manuellement à l'étape suivante après 3 secondes
	$effect(() => {
	  if (isPlaying && currentStep < 3) {
		const timer = setTimeout(() => {
		  currentStep += 1;
		}, 3000); // 3 secondes par argument
		return () => clearTimeout(timer);
	  }
	});
  </script>
  
  <main class="relative flex min-h-screen flex-col bg-black text-white">
	<div class="relative flex-auto space-y-8 px-4 py-12 sm:mx-[10vw] sm:px-0 md:py-16">
	  <div class="flex max-w-full flex-col items-center gap-8 text-center md:max-w-[70%] md:items-start md:text-left">
		<!-- Title with Highlighted Keywords -->
		<h1 class="font-sans text-2xl leading-tight font-bold text-gray-100 sm:text-3xl">
		  <span class="font-bold text-teal-500">L’outil de veille scientifique</span> <br /> conçu
		  pour les <span class="font-bold text-teal-500">médecins</span>
		</h1>
  
		<!-- Core Message -->
		<div class="flex flex-col space-y-4 text-center md:text-left">
		  <p class="text-base leading-relaxed text-gray-300 sm:text-lg">
			Trop d’études scientifiques, pas assez de temps pour les lire ?
		  </p>
		  <p class="text-lg font-medium text-gray-100 sm:text-xl">
			Avec <span class="font-bold text-teal-500">Veille</span>, restez à la pointe de votre
			<span class="font-bold text-teal-500">spécialité</span>.
		  </p>
		  <p class="text-base leading-relaxed text-gray-300 sm:text-lg">
			Recevez un <span class="font-bold text-teal-500">résumé clair et concis</span> des
			meilleures études récentes dans votre domaine, à votre rythme, avec un
			<span class="font-bold text-teal-500">accès direct à l’article original</span>.
		  </p>
		</div>
  
		<!-- Audio Button (Subtle and Professional) -->
		<div class="mt-6 flex justify-center md:justify-start">
		  <audio id="myAudio" preload="auto">
			<source src="/audio/welcome.m4a" type="audio/mp4" />
			Votre navigateur ne supporte pas l'élément audio.
		  </audio>
		  <button
			on:click={toggleAudio}
			class="play-button group relative flex items-center gap-2 rounded-full bg-gradient-to-r from-teal-500 to-blue-600 px-5 py-2 font-medium text-white shadow-md transition-all duration-300 hover:from-teal-600 hover:to-blue-700 hover:shadow-lg"
		  >
			<span class="text-lg transition-transform duration-300 group-hover:scale-110">
			  {isPlaying ? '⏸' : '▶'}
			</span>
			<span>{isPlaying ? 'Pause' : 'Découvrez Veille en 1 min'}</span>
		  </button>
		</div>
  
		<!-- Arguments List -->
		<ul class="space-y-3 text-center md:text-left">
		  <li class="flex items-center justify-center gap-3 text-base text-gray-300 sm:text-lg md:justify-start">
			<span class="text-xl text-teal-400">✔</span>
			Choisissez vos disciplines
		  </li>
		  <li class="flex items-center justify-center gap-3 text-base text-gray-300 sm:text-lg md:justify-start">
			<span class="text-xl text-teal-400">✔</span>
			Paramétrez vos alertes
		  </li>
		  <li class="flex items-center justify-center gap-3 text-base text-gray-300 sm:text-lg md:justify-start">
			<span class="text-xl text-teal-400">✔</span>
			Résumés clairs et accès direct aux articles originaux
		  </li>
		</ul>
  
		<!-- CTA Text -->
		<p class="flex items-center justify-center gap-3 text-base text-gray-300 sm:text-lg md:justify-start">
		  <span class="text-2xl text-red-400">📩</span>
		  3 min/jour pour rester à la pointe de votre spécialité
		</p>
  
		<!-- CTA Button (Sticky on Mobile) -->
		<div class="sticky bottom-4 mt-6 flex w-full justify-center">
		  <a
			href={$userProfileStore ? '/ma-veille' : '/signup'}
			on:click={handleVeilleClick}
			class="inline-block w-[85%] rounded-full bg-gradient-to-r from-blue-500 to-teal-500 px-8 py-3 text-center text-base font-semibold text-white shadow-lg transition-all duration-300 hover:from-blue-600 hover:to-teal-600 hover:shadow-xl sm:w-[60%] md:w-auto md:px-12 md:py-4 md:text-lg"
		  >
			{$userProfileStore ? 'Accéder à ma veille' : 'S’inscrire maintenant'}
		  </a>
		</div>
	  </div>
	</div>
  
	<!-- Partenaires -->
	<div class="relative flex flex-col gap-6 overflow-hidden px-6 py-8 sm:mx-[10vw] sm:px-0">
	  <h2 class="mb-4 text-left text-2xl font-bold text-white">Nos partenaires</h2>
	  <div class="flex flex-wrap items-center justify-start gap-8">
		<a href="https://pubmed.ncbi.nlm.nih.gov/" target="_blank" class="flex flex-col items-center gap-2">
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
	  </div>
	</div>
  
	<!-- Spécialités et Articles -->
	<div class="relative flex flex-col gap-4 overflow-hidden px-6 py-8 sm:mx-[10vw] sm:px-0">
	  <div class="w-full py-12 text-white">
		<div class="flex flex-col gap-6">
		  <h2 class="text-3xl font-bold">Découvrez certains de nos articles</h2>
  
		  <!-- Specialty Selection -->
		  <h2 class="mb-4 text-left text-2xl font-bold text-white">1. Choisissez votre spécialité</h2>
		  <div class="relative w-full max-w-sm">
			<Select.Root type="single" name="selectedSpecialty" bind:value={selectedSpecialty}>
			  <Select.Trigger
				class="w-full rounded-lg border-gray-700 bg-gray-800 px-4 py-3 text-sm font-medium text-white shadow-md transition-all duration-300 hover:bg-gray-700 focus:ring-2 focus:ring-teal-500 focus:outline-none"
			  >
				{triggerContent}
			  </Select.Trigger>
			  <Select.Content
				class="scrollbar-thin scrollbar-thumb-teal-500 scrollbar-track-gray-800 max-h-60 overflow-y-auto rounded-lg border border-gray-700 bg-gray-900"
			  >
				<Select.Group>
				  <Select.GroupHeading class="px-4 py-2 text-gray-400 font-semibold">Spécialités</Select.GroupHeading>
				  {#each specialties as specialty (specialty)}
					<Select.Item
					  value={specialty}
					  label={specialty}
					  class="cursor-pointer px-4 py-2 text-white transition-all duration-200 hover:bg-teal-600 hover:text-white"
					/>
				  {/each}
				</Select.Group>
			  </Select.Content>
			</Select.Root>
		  </div>
  
		  <!-- Selected Specialty Display -->
		  <h2 bind:this={articleSection} class="mb-4 text-left text-2xl font-bold text-white">
			2. Explorez : {selectedSpecialty || 'Toutes'}
		  </h2>
  
		  <!-- Article List -->
		  {#if articles.length === 0}
			<p class="text-gray-400">
			  Aucun article disponible pour {selectedSpecialty || 'toutes les spécialités'}.
			</p>
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
  
		  {#if !$userProfileStore}
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
	  <div class="fixed inset-0 z-[200] flex items-center justify-center bg-black/30 backdrop-blur-sm">
		<div class="relative max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-2xl bg-gray-900 p-8 shadow-2xl">
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
		  {#if !$userProfileStore}
			<div class="mt-6 flex justify-center">
			  <button
				on:click={() => goto('/login')}
				class="rounded-full bg-gradient-to-r from-blue-500 to-teal-500 px-6 py-2 font-semibold text-white shadow-md transition-all duration-200 hover:from-blue-600 hover:to-teal-600"
			  >
				Voir l'article ainsi que les recommandations IA
			  </button>
			</div>
		  {/if}
		</div>
	  </div>
	{/if}
  </main>
  
  <style>
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
  
	/* Custom scrollbar for the select dropdown */
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