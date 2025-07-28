<!-- /src/routes/ma-veille -->
<script lang="ts">
	// Correctly import 'page', not '$page'
	import ArticleListView from '$lib/components/articles/ArticleListView.svelte';
	import ArticleEditModal from '$lib/components/articles/ArticleEditModal.svelte';
	import { i18n } from '$lib/i18n';
	import userProfileStore from '$lib/stores/user';
	import { onMount } from 'svelte';
	import { supabase } from '$lib/supabase';
	import type { Article } from '$lib/utils/articleUtils';

	// --- Type for the structure from server ---
	interface SubDisciplineInfo { id: number; name: string; }
	interface DisciplineStructure {
		id: number;
		name: string;
		subscribed_sub_disciplines: SubDisciplineInfo[];
	}

	// Types for reading progress - updated to match actual RPC response
	interface DisciplineProgressItem {
		read_articles: number;
		total_articles: number;
		discipline_name: string;
		unread_articles: number;
		progress_percentage: number;
		sub_discipline_name: string;
	}
	
	interface ReadingProgressData {
		disciplines_progress: DisciplineProgressItem[];
	}
	
	// Computed values from the raw data
	interface ProcessedProgressData {
		progress_percentage: number;
		articles_read: number;
		articles_to_read: number;
		articles_by_discipline: Record<string, {
			total_articles: number;
			read_articles: number;
			progress_percentage: number;
			sub_disciplines: Array<{
				name: string;
				total_articles: number;
				read_articles: number;
				progress_percentage: number;
			}>;
		}>;
	}

	// Get data loaded by +page.server.ts
	const { data } = $props<{
		data: {
			isSubscribed: boolean;
			initialMainFilterValue: string | null; // Provided by server
			initialSubFilterValue: string | null;  // Provided by server
			userSubscriptionStructure: DisciplineStructure[];
			savedArticleIds: (string | number)[];
			articleData: any;
			error: string | null;
		}
	}>();
	console.log("data", data);
	console.log("data.isSubscribed", data.isSubscribed);

	const userStructure = data.userSubscriptionStructure || [];
	const hasSubscriptions = userStructure.length > 0;

	// Prepare filters for the *first* dropdown using the structure
	const filterOptions = $derived(
		userStructure.map((discipline: DisciplineStructure) => ({
			value: discipline.name,
			label: discipline.name
		}))
	);

	const savedIdsSet = $derived(new Set<string | number>(data.savedArticleIds || []));
	const currentUserId = $derived($userProfileStore?.id ?? null);
	const articleOfTheDayTitleTemplate = '🔥 Article du jour pour {filter} :';
	const previousArticlesTitleTemplate = '📖 Articles précédents pour {filter} :';

	// Pass the server-determined initial values directly
	const initialMainFilterFromData = data.initialMainFilterValue;
	const initialSubFilterFromData = data.initialSubFilterValue;

	// Reading progress state
	let progressLoading = $state(true);
	let progressError: string | null = $state(null);
	let progressData: ProcessedProgressData | null = $state(null);
	let showProgressModal = $state(false);

	// Edit modal state
	let showEditModal = $state(false);
	let editingArticle = $state<Article | null>(null);

	// Check if user is admin
	const isAdmin = $derived($userProfileStore?.is_admin ?? false);

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

	// Function to process raw RPC data into UI format
	function processProgressData(rawData: ReadingProgressData): ProcessedProgressData {
		const disciplinesMap = new Map<string, {
			total_articles: number;
			read_articles: number;
			sub_disciplines: Array<{
				name: string;
				total_articles: number;
				read_articles: number;
				progress_percentage: number;
			}>;
		}>();

		let totalRead = 0;
		let totalArticles = 0;

		// Process each discipline progress item
		rawData.disciplines_progress.forEach(item => {
			totalRead += item.read_articles;
			totalArticles += item.total_articles;

			if (!disciplinesMap.has(item.discipline_name)) {
				disciplinesMap.set(item.discipline_name, {
					total_articles: 0,
					read_articles: 0,
					sub_disciplines: []
				});
			}

			const discipline = disciplinesMap.get(item.discipline_name)!;
			discipline.total_articles += item.total_articles;
			discipline.read_articles += item.read_articles;

			// Add sub-discipline
			discipline.sub_disciplines.push({
				name: item.sub_discipline_name,
				total_articles: item.total_articles,
				read_articles: item.read_articles,
				progress_percentage: item.progress_percentage
			});
		});

		// Convert map to object and calculate percentages
		const articlesByDiscipline: Record<string, any> = {};
		disciplinesMap.forEach((data, disciplineName) => {
			articlesByDiscipline[disciplineName] = {
				...data,
				progress_percentage: data.total_articles > 0 
					? Math.round((data.read_articles / data.total_articles) * 100 * 100) / 100
					: 0
			};
		});

		return {
			progress_percentage: totalArticles > 0 
				? Math.round((totalRead / totalArticles) * 100 * 100) / 100
				: 0,
			articles_read: totalRead,
			articles_to_read: totalArticles,
			articles_by_discipline: articlesByDiscipline
		};
	}

	// Function to load progress data
	async function loadProgressData() {
		console.log('=== Starting loadProgressData ===');
		console.log('currentUserId:', currentUserId);
		console.log('hasSubscriptions:', hasSubscriptions);
		console.log('data.isSubscribed:', data.isSubscribed);
		
		if (!currentUserId) {
			console.error('No currentUserId - aborting RPC call');
			progressError = 'Utilisateur non identifié';
			progressLoading = false;
			return;
		}

		try {
			progressLoading = true;
			progressError = null;
			
			console.log('Making RPC call to calculate_user_reading_progress with user_id_param:', currentUserId);
			
			// Call the Supabase RPC directly
			const { data: rpcData, error } = await supabase.rpc('calculate_user_reading_progress', {
				user_id_param: currentUserId
			});
			
			console.log('RPC Response status:', error ? 'error' : 'success');
			console.log('RPC Error:', error);
			console.log('RPC Response data received:', JSON.stringify(rpcData, null, 2));
			
			if (error) {
				console.error('RPC Error details:', error);
				throw new Error(error.message || 'Erreur RPC');
			}

			console.log('RPC call successful, processing data...');
			
			// The RPC returns the progress data directly
			if (rpcData && rpcData.progress) {
				progressData = processProgressData(rpcData.progress);
				console.log('Set progressData from rpcData.progress:', progressData);
			} else {
				progressData = processProgressData(rpcData); // In case the RPC returns progress data directly
				console.log('Set progressData directly from rpcData:', progressData);
			}
		} catch (err: any) {
			console.error('Erreur lors du chargement des données de progression:', err);
			progressError = err.message || "Une erreur s'est produite";
		} finally {
			progressLoading = false;
			console.log('=== loadProgressData completed ===');
		}
	}

	// Format date function
	function formatDate(dateString: string): string {
		return new Date(dateString).toLocaleDateString('fr-FR', {
			day: 'numeric',
			month: 'short',
			year: 'numeric'
		});
	}

	// Load progress data on component mount
	onMount(() => {
		console.log('=== onMount called ===');
		console.log('hasSubscriptions:', hasSubscriptions);
		console.log('data.isSubscribed:', data.isSubscribed);
		console.log('currentUserId in onMount:', currentUserId);
		
		if (hasSubscriptions && data.isSubscribed) {
			console.log('Conditions met - calling loadProgressData from onMount');
			loadProgressData();
		} else {
			console.log('Conditions not met for loading progress data:', {
				hasSubscriptions,
				isSubscribed: data.isSubscribed
			});
		}
	});

	// Toggle progress modal
	function toggleProgressModal() {
		console.log('=== toggleProgressModal called ===');
		console.log('showProgressModal before:', showProgressModal);
		console.log('progressData:', progressData);
		console.log('progressLoading:', progressLoading);
		console.log('currentUserId:', currentUserId);
		
		showProgressModal = !showProgressModal;
		
		// If opening modal and no data yet, try to load it
		if (showProgressModal && !progressData && !progressLoading) {
			console.log('Modal opened but no data - calling loadProgressData');
			loadProgressData();
		}
		
		console.log('showProgressModal after:', showProgressModal);
	}
