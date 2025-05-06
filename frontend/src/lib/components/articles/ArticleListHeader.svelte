<!-- src/lib/components/articles/ArticleListHeader.svelte -->
<script lang="ts">
	import * as Select from '$lib/components/ui/select';
	import { createEventDispatcher } from 'svelte';

	interface FilterOption {
		value: string;
		label: string;
	}
	interface SubDisciplineOption {
		id: number; // Or string, ensure consistency
		name: string;
	}

	let {
		// Main Filter Props
		filters = [] as FilterOption[],
		selectedFilter = $bindable<string | null>(null),
		filterSelectLabel = 'Filtrer par',
		showAllCategoriesOption = true,
		ALL_CATEGORIES_VALUE = "__ALL__",
		ALL_CATEGORIES_LABEL = "Toutes les catégories",
		isContentLoading = false, // Disables filter when main content is initially loading

		// Sub-Discipline Filter Props
		showSubDisciplineFilter = false,
		availableSubDisciplines = [] as SubDisciplineOption[],
		selectedSubDiscipline = $bindable<string | null>(null),
		isLoadingSubDisciplines = false,
		subDisciplineSelectLabel = "Affiner par sous-spécialité",
		allSubDisciplinesLabel = "Toutes les sous-spécialités",
		showAllSubDisciplinesOption = true,

		// Search Props
		enableSearch = false,
		searchQuery = $bindable(''),
		searchPlaceholder = "Rechercher par mots-clés...",
        isSearchDisabled = false // To disable search specifically if needed (e.g. during initial load)
	} = $props<{
		// Main Filter Props
		filters?: FilterOption[];
		selectedFilter?: string | null;
		filterSelectLabel?: string;
		showAllCategoriesOption?: boolean;
		ALL_CATEGORIES_VALUE?: string;
		ALL_CATEGORIES_LABEL?: string;
		isContentLoading?: boolean;

		// Sub-Discipline Filter Props
		showSubDisciplineFilter?: boolean;
		availableSubDisciplines?: SubDisciplineOption[];
		selectedSubDiscipline?: string | null;
		isLoadingSubDisciplines?: boolean;
		subDisciplineSelectLabel?: string;
		allSubDisciplinesLabel?: string;
		showAllSubDisciplinesOption?: boolean;

		// Search Props
		enableSearch?: boolean;
		searchQuery?: string;
		searchPlaceholder?: string;
        isSearchDisabled?: boolean;
	}>();

	const sortedFilters = $derived(
        [...filters].sort((a: FilterOption, b: FilterOption) =>
			a.label.localeCompare(b.label, 'fr', { sensitivity: 'base' })
		)
    );

	const triggerContent = $derived(
        selectedFilter === ALL_CATEGORIES_VALUE
            ? ALL_CATEGORIES_LABEL
            : (filters.find((f: FilterOption) => f.value === selectedFilter)?.label ?? filterSelectLabel)
    );

    const subDisciplineTriggerContent = $derived(
        selectedSubDiscipline === null ? subDisciplineSelectLabel :
        selectedSubDiscipline === allSubDisciplinesLabel ? allSubDisciplinesLabel : selectedSubDiscipline
    );

    // Event dispatcher for sub-discipline change to allow parent to clear search query
    const dispatch = createEventDispatcher<{ subdisciplinechanged: string | null }>();

    function handleSubDisciplineChange(value: string | null) {
        const newValue = value === allSubDisciplinesLabel ? null : value;
        if (selectedSubDiscipline !== newValue) {
            selectedSubDiscipline = newValue; // Update bound value
            dispatch('subdisciplinechanged', newValue); // Notify parent
        }
    }

    function handleFilterChange(value: string | null) {
        if (selectedFilter !== value) {
            selectedFilter = value;
            // searchQuery = ''; // Parent will handle clearing search query
        }
    }
</script>

