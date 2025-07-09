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
    
    interface PendingUpdate {
        user: User;
        field: 'is_admin' | 'has_all_power';
        newValue: boolean;
        oldValue: boolean;
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
    
    // Confirmation modal state
    let showConfirmation = $state(false);
    let pendingUpdate = $state<PendingUpdate | null>(null);
    
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
    
    // Handle checkbox change with confirmation
    function handleRightsChange(user: User, field: 'is_admin' | 'has_all_power', event: Event) {
        const target = event.target as HTMLInputElement;
        const newValue = target.checked;
        const oldValue = user[field];
        
        // If giving admin rights, show confirmation
        if (newValue && !oldValue) {
            target.checked = oldValue; // Revert the checkbox
            pendingUpdate = { user, field, newValue, oldValue };
            showConfirmation = true;
        } else {
            // If removing rights, apply directly without confirmation
            updateUserRights(user, field, newValue);
        }
    }
    
    // Confirm the pending update
    function confirmUpdate() {
        if (pendingUpdate) {
            updateUserRights(pendingUpdate.user, pendingUpdate.field, pendingUpdate.newValue);
            showConfirmation = false;
            pendingUpdate = null;
        }
    }
    
    // Cancel the pending update
    function cancelUpdate() {
        showConfirmation = false;
        pendingUpdate = null;
    }
    
    // Update user admin rights
    async function updateUserRights(user: User, field: 'is_admin' | 'has_all_power', newValue: boolean) {
        // Update the local state
        if (field === 'is_admin') {
            user.is_admin = newValue;
        } else {
            user.has_all_power = newValue;
        }
        
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

<div class="min-h-screen bg-black text-white">
    <div class="container mx-auto px-4 py-8">
        <!-- Header -->
        <div class="mb-8">
            <div class="flex items-center justify-between mb-4">
                <div>
                    <h1 class="text-3xl font-bold text-white mb-2">Gestion des Utilisateurs</h1>
                    <p class="text-gray-400">Gérez les utilisateurs et leurs permissions d'administration</p>
                </div>
                <button 
                    onclick={() => goto('/dashboard')}
                    class="inline-flex items-center px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-colors border border-gray-700"
                >
                    <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
                    </svg>
                    Retour au Dashboard
                </button>
            </div>
            <div class="p-4 bg-blue-900/30 border border-blue-700 rounded-lg">
                <p class="text-sm text-blue-300">
                    <strong>Note :</strong> Seuls les super administrateurs (has_all_power) peuvent modifier les droits des utilisateurs.
                </p>
            </div>
        </div>
        
        <!-- Notifications -->
        {#if updateMessage}
            <div class="mb-6 p-4 bg-green-900/30 border border-green-700 text-green-300 rounded-lg">
                {updateMessage}
            </div>
        {/if}
        
        {#if updateError}
            <div class="mb-6 p-4 bg-red-900/30 border border-red-700 text-red-300 rounded-lg">
                {updateError}
            </div>
        {/if}
        
        <!-- Search Bar -->
        <div class="mb-6 bg-gray-900 rounded-lg shadow-xl border border-gray-800 p-6">
            <div class="flex gap-4">
                <input
                    type="text"
                    bind:value={searchQuery}
                    oninput={handleSearch}
                    placeholder="Rechercher par nom ou email..."
                    class="flex-1 px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                />
            </div>
            <p class="text-sm text-gray-400 mt-2">
                {pagination.total} utilisateur{pagination.total > 1 ? 's' : ''} trouvé{pagination.total > 1 ? 's' : ''}
            </p>
        </div>
        
        <!-- Users Table -->
        <div class="bg-gray-900 shadow-xl rounded-lg overflow-hidden border border-gray-800">
            <table class="min-w-full divide-y divide-gray-800">
                <thead class="bg-gray-800">
                    <tr>
                        <th class="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                            Utilisateur
                        </th>
                        <th class="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                            Email
                        </th>
                        <th class="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                            Administrateur
                        </th>
                        <th class="px-6 py-4 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                            Super Admin
                        </th>
                    </tr>
                </thead>
                <tbody class="bg-gray-900 divide-y divide-gray-800">
                    {#if loading}
                        <tr>
                            <td colspan="4" class="px-6 py-12 text-center text-gray-400">
                                <div class="flex items-center justify-center">
                                    <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-teal-500"></div>
                                    <span class="ml-2">Chargement des utilisateurs...</span>
                                </div>
                            </td>
                        </tr>
                    {:else if users.length === 0}
                        <tr>
                            <td colspan="4" class="px-6 py-12 text-center text-gray-400">
                                Aucun utilisateur trouvé
                            </td>
                        </tr>
                    {:else}
                        {#each users as user (user.id)}
                            <tr class="hover:bg-gray-800 transition-colors">
                                <td class="px-6 py-4 whitespace-nowrap">
                                    <div class="flex items-center">
                                        <div class="flex-shrink-0 h-10 w-10">
                                            <div class="h-10 w-10 rounded-full bg-gray-700 flex items-center justify-center">
                                                <span class="text-sm font-medium text-gray-300">
                                                    {(user.first_name?.charAt(0) || '') + (user.last_name?.charAt(0) || '')}
                                                </span>
                                            </div>
                                        </div>
                                        <div class="ml-4">
                                            <div class="text-sm font-medium text-white">
                                                {user.first_name} {user.last_name}
                                            </div>
                                            {#if user.id === currentUser?.id}
                                                <div class="text-xs text-teal-400 font-medium">
                                                    Vous
                                                </div>
                                            {/if}
                                        </div>
                                    </div>
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap">
                                    <div class="text-sm text-gray-300">{user.email}</div>
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap">
                                    <label class="inline-flex items-center">
                                        <input 
                                            type="checkbox" 
                                            checked={user.is_admin}
                                            onchange={(e) => handleRightsChange(user, 'is_admin', e)}
                                            disabled={user.id === currentUser?.id}
                                            class="h-5 w-5 text-teal-600 bg-gray-700 border-gray-600 rounded focus:ring-teal-500 focus:ring-2 disabled:opacity-50 disabled:cursor-not-allowed"
                                        />
                                        <span class="ml-3 text-sm">
                                            {#if user.is_admin}
                                                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-900/50 text-green-300 border border-green-700">
                                                    Admin
                                                </span>
                                            {:else}
                                                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-700 text-gray-300 border border-gray-600">
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
                                            checked={user.has_all_power}
                                            onchange={(e) => handleRightsChange(user, 'has_all_power', e)}
                                            disabled={user.id === currentUser?.id}
                                            class="h-5 w-5 text-red-600 bg-gray-700 border-gray-600 rounded focus:ring-red-500 focus:ring-2 disabled:opacity-50 disabled:cursor-not-allowed"
                                        />
                                        <span class="ml-3 text-sm">
                                            {#if user.has_all_power}
                                                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-900/50 text-red-300 border border-red-700">
                                                    Super Admin
                                                </span>
                                            {:else}
                                                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-700 text-gray-300 border border-gray-600">
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
        <div class="mt-6 bg-gray-900 rounded-lg shadow-xl border border-gray-800 p-6">
            <h3 class="text-sm font-medium text-white mb-4">Légende des permissions :</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div class="flex items-center gap-3">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-900/50 text-green-300 border border-green-700">
                        Admin
                    </span>
                    <span class="text-gray-400">Peut accéder au dashboard et modifier les articles</span>
                </div>
                <div class="flex items-center gap-3">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-900/50 text-red-300 border border-red-700">
                        Super Admin
                    </span>
                    <span class="text-gray-400">Peut gérer les utilisateurs et leurs permissions</span>
                </div>
            </div>
        </div>
        
        <!-- Pagination -->
        {#if pagination.totalPages > 1}
            <div class="flex justify-center mt-8">
                <nav class="inline-flex rounded-md shadow-sm border border-gray-800 overflow-hidden">
                    <button 
                        onclick={() => changePage(pagination.page - 1)}
                        disabled={pagination.page === 1}
                        class="relative inline-flex items-center px-3 py-2 bg-gray-900 text-sm font-medium text-gray-400 hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed border-r border-gray-800"
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
                                class={`relative inline-flex items-center px-4 py-2 text-sm font-medium border-r border-gray-800 last:border-r-0 ${
                                    pagination.page === i + 1 
                                        ? 'bg-teal-900/50 text-teal-300 z-10' 
                                        : 'bg-gray-900 text-gray-400 hover:bg-gray-800'
                                }`}
                            >
                                {i + 1}
                            </button>
                        {:else if i + 1 === pagination.page - 2 || i + 1 === pagination.page + 2}
                            <span class="relative inline-flex items-center px-4 py-2 bg-gray-900 text-sm font-medium text-gray-500 border-r border-gray-800">
                                ...
                            </span>
                        {/if}
                    {/each}
                    
                    <button 
                        onclick={() => changePage(pagination.page + 1)}
                        disabled={pagination.page === pagination.totalPages}
                        class="relative inline-flex items-center px-3 py-2 bg-gray-900 text-sm font-medium text-gray-400 hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <span class="sr-only">Suivant</span>
                        <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
                        </svg>
                    </button>
                </nav>
            </div>
        {/if}
    </div>
</div>

<!-- Confirmation Modal -->
{#if showConfirmation && pendingUpdate}
    <div class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-75">
        <div class="w-full max-w-md bg-gray-900 rounded-lg shadow-xl border border-gray-800">
            <!-- Modal Header -->
            <div class="flex items-center justify-between bg-gray-800 px-6 py-4 rounded-t-lg border-b border-gray-700">
                <h2 class="text-lg font-semibold text-white">Confirmer les permissions</h2>
                <button
                    onclick={cancelUpdate}
                    class="text-gray-400 hover:text-white transition-colors"
                >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                </button>
            </div>

            <!-- Modal Content -->
            <div class="p-6">
                <div class="mb-6">
                    <div class="flex items-center justify-center w-12 h-12 mx-auto mb-4 bg-yellow-900/50 rounded-full border border-yellow-700">
                        <svg class="w-6 h-6 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"/>
                        </svg>
                    </div>
                    <h3 class="text-lg font-medium text-white text-center mb-2">Attention !</h3>
                    <p class="text-gray-400 text-center text-sm mb-4">
                        Vous êtes sur le point d'accorder des permissions 
                        {pendingUpdate.field === 'has_all_power' ? 'de Super Administrateur' : 'd\'Administrateur'} 
                        à cet utilisateur.
                    </p>
                    
                    <div class="bg-gray-800 rounded-lg p-4 border border-gray-700">
                        <div class="flex items-center gap-3">
                            <div class="h-10 w-10 rounded-full bg-gray-700 flex items-center justify-center">
                                <span class="text-sm font-medium text-gray-300">
                                    {(pendingUpdate.user.first_name?.charAt(0) || '') + (pendingUpdate.user.last_name?.charAt(0) || '')}
                                </span>
                            </div>
                            <div>
                                <p class="text-sm font-medium text-white">
                                    {pendingUpdate.user.first_name} {pendingUpdate.user.last_name}
                                </p>
                                <p class="text-xs text-gray-400">{pendingUpdate.user.email}</p>
                            </div>
                        </div>
                        <div class="mt-3 pt-3 border-t border-gray-700">
                            <p class="text-xs text-gray-400">
                                {#if pendingUpdate.field === 'has_all_power'}
                                    <strong class="text-red-400">Super Administrateur :</strong> Peut gérer tous les utilisateurs et leurs permissions
                                {:else}
                                    <strong class="text-green-400">Administrateur :</strong> Peut accéder au dashboard et modifier les articles
                                {/if}
                            </p>
                        </div>
                    </div>
                </div>

                <!-- Modal Actions -->
                <div class="flex items-center justify-end gap-3">
                    <button
                        onclick={cancelUpdate}
                        class="px-4 py-2 text-gray-400 hover:text-white transition-colors"
                    >
                        Annuler
                    </button>
                    <button
                        onclick={confirmUpdate}
                        class={`px-6 py-2 text-white rounded-lg transition-colors ${
                            pendingUpdate.field === 'has_all_power' 
                                ? 'bg-red-600 hover:bg-red-700' 
                                : 'bg-green-600 hover:bg-green-700'
                        }`}
                    >
                        Confirmer
                    </button>
                </div>
            </div>
        </div>
    </div>
{/if} 