</script>

<!-- {#if !data.isSubscribed} -->
	<!-- <SubscriptionRequired /> -->
{#if !hasSubscriptions && !data.error}
	<!-- Empty State (No Subscriptions) -->
	<div class="flex min-h-[60vh] items-center justify-center text-center text-white p-6">
		<div class="empty-state">
			<p>Vous n'avez pas encore configuré les disciplines que vous souhaitez suivre.</p>
			<p>Veuillez <a href="/account">configurer vos disciplines</a> pour commencer à recevoir des articles pertinents.</p>
		</div>
	</div>
{:else if data.error}
	<!-- Error State -->
	<div class="flex min-h-[60vh] items-center justify-center text-center text-red-300 p-6">
		<p>Une erreur est survenue lors du chargement de vos données. Veuillez réessayer plus tard.</p>
	</div>
{:else}
	<!-- Vertical Progress Bar Widget (Right Side) -->
	{#if hasSubscriptions && data.isSubscribed}
		<div class="fixed right-4 md:right-6 sm:bottom-0 bottom-10 md:transform md:-translate-y-1/2 z-40">
			<button 
				onclick={toggleProgressModal}
				class="group relative bg-gray-900/80 backdrop-blur-sm border border-gray-600/50 rounded-full p-2 shadow-xl hover:shadow-2xl transition-all duration-500 hover:border-teal-400/60 hover:bg-gray-800/90"
				title="Cliquez pour voir votre progression de lecture"
			>
				<!-- Vertical Progress Bar Container -->
				<div class="relative w-3 h-16 md:h-24 bg-gray-700/60 rounded-full overflow-hidden">
					{#if progressLoading}
						<!-- Loading Animation -->
						<div class="absolute inset-0 bg-gradient-to-t from-teal-500/30 to-teal-400/30 rounded-full animate-pulse"></div>
						<div class="absolute bottom-0 w-full bg-gradient-to-t from-teal-500 to-teal-400 rounded-full transition-all duration-1000 ease-out animate-bounce" style="height: 20%"></div>
					{:else if progressError}
						<!-- Error State -->
						<div class="absolute inset-0 bg-gradient-to-t from-red-500/30 to-red-400/30 rounded-full"></div>
						<div class="absolute bottom-0 w-full bg-gradient-to-t from-red-500 to-red-400 rounded-full" style="height: 100%"></div>
					{:else if progressData}
						<!-- Progress Fill -->
						<div class="absolute inset-0 bg-gray-700/40 rounded-full"></div>
						<div 
							class="absolute bottom-0 w-full bg-gradient-to-t from-teal-500 via-teal-400 to-teal-300 rounded-full transition-all duration-1000 ease-out shadow-lg" 
							style="height: {Math.max(progressData.progress_percentage, 5)}%"
						></div>
						<!-- Glow effect -->
						<div 
							class="absolute bottom-0 w-full bg-gradient-to-t from-teal-400/50 via-teal-300/30 to-transparent rounded-full blur-sm transition-all duration-1000 ease-out" 
							style="height: {Math.max(progressData.progress_percentage + 10, 15)}%"
						></div>
					{:else}
						<!-- Default State -->
						<div class="absolute inset-0 bg-gray-700/40 rounded-full"></div>
						<div class="absolute bottom-0 w-full bg-gradient-to-t from-gray-500 to-gray-400 rounded-full" style="height: 10%"></div>
					{/if}
				</div>
				
				<!-- Percentage Label -->
				{#if progressData && !progressLoading && !progressError}
					<div class="absolute -left-12 md:-left-12 -top-8 md:top-1/2 md:transform md:-translate-y-1/2 bg-gray-800/90 backdrop-blur-sm border border-gray-600/50 rounded-lg px-2 py-1 opacity-0 group-hover:opacity-100 transition-all duration-300 pointer-events-none">
						<span class="text-xs font-bold text-teal-300 whitespace-nowrap">{progressData.progress_percentage}%</span>
						<div class="absolute right-0 top-1/2 transform translate-x-full -translate-y-1/2 w-0 h-0 border-l-4 border-l-gray-800/90 border-t-2 border-t-transparent border-b-2 border-b-transparent md:block hidden"></div>
						<!-- Mobile arrow (bottom) -->
						<div class="absolute left-1/2 bottom-0 transform -translate-x-1/2 translate-y-full w-0 h-0 border-t-4 border-t-gray-800/90 border-l-2 border-l-transparent border-r-2 border-r-transparent md:hidden block"></div>
					</div>
				{/if}

				<!-- Icon -->
				<div class="absolute -bottom-8 md:-bottom-8 left-1/2 transform -translate-x-1/2 text-teal-400 opacity-70 group-hover:opacity-100 transition-all duration-300">
					<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
					</svg>
				</div>
			</button>
		</div>
	{/if}

	<!-- ArticleListView with integrated email toggle -->
	<ArticleListView
		pageTitle="Ma veille"
		filters={filterOptions}
		initialFilterValue={initialMainFilterFromData}
		initialSubFilterValue={initialSubFilterFromData}
		filterSelectLabel="Spécialités"
		subDisciplineFetchMode="user"
		showSignupPromptProp={false}
		enableSearch={true}
		apiEndpoint="/api/get_articles_my_veille"
		apiFilterParamName="specialty"
		userId={currentUserId}
		itemsPerPage={15}
		loadMoreButtonText="Charger plus d'articles"
		allArticlesLoadedText="Tous les articles ont été chargés"
		isSubscribed={data.isSubscribed}
		showRecommendationsOnly={false}
		enableRecommendationsToggle={true}
		enableReadArticlesToggle={true}
		onEditClick={handleEditArticle}
	/>
{/if}

<!-- Modern Progress Modal -->
{#if showProgressModal}
	<div class="fixed inset-0 z-[9999] flex items-center justify-center p-4">
		<!-- Backdrop with blur -->
		<div 
			class="absolute inset-0 bg-black/60 backdrop-blur-md transition-opacity duration-300"
			onclick={toggleProgressModal}
		></div>
		
		<!-- Modal Content -->
		<div class="relative w-full max-w-4xl max-h-[90vh] md:max-h-[85vh] bg-gray-900/95 backdrop-blur-lg border border-gray-700/50 rounded-2xl shadow-2xl overflow-hidden animate-fade-in">
			<!-- Modern Header -->
			<div class="relative bg-gradient-to-r from-teal-500/10 via-teal-400/5 to-transparent border-b border-gray-700/50 px-4 md:px-6 py-4">
				<div class="flex items-center justify-between">
					<div class="flex items-center space-x-3">
						<div class="w-6 h-6 md:w-8 md:h-8 bg-gradient-to-r from-teal-500 to-teal-400 rounded-lg flex items-center justify-center">
							<svg class="w-4 h-4 md:w-5 md:h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
							</svg>
						</div>
						<h2 class="text-lg md:text-xl font-semibold text-white">
							Votre Progression de Veille
						</h2>
					</div>
				<button
					onclick={toggleProgressModal}
						class="text-gray-400 hover:text-white transition-colors p-2 rounded-lg hover:bg-gray-800/50"
				>
					<svg class="w-5 h-5 md:w-6 md:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
						<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
					</svg>
				</button>
				</div>
			</div>

			<!-- Modal Content -->
			<div class="p-4 md:p-6 overflow-y-auto max-h-[calc(90vh-80px)] md:max-h-[calc(85vh-80px)]">
				{#if progressLoading}
					<!-- Modern Loading State -->
					<div class="text-center py-12">
						<div class="relative w-16 h-16 mx-auto mb-6">
							<div class="absolute inset-0 bg-gradient-to-r from-teal-500 to-teal-400 rounded-full animate-spin opacity-20"></div>
							<div class="absolute inset-2 bg-gradient-to-r from-teal-500 to-teal-400 rounded-full animate-pulse"></div>
						</div>
						<p class="text-gray-300 text-lg">Chargement de votre progression...</p>
					</div>
				{:else if progressError}
					<!-- Modern Error State -->
					<div class="text-center py-12">
						<div class="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
							<svg class="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"/>
							</svg>
						</div>
						<h3 class="text-lg font-medium text-white mb-2">Une erreur est survenue</h3>
						<p class="text-gray-400 mb-6">{progressError}</p>
						<button 
							onclick={loadProgressData}
							class="bg-gradient-to-r from-teal-500 to-teal-400 hover:from-teal-600 hover:to-teal-500 text-white px-6 py-3 rounded-xl transition-all duration-300 font-medium shadow-lg hover:shadow-teal-500/25"
						>
							Réessayer
						</button>
					</div>
				{:else if progressData}
					<!-- Explanation Card -->
					<div class="bg-gradient-to-r from-teal-500/10 via-teal-400/5 to-transparent border border-teal-500/20 rounded-xl p-6 mb-8">
						<div class="flex items-start space-x-4">
							<div class="w-10 h-10 bg-gradient-to-r from-teal-500/20 to-teal-400/20 rounded-lg flex items-center justify-center flex-shrink-0">
								<span class="text-2xl">💡</span>
							</div>
							<div>
								<h3 class="text-lg font-medium text-teal-300 mb-2">Qu'est-ce que cela représente ?</h3>
								<p class="text-gray-300 leading-relaxed">
									Cette barre représente le pourcentage d'articles que vous avez lus parmi tous ceux disponibles dans vos spécialités ! 
									Plus vous lisez, plus votre veille est complète. 📖✨
								</p>
								<p class="text-gray-400 text-sm mt-2">
									Les statistiques sont calculées en fonction de vos abonnements aux disciplines et sous-spécialités.
								</p>
							</div>
						</div>
					</div>

					<!-- Detailed Statistics -->
					<div class="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6 mb-6">
						<h3 class="text-lg font-semibold text-white mb-6 flex items-center">
							<svg class="w-5 h-5 mr-2 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
							</svg>
							Statistiques Détaillées
						</h3>
						
						<div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
							<div class="bg-gray-700/30 border border-gray-600/30 rounded-lg p-4 text-center">
								<div class="text-2xl font-bold text-teal-400">{progressData.articles_read}</div>
								<div class="text-sm text-gray-400">Articles lus</div>
							</div>
							<div class="bg-gray-700/30 border border-gray-600/30 rounded-lg p-4 text-center">
								<div class="text-2xl font-bold text-orange-400">{progressData.articles_to_read - progressData.articles_read}</div>
								<div class="text-sm text-gray-400">Articles non lus</div>
							</div>
							<div class="bg-gray-700/30 border border-gray-600/30 rounded-lg p-4 text-center">
								<div class="text-2xl font-bold text-blue-400">{Object.keys(progressData.articles_by_discipline).length}</div>
								<div class="text-sm text-gray-400">Spécialités suivies</div>
							</div>
						</div>
						
						<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
							<div class="bg-gray-700/30 border border-gray-600/30 rounded-lg p-4">
								<h4 class="font-medium text-white mb-3">Meilleures performances</h4>
								{#if Object.values(progressData.articles_by_discipline).some(d => d.progress_percentage > 0)}
									{#each Object.entries(progressData.articles_by_discipline)
										.filter(([_, data]) => data.progress_percentage > 0)
										.sort(([_, a], [__, b]) => b.progress_percentage - a.progress_percentage)
										.slice(0, 3) as [name, data]}
										{#if name !== "Non spécifié"}
											<div class="flex justify-between items-center mb-2">
												<span class="text-gray-300 text-sm">{name}</span>
												<span class="text-teal-400 font-medium">{data.progress_percentage}%</span>
											</div>
										{/if}
									{/each}
								{:else}
									<p class="text-gray-500 text-sm">Aucune progression encore</p>
								{/if}
							</div>
							
							<div class="bg-gray-700/30 border border-gray-600/30 rounded-lg p-4">
								<h4 class="font-medium text-white mb-3">À améliorer</h4>
								{#each Object.entries(progressData.articles_by_discipline)
									.filter(([_, data]) => data.progress_percentage === 0 && data.total_articles > 0)
									.sort(([_, a], [__, b]) => b.total_articles - a.total_articles)
									.slice(0, 3) as [name, data]}
									{#if name !== "Non spécifié"}
										<div class="flex justify-between items-center mb-2">
											<span class="text-gray-300 text-sm">{name}</span>
											<span class="text-orange-400 font-medium">{data.total_articles} articles</span>
										</div>
									{/if}
								{/each}
							</div>
						</div>
					</div>

					<!-- Main Progress Overview -->
					<div class="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6 mb-6">
						<div class="flex items-center justify-between mb-6">
							<h3 class="text-lg font-semibold text-white">Progression Générale</h3>
							<div class="text-right">
								<div class="text-3xl font-bold text-transparent bg-gradient-to-r from-teal-400 to-teal-300 bg-clip-text">
									{progressData.progress_percentage}%
								</div>
								<div class="text-sm text-gray-400">de completion</div>
							</div>
						</div>
						
						<!-- Modern Progress Bar -->
						<div class="relative">
							<div class="w-full h-3 bg-gray-700/60 rounded-full overflow-hidden">
								<div 
									class="h-full bg-gradient-to-r from-teal-500 via-teal-400 to-teal-300 rounded-full transition-all duration-1000 ease-out shadow-lg relative"
									style="width: {progressData.progress_percentage}%"
								>
									<!-- Shine effect -->
									<div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse"></div>
								</div>
							</div>
							<div class="flex justify-between items-center mt-3">
								<div class="flex items-center space-x-2">
									<div class="w-2 h-2 bg-teal-400 rounded-full"></div>
									<span class="text-sm text-gray-400">{progressData.articles_read} articles lus</span>
								</div>
								<span class="text-sm text-gray-500">sur {progressData.articles_to_read}</span>
							</div>
						</div>
					</div>

					<!-- Progress by Discipline with modern cards -->
					<div class="bg-gray-800/50 border border-gray-700/50 rounded-xl p-6 mb-6">
						<h3 class="text-lg font-semibold text-white mb-6 flex items-center">
							<svg class="w-5 h-5 mr-2 text-teal-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
							</svg>
							Progression par Spécialité
						</h3>
						
						<div class="space-y-4">
							{#each Object.entries(progressData.articles_by_discipline) as [disciplineName, disciplineData]}
								{#if disciplineName !== "Non spécifié"}
									<div class="bg-gray-700/30 border border-gray-600/30 rounded-lg p-4 hover:bg-gray-700/50 transition-all duration-300">
										<!-- Discipline Header -->
										<div class="flex justify-between items-center mb-3">
											<h4 class="font-medium text-white text-lg">{disciplineName}</h4>
											<div class="text-right">
												<span class="text-lg font-bold text-teal-300">{disciplineData.progress_percentage}%</span>
												<div class="text-xs text-gray-400">{disciplineData.read_articles} / {disciplineData.total_articles} articles</div>
											</div>
										</div>
										
										<!-- Discipline Progress Bar -->
										<div class="w-full bg-gray-600/50 rounded-full h-3 mb-4">
											<div 
												class="bg-gradient-to-r from-teal-500 to-teal-400 h-3 rounded-full transition-all duration-1000 ease-out relative"
												style="width: {disciplineData.progress_percentage}%"
											>
												<!-- Shine effect -->
												<div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-pulse"></div>
											</div>
										</div>
										
										<!-- Sub-disciplines -->
										{#if disciplineData.sub_disciplines && disciplineData.sub_disciplines.length > 0}
											<div class="space-y-2">
												<h5 class="text-sm font-medium text-gray-300 mb-2">Sous-spécialités :</h5>
												<div class="grid grid-cols-1 md:grid-cols-2 gap-2">
													{#each disciplineData.sub_disciplines as subDiscipline}
														<div class="bg-gray-800/50 border border-gray-600/20 rounded p-2 text-xs">
															<div class="flex justify-between items-center mb-1">
																<span class="text-gray-300 truncate" title={subDiscipline.name}>
																	{subDiscipline.name}
																</span>
																<span class="text-teal-400 font-medium">
																	{subDiscipline.progress_percentage}%
																</span>
															</div>
															<div class="w-full bg-gray-700/50 rounded-full h-1">
																<div 
																	class="bg-gradient-to-r from-teal-500 to-teal-400 h-1 rounded-full transition-all duration-1000 ease-out"
																	style="width: {subDiscipline.progress_percentage}%"
																></div>
															</div>
															<div class="text-gray-500 text-xs mt-1">
																{subDiscipline.read_articles} / {subDiscipline.total_articles}
															</div>
														</div>
													{/each}
												</div>
											</div>
										{/if}
									</div>
								{/if}
							{/each}
						</div>
					</div>
				{:else}
					<!-- No Data State -->
					<div class="text-center py-12">
						<div class="w-16 h-16 bg-gray-600/30 rounded-full flex items-center justify-center mx-auto mb-4">
							<svg class="w-8 h-8 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
								<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
							</svg>
						</div>
						<p class="text-gray-400 text-lg">Aucune donnée de progression disponible</p>
					</div>
				{/if}
			</div>
		</div>
	</div>
{/if}

<!-- Edit Article Modal -->
<ArticleEditModal 
	showModal={showEditModal} 
	article={editingArticle} 
	onClose={closeEditModal} 
/>

<style>
	/* Page-specific styles */
	.empty-state {
		text-align: center;
		padding: 2rem;
		margin: 2rem auto;
		max-width: 600px;
		background-color: #374151; /* gray-700 to match other components */
		border-radius: 8px;
		color: #f3f4f6; /* gray-100 for text */
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
	}

	.empty-state p {
		margin: 1rem 0;
		font-size: 1.1rem;
		color: inherit;
	}

	.empty-state a {
		color: var(--color-primary, #0d9488); /* teal-600 */
		text-decoration: underline;
	}
</style>