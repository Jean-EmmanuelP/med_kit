<script lang="ts">
    import { onMount } from 'svelte';
    import { goto } from '$app/navigation';
    import { page } from '$app/stores';
    
    // Types
    interface User {
        id: string;
        first_name: string;
        last_name: string;
        email: string;
        is_admin: boolean;
        has_all_power: boolean;
    }
    
    interface Pagination {
        total: number;
        page: number;
        pageSize: number;
        totalPages: number;
    }
    
    let { data } = $props();
    
    // State using Svelte 5 runes
    let users = $state<User[]>([]);
    let loading = $state(true);
    let searchQuery = $state('');
    let pagination = $state<Pagination>({
        total: 0,
        page: 1,
        pageSize: 10,
        totalPages: 0
    });
    let currentUser = $state(data.user);
    let debounceTimer: NodeJS.Timeout;
    let updateMessage = $state('');
    let updateError = $state('');
    
    // Toast-like notifications
    function showMessage(message: string, isError = false) {
        if (isError) {
            updateError = message;
            updateMessage = '';
        } else {
            updateMessage = message;
            updateError = '';
        }
        
        setTimeout(() => {
            updateMessage = '';
            updateError = '';
        }, 3000);
    }
    
    // Fetch users with search and pagination
    async function fetchUsers() {
        loading = true;
        try {
            const queryParams = new URLSearchParams({
                q: searchQuery,
                page: pagination.page.toString(),
                pageSize: pagination.pageSize.toString()
            });
            
            const response = await fetch(`/api/admin/users?${queryParams}`);
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to fetch users');
            }
            
            const data = await response.json();
            users = data.users;
            pagination = data.pagination;
        } catch (error: any) {
            console.error('Error fetching users:', error);
            showMessage(`Erreur: ${error.message}`, true);
        } finally {
            loading = false;
        }
    }
    
    // Handle search input with debounce
    function handleSearch() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            pagination.page = 1; // Reset to first page on new search
            fetchUsers();
            
            // Update URL with search params
            const url = new URL(window.location.href);
            url.searchParams.set('q', searchQuery);
            url.searchParams.set('page', '1');
            history.replaceState(null, '', url);
        }, 300);
    }
    
    // Handle page change
    function changePage(newPage: number) {
        if (newPage < 1 || newPage > pagination.totalPages) return;
        pagination.page = newPage;
        fetchUsers();
        
        // Update URL with page param
        const url = new URL(window.location.href);
        url.searchParams.set('page', newPage.toString());
        history.replaceState(null, '', url);
    }
    
    // Update user admin rights
    async function updateUserRights(user: User, field: 'is_admin' | 'has_all_power') {
        try {
            const response = await fetch(`/api/admin/users/${user.id}/update-rights`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    is_admin: user.is_admin,
                    has_all_power: user.has_all_power
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to update user rights');
            }
            
            showMessage('Droits utilisateur mis à jour avec succès');
        } catch (error: any) {
            console.error('Error updating user rights:', error);
            showMessage(`Erreur: ${error.message}`, true);
            
            // Revert changes on error
            fetchUsers();
        }
    }
    
    // Initialize from URL params
    onMount(() => {
        const urlParams = new URLSearchParams(window.location.search);
        searchQuery = urlParams.get('q') || '';
        pagination.page = parseInt(urlParams.get('page') || '1');
        
        fetchUsers();
    });
</script>

<svelte:head>
    <title>Gestion des Utilisateurs | Super Admin</title>
</svelte:head>

