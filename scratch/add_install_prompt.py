import re

with open('src/routes/+page.svelte', 'r', encoding='utf-8') as f:
    content = f.read()

# Add state for deferredPrompt and showInstall
state_injection = """  let deferredPrompt = $state<any>(null);
  let showInstallBanner = $state(false);
  
  onMount(async () => {"""

content = content.replace("  onMount(async () => {", state_injection)

# Add event listener for beforeinstallprompt inside onMount
onmount_injection = """  onMount(async () => {
    window.addEventListener('beforeinstallprompt', (e) => {
      // Prevent Chrome 67 and earlier from automatically showing the prompt
      e.preventDefault();
      // Stash the event so it can be triggered later.
      deferredPrompt = e;
      // Update UI to notify the user they can add to home screen
      showInstallBanner = true;
    });
"""
content = content.replace("  onMount(async () => {", onmount_injection)

# Add function to handle install click
functions_injection = """  async function processAndCropImage(fileOrBlob: File | Blob, targetWidth: number, targetHeight: number, quality = 0.7): Promise<File> {
"""
install_fn = """  async function installPwa() {
    if (!deferredPrompt) return;
    // Show the install prompt
    deferredPrompt.prompt();
    // Wait for the user to respond to the prompt
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === 'accepted') {
      console.log('User accepted the install prompt');
    }
    deferredPrompt = null;
    showInstallBanner = false;
  }

  async function processAndCropImage(fileOrBlob: File | Blob, targetWidth: number, targetHeight: number, quality = 0.7): Promise<File> {"""
content = content.replace(functions_injection, install_fn)


# Add the floating banner UI at the end of the page (before the last closing div if possible, or just at the very bottom)
# Let's add it right before the last closing </div> (which is the min-h-screen div)
banner_ui = """
  <!-- PWA Install Banner -->
  {#if showInstallBanner}
    <div class="fixed bottom-4 left-4 right-4 sm:left-auto sm:right-4 sm:w-80 bg-slate-900/95 backdrop-blur-md text-white p-4 rounded-2xl shadow-2xl z-[60] flex items-center justify-between animate-fade-in border border-slate-700">
      <div class="flex items-center">
        <img src="/icon-192.png" alt="Logo" class="w-10 h-10 rounded-lg mr-3" />
        <div>
          <h4 class="text-sm font-bold">Install Aplikasi</h4>
          <p class="text-[10px] text-slate-300">Tambahkan FORM MAZEEDA ke HP Anda</p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <button onclick={() => showInstallBanner = false} class="text-slate-400 hover:text-white p-1">
          <X class="w-4 h-4" />
        </button>
        <button onclick={installPwa} class="bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold py-1.5 px-3 rounded-lg transition-colors">
          Install
        </button>
      </div>
    </div>
  {/if}
</div>"""

# Replace the last `</div>` with the banner_ui. Since there are many `</div>`s, I'll use regex to replace the very last one.
content = re.sub(r'</div>\s*$', banner_ui, content)

# I also need to ensure 'X' icon is imported. Wait, X is not imported in +page.svelte!
# import { Upload, CheckCircle, Search, ChevronDown, Camera, FolderOpen, Shield } from 'lucide-svelte';
content = content.replace("FolderOpen, Shield", "FolderOpen, Shield, X")

with open('src/routes/+page.svelte', 'w', encoding='utf-8') as f:
    f.write(content)
