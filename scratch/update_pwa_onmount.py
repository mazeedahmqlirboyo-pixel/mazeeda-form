import re

with open('src/routes/+page.svelte', 'r', encoding='utf-8') as f:
    content = f.read()

# Update onMount in +page.svelte
old_onmount = """  onMount(async () => {
    window.addEventListener('beforeinstallprompt', (e) => {
      // Prevent Chrome 67 and earlier from automatically showing the prompt
      e.preventDefault();
      // Stash the event so it can be triggered later.
      deferredPrompt = e;
      // Update UI to notify the user they can add to home screen
      showInstallBanner = true;
    });"""

new_onmount = """  onMount(async () => {
    // Cek apakah event sudah ditangkap oleh app.html lebih awal
    if (window.deferredPWAInstallPrompt) {
      deferredPrompt = window.deferredPWAInstallPrompt;
      showInstallBanner = true;
    }
    
    // Tetap pasang listener buat jaga-jaga kalau eventnya muncul belakangan
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      deferredPrompt = e;
      showInstallBanner = true;
    });"""

content = content.replace(old_onmount, new_onmount)

with open('src/routes/+page.svelte', 'w', encoding='utf-8') as f:
    f.write(content)