<div class="min-h-screen bg-gray-50 py-8">
    <div class="container mx-auto px-4">
        <!-- Header -->
        <div class="mb-8">
            <h1 class="text-3xl font-bold text-gray-900 mb-2">Gestion des Utilisateurs</h1>
            <p class="text-gray-600">Gérez les utilisateurs et leurs permissions d'administration</p>
            <div class="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-md">
                <p class="text-sm text-blue-800">
                    <strong>Note :</strong> Seuls les super administrateurs (has_all_power) peuvent modifier les droits des utilisateurs.
                </p>
            </div>
        </div>
        
        <!-- Notifications -->
        {#if updateMessage}
            <div class="mb-6 p-4 bg-green-100 border border-green-400 text-green-700 rounded-md">
                {updateMessage}
            </div>
        {/if}
        
        {#if updateError}
            <div class="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded-md">
                {updateError}
            </div>
        {/if}
        
        <!-- Search Bar -->
        <div class="mb-6 bg-white rounded-lg shadow p-6">
            <div class="flex gap-4">
                <input
                    type="text"
                    bind:value={searchQuery}
                    oninput={handleSearch}
                    placeholder="Rechercher par nom ou email..."
                    class="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
            </div>
            <p class="text-sm text-gray-500 mt-2">
                {pagination.total} utilisateur{pagination.total > 1 ? 's' : ''} trouvé{pagination.total > 1 ? 's' : ''}
            </p>
        </div>
        
        <!-- Users Table -->
        <div class="bg-white shadow-md rounded-lg overflow-hidden">
            <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Utilisateur
                        </th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Email
                        </th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Administrateur
                        </th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Super Admin
                        </th>
                    </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                    {#if loading}
                        <tr>
                            <td colspan="4" class="px-6 py-8 text-center text-gray-500">
                                <div class="flex items-center justify-center">
                                    <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                                    <span class="ml-2">Chargement des utilisateurs...</span>
                                </div>
                            </td>
                        </tr>
                    {:else if users.length === 0}
                        <tr>
                            <td colspan="4" class="px-6 py-8 text-center text-gray-500">
                                Aucun utilisateur trouvé
                            </td>
                        </tr>
                    {:else}
                        {#each users as user (user.id)}
                            <tr class="hover:bg-gray-50 transition-colors">
                                <td class="px-6 py-4 whitespace-nowrap">
                                    <div class="flex items-center">
                                        <div class="flex-shrink-0 h-10 w-10">
                                            <div class="h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center">
                                                <span class="text-sm font-medium text-gray-700">
                                                    {(user.first_name?.charAt(0) || '') + (user.last_name?.charAt(0) || '')}
                                                </span>
                                            </div>
                                        </div>
                                        <div class="ml-4">
                                            <div class="text-sm font-medium text-gray-900">
                                                {user.first_name} {user.last_name}
                                            </div>
                                            {#if user.id === currentUser?.id}
                                                <div class="text-xs text-blue-600 font-medium">
                                                    Vous
                                                </div>
                                            {/if}
                                        </div>
                                    </div>
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap">
                                    <div class="text-sm text-gray-900">{user.email}</div>
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap">
                                    <label class="inline-flex items-center">
                                        <input 
                                            type="checkbox" 
                                            bind:checked={user.is_admin}
                                            onchange={() => updateUserRights(user, 'is_admin')}
                                            disabled={user.id === currentUser?.id}
                                            class="form-checkbox h-5 w-5 text-blue-600 rounded border-gray-300 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                                        />
                                        <span class="ml-2 text-sm text-gray-700">
                                            {#if user.is_admin}
                                                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                                    Admin
                                                </span>
                                            {:else}
                                                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                                                    Utilisateur
                                                </span>
                                            {/if}
                                        </span>
                                    </label>
                                    {#if user.id === currentUser?.id}
                                        <div class="text-xs text-gray-500 mt-1">
                                            Vous ne pouvez pas modifier vos propres permissions
                                        </div>
                                    {/if}
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap">
                                    <label class="inline-flex items-center">
                                        <input 
                                            type="checkbox" 
                                            bind:checked={user.has_all_power}
                                            onchange={() => updateUserRights(user, 'has_all_power')}
                                            disabled={user.id === currentUser?.id}
                                            class="form-checkbox h-5 w-5 text-red-600 rounded border-gray-300 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
                                        />
                                        <span class="ml-2 text-sm text-gray-700">
                                            {#if user.has_all_power}
                                                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                                    Super Admin
                                                </span>
                                            {:else}
                                                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                                                    Utilisateur
                                                </span>
                                            {/if}
                                        </span>
                                    </label>
                                    {#if user.id === currentUser?.id}
                                        <div class="text-xs text-gray-500 mt-1">
                                            Vous ne pouvez pas modifier vos propres permissions
                                        </div>
                                    {/if}
                                </td>
                            </tr>
                        {/each}
                    {/if}
                </tbody>
            </table>
        </div>
        
        <!-- Legend -->
        <div class="mt-4 bg-white rounded-lg shadow p-4">
            <h3 class="text-sm font-medium text-gray-900 mb-3">Légende des permissions :</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div class="flex items-center gap-2">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        Admin
                    </span>
                    <span class="text-gray-600">Peut accéder au dashboard et modifier les articles</span>
                </div>
                <div class="flex items-center gap-2">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                        Super Admin
                    </span>
                    <span class="text-gray-600">Peut gérer les utilisateurs et leurs permissions</span>
                </div>
            </div>
        </div>
        
        <!-- Pagination -->
        {#if pagination.totalPages > 1}
            <div class="flex justify-center mt-6">
                <nav class="inline-flex rounded-md shadow-sm -space-x-px">
                    <button 
                        onclick={() => changePage(pagination.page - 1)}
                        disabled={pagination.page === 1}
                        class="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <span class="sr-only">Précédent</span>
                        <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd" />
                        </svg>
                    </button>
                    
                    {#each Array(pagination.totalPages) as _, i}
                        {#if i + 1 === pagination.page || i + 1 === 1 || i + 1 === pagination.totalPages || (i + 1 >= pagination.page - 1 && i + 1 <= pagination.page + 1)}
                            <button 
                                onclick={() => changePage(i + 1)}
                                class={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                                    pagination.page === i + 1 
                                        ? 'bg-blue-50 border-blue-500 text-blue-600 z-10' 
                                        : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                                }`}
                            >
                                {i + 1}
                            </button>
                        {:else if i + 1 === pagination.page - 2 || i + 1 === pagination.page + 2}
                            <span class="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700">
                                ...
                            </span>
                        {/if}
                    {/each}
                    
                    <button 
                        onclick={() => changePage(pagination.page + 1)}
                        disabled={pagination.page === pagination.totalPages}
                        class="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <span class="sr-only">Suivant</span>
                        <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
                        </svg>
                    </button>
                </nav>
            </div>
        {/if}
        
        <!-- Back to Dashboard -->
        <div class="mt-8 text-center">
            <button 
                onclick={() => goto('/dashboard')}
                class="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
                </svg>
                Retour au Dashboard
            </button>
        </div>
    </div>
</div> 