<div class="mb-6 flex flex-col gap-4">
    <div class="flex flex-col md:flex-row flex-wrap gap-4">
        {#if filters.length > 0 || showAllCategoriesOption}
            <div class="relative w-full md:max-w-xs shrink-0">
                <Select.Root type="single" name="selectedFilter" value={selectedFilter ?? undefined} onValueChange={(detail) => handleFilterChange(detail)}>
                    <Select.Trigger class="w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-3 text-sm font-medium text-white shadow-sm hover:bg-gray-700 focus:ring-2 focus:ring-teal-500 focus:outline-none" disabled={isContentLoading}>{triggerContent}</Select.Trigger>
                    <Select.Content class="scrollbar-thin scrollbar-thumb-teal-500 scrollbar-track-gray-800 z-20 max-h-60 overflow-y-auto rounded-lg border border-gray-700 bg-gray-900 shadow-lg">
                        <Select.Group>
                            <Select.GroupHeading class="px-4 py-2 font-semibold text-gray-400 text-xs uppercase tracking-wider">{filterSelectLabel}</Select.GroupHeading>
                            {#if showAllCategoriesOption}
                                <Select.Item value={ALL_CATEGORIES_VALUE} label={ALL_CATEGORIES_LABEL} class="cursor-pointer px-4 py-2 text-white hover:bg-teal-600/80 data-[selected]:bg-teal-700">{ALL_CATEGORIES_LABEL}</Select.Item>
                            {/if}
                            {#each sortedFilters as filter (filter.value)}
                                <Select.Item value={filter.value} label={filter.label} class="cursor-pointer px-4 py-2 text-white hover:bg-teal-600/80 data-[selected]:bg-teal-700">{filter.label}</Select.Item>
                            {/each}
                        </Select.Group>
                    </Select.Content>
                </Select.Root>
            </div>
        {/if}
        {#if showSubDisciplineFilter}
            <div class="relative w-full md:max-w-xs shrink-0">
                <Select.Root type="single" name="selectedSubDiscipline" value={selectedSubDiscipline ?? allSubDisciplinesLabel} onValueChange={(detail) => handleSubDisciplineChange(detail)}>
                    <Select.Trigger class="w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-3 text-sm font-medium text-white shadow-sm hover:bg-gray-700 focus:ring-2 focus:ring-teal-500 focus:outline-none" disabled={isLoadingSubDisciplines || isContentLoading}>
                        {#if isLoadingSubDisciplines}
                            <span class="flex items-center gap-2 opacity-70"><svg class="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"> <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle> <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path> </svg>Chargement...</span>
                        {:else}{subDisciplineTriggerContent}{/if}
                    </Select.Trigger>
                    <Select.Content class="scrollbar-thin scrollbar-thumb-teal-500 scrollbar-track-gray-800 z-10 max-h-60 overflow-y-auto rounded-lg border border-gray-700 bg-gray-900 shadow-lg">
                        <Select.Group>
                            <Select.GroupHeading class="px-4 py-2 font-semibold text-gray-400 text-xs uppercase tracking-wider">{subDisciplineSelectLabel}</Select.GroupHeading>
                            {#if showAllSubDisciplinesOption}
                                <Select.Item value={allSubDisciplinesLabel} label={allSubDisciplinesLabel} class="cursor-pointer px-4 py-2 text-white hover:bg-teal-600/80 data-[selected]:bg-teal-700">{allSubDisciplinesLabel}</Select.Item>
                            {/if}
                            {#each availableSubDisciplines as sub (sub.name)} <!-- Assuming sub.name is unique for keying -->
                                <Select.Item value={sub.name} label={sub.name} class="cursor-pointer px-4 py-2 text-white hover:bg-teal-600/80 data-[selected]:bg-teal-700">{sub.name}</Select.Item>
                            {/each}
                        </Select.Group>
                    </Select.Content>
                </Select.Root>
            </div>
        {/if}
    </div>
    {#if enableSearch}
        <div class="relative w-full">
            <input type="search" bind:value={searchQuery} placeholder={searchPlaceholder} class="w-full rounded-lg border border-gray-700 bg-gray-800 px-4 py-3 pl-10 text-sm font-medium text-white shadow-sm placeholder-gray-500 focus:ring-2 focus:ring-teal-500 focus:outline-none focus:border-teal-500" disabled={isSearchDisabled}/>
            <svg class="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-500 pointer-events-none" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" /></svg>
            {#if searchQuery}
                <button aria-label="Effacer la recherche" on:click={() => searchQuery = ''} class="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-white focus:outline-none focus:ring-1 focus:ring-teal-500 rounded-full p-0.5">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" /></svg>
                </button>
            {/if}
        </div>
    {/if}
</div>