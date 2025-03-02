<!-- /components/auth/MessageDisplay.svelte -->
<script>
    export let errorMessage = '';
    export let successMessage = '';
  </script>
  
  {#if errorMessage}
    <div class="rounded-lg bg-red-50 p-4 text-red-700 animate-fade-in">
      <span class="font-semibold">Erreur :</span> {errorMessage}
    </div>
  {/if}
  
  {#if successMessage}
    <div class="rounded-lg bg-green-50 p-4 text-green-700 animate-fade-in">
      <span class="font-semibold">Succès :</span> {successMessage}
    </div>
  {/if}
  
  <style>
    .animate-fade-in {
      animation: fadeIn 0.3s ease-out;
    }
  
    @keyframes fadeIn {
      from {
        opacity: 0;
        transform: translateY(-10px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
  </style>