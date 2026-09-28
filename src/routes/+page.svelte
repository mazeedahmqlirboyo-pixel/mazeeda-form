<script lang="ts">
  import { onMount, tick } from 'svelte';
  import { supabase } from '$lib/supabaseClient';
  import { getWhatsAppProvider, getProviderColor, type Provider } from '$lib/utils/whatsapp';
  import { Upload, CheckCircle, Search, ChevronDown, Camera, FolderOpen, Shield, X, FileImage } from 'lucide-svelte';

  let siswiList = $state<any[]>([]);
  let filteredSiswi = $state<any[]>([]);
  let searchQuery = $state('');
  let showDropdown = $state(false);
  let showBloodTypeDropdown = $state(false);
  
  let selectedSiswi = $state<any>(null);

  // Form State
  let formData = $state({
    id: '',
    nis: '',
    full_name: '',
    blood_type: '',
    residence: '',
    travel_route: '',
    whatsapp_number: '',
    whatsapp_provider: 'Unknown' as Provider,
    email: '',
    instagram: '',
    tiktok: '',
    twitter_x: '',
    hobbies: '',
    special_skills: '',
    aspirations: '',
    favorite_food: '',
    favorite_drink: '',
    favorite_color: '',
    favorite_music: '',
    quote: '',
    impression: '',
    message: '',
    avatar_url: '',
    paper_form_url: '',
    paper_form_url_2: '',
    is_completed: false
  });

  let isUploading = $state(false);
    let isUploadingDoc = $state(false);

  // State untuk Webcam
  let showCameraModal = $state(false);
  let videoElement = $state<HTMLVideoElement | null>(null);
  let canvasElement = $state<HTMLCanvasElement | null>(null);
  let stream = $state<MediaStream | null>(null);


  // Fungsi untuk Resize & Crop (Kompresi ke bawah 1MB)
  async function installPwa() {
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

  async function processAndCropImage(fileOrBlob: File | Blob, targetWidth: number, targetHeight: number, quality = 0.7): Promise<File> {    return new Promise((resolve, reject) => {
      const img = new Image();
      const url = URL.createObjectURL(fileOrBlob);
      
      img.onload = () => {
        URL.revokeObjectURL(url);
        
        const canvas = document.createElement('canvas');
        canvas.width = targetWidth;
        canvas.height = targetHeight;
        const ctx = canvas.getContext('2d');
        if (!ctx) return reject('No canvas context');

        // Hitung crop ke tengah (center crop)
        const imgRatio = img.width / img.height;
        const targetRatio = targetWidth / targetHeight;
        
        let drawWidth = img.width;
        let drawHeight = img.height;
        let offsetX = 0;
        let offsetY = 0;

        if (imgRatio > targetRatio) {
          drawWidth = img.height * targetRatio;
          offsetX = (img.width - drawWidth) / 2;
        } else {
          drawHeight = img.width / targetRatio;
          offsetY = (img.height - drawHeight) / 2;
        }

        ctx.drawImage(img, offsetX, offsetY, drawWidth, drawHeight, 0, 0, targetWidth, targetHeight);
        
        canvas.toBlob((blob) => {
          if (!blob) return reject('Blob failed');
          let fileName = fileOrBlob instanceof File ? fileOrBlob.name.replace(/\.[^/.]+$/, "") + '.jpg' : 'image.jpg';
          resolve(new File([blob], fileName, { type: 'image/jpeg' }));
        }, 'image/jpeg', quality);
      };
      
      img.onerror = reject;
      img.src = url;
    });
  }

  async function openCameraModal() {
    if (!selectedSiswi) {
      errorMsg = 'Silakan pilih Nama / NIS Anda terlebih dahulu di bagian atas.';
      return;
    }
    
    showCameraModal = true;
    await tick(); // Tunggu HTML video dirender

    try {
      // Coba kamera belakang dulu (untuk HP)
      stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
      if (videoElement) {
        videoElement.srcObject = stream;
        videoElement.play();
      }
    } catch (err) {
      // Jika tidak ada kamera belakang (misal di Laptop), gunakan kamera depan/webcam bawaan
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        if (videoElement) {
          videoElement.srcObject = stream;
          videoElement.play();
        }
      } catch (fallbackErr) {
        alert('Tidak dapat mengakses kamera. Pastikan Anda telah memberikan izin kamera pada browser.');
        closeCameraModal();
      }
    }
  }

  function closeCameraModal() {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      stream = null;
    }
    showCameraModal = false;
  }

  async function capturePhoto() {
    if (!videoElement || !canvasElement || !selectedSiswi) return;
    
    // Ambil full resolusi dari video asli dulu
    canvasElement.width = videoElement.videoWidth;
    canvasElement.height = videoElement.videoHeight;
    const ctx = canvasElement.getContext('2d');
    if (!ctx) return;
    ctx.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);
    
    canvasElement.toBlob(async (blob) => {
      if (!blob) return;
      
      // Crop & compress hasil webcam menjadi portrait 900x1200
      const compressedFile = await processAndCropImage(blob, 900, 1200, 0.7);
      const file = new File([compressedFile], `webcam-${selectedSiswi.id}-${Math.random()}.jpg`, { type: 'image/jpeg' });
      
      closeCameraModal();
      
      isUploadingDoc = true;
      errorMsg = '';
      
      const { error: uploadError } = await supabase.storage
        .from('avatars')
        .upload(file.name, file);

      if (uploadError) {
        errorMsg = 'Gagal upload foto kamera: ' + uploadError.message;
        isUploadingDoc = false;
        return;
      }

      const { data } = supabase.storage.from('avatars').getPublicUrl(file.name);
      formData.paper_form_url = data.publicUrl;
      isUploadingDoc = false;
      
    }, 'image/jpeg', 0.8);
  }

  let isSaving = $state(false);
  let saveSuccess = $state(false);
  let errorMsg = $state('');

  const webhookUrl = 'https://script.google.com/macros/s/AKfycb.../exec'; // Ganti dengan Webhook URL asli

  let deferredPrompt = $state<any>(null);
  let showInstallBanner = $state(false);
  
  onMount(async () => {
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
    });

    await fetchSiswiList();
  });

  async function fetchSiswiList() {
    const { data, error } = await supabase
      .from('siswi')
      .select('id, nis, full_name, is_completed')
      .order('full_name');
    
    if (error) {
      console.error('Error fetching data:', error);
    } else {
      siswiList = data || [];
      filteredSiswi = siswiList;
    }
  }

  function handleSearchInput() {
    showDropdown = true;
    filteredSiswi = siswiList.filter(s => 
      s.full_name.toLowerCase().includes(searchQuery.toLowerCase()) || 
      (s.nis && s.nis.includes(searchQuery))
    );
  }

  async function selectSiswi(siswi: any) {
    searchQuery = `${siswi.nis ? siswi.nis + ' - ' : ''}${siswi.full_name}`;
    showDropdown = false;
    selectedSiswi = siswi;
    
    // Fetch full data
    const { data, error } = await supabase
      .from('siswi')
      .select('*')
      .eq('id', siswi.id)
      .single();
      
    if (data) {
      formData = { ...formData, ...data, whatsapp_provider: data.whatsapp_provider || 'Unknown' };
    }
  }

  function handleWhatsAppChange(e: Event) {
    const target = e.target as HTMLInputElement;
    formData.whatsapp_number = target.value;
    formData.whatsapp_provider = getWhatsAppProvider(target.value);
  }

  async function handleFileUpload(e: Event) {
    const target = e.target as HTMLInputElement;
    const file = target.files?.[0];
    if (!file || !selectedSiswi) return;

    isUploading = true;
    errorMsg = '';
    const fileExt = file.name.split('.').pop();
    const fileName = `${selectedSiswi.id}-${Math.random()}.${fileExt}`;
    const filePath = `${fileName}`;

    // Compress and crop to square 800x800 (under 500kb)
    const compressedFile = await processAndCropImage(file, 800, 800, 0.7);

    const { error: uploadError } = await supabase.storage
      .from('avatars')
      .upload(filePath, compressedFile);

    if (uploadError) {
      errorMsg = 'Gagal upload foto: ' + uploadError.message;
      isUploading = false;
      return;
    }

    const { data } = supabase.storage.from('avatars').getPublicUrl(filePath);
    formData.avatar_url = data.publicUrl;
    isUploading = false;
  }

  
  async function handleDocumentUpload(e: Event) {
    const target = e.target as HTMLInputElement;
    const file = target.files?.[0];
    if (!file || !selectedSiswi) return;

    isUploadingDoc = true;
    errorMsg = '';
    const fileExt = file.name.split('.').pop();
    const fileName = `form-${selectedSiswi.id}-${Math.random()}.${fileExt}`;

    // Compress and crop to portrait 900x1200
    const compressedFile = await processAndCropImage(file, 900, 1200, 0.7);

    const { error: uploadError } = await supabase.storage
      .from('avatars')
      .upload(fileName, compressedFile);

    if (uploadError) {
      errorMsg = 'Gagal upload dokumen: ' + uploadError.message;
      isUploadingDoc = false;
      return;
    }

    const { data } = supabase.storage.from('avatars').getPublicUrl(fileName);
    formData.paper_form_url = data.publicUrl;
    isUploadingDoc = false;
  }

  async function handleSubmit(e: Event) {
    e.preventDefault();
    if (!selectedSiswi) {
      errorMsg = 'Silakan pilih nama Anda terlebih dahulu.';
      return;
    }

    isSaving = true;
    errorMsg = '';
    saveSuccess = false;
    
    formData.is_completed = true;

    const { error } = await supabase
      .from('siswi')
      .update(formData)
      .eq('id', selectedSiswi.id);

    if (error) {
      errorMsg = 'Gagal menyimpan data: ' + error.message;
      isSaving = false;
      return;
    }

    // Optional: Kirim ke Google Sheets Webhook
    try {
      await fetch(webhookUrl, {
        method: 'POST',
        mode: 'no-cors',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });
    } catch (e) {
      console.warn('Google Sheets webhook error (diabaikan)', e);
    }

    saveSuccess = true;
    isSaving = false;
    
    // Refresh list to update is_completed status in search dropdown
    await fetchSiswiList();
  }

  // Action untuk auto-resize textarea
  function autoResizeAction(node: HTMLTextAreaElement, value: string) {
    function resize() {
      node.style.height = 'auto';
      node.style.height = node.scrollHeight + 'px';
    }
    
    node.addEventListener('input', resize);
    setTimeout(resize, 0);

    return {
      update(newValue: string) {
        setTimeout(resize, 0);
      },
      destroy() {
        node.removeEventListener('input', resize);
      }
    };
  }

</script>

<div class="min-h-screen bg-slate-50 py-4 sm:py-12 relative px-4 sm:px-6 lg:px-8">
  <div class="max-w-3xl mx-auto bg-white/95 backdrop-blur-3xl rounded-3xl shadow-2xl ring-1 ring-black/5">
    
    <div class="rounded-t-2xl overflow-hidden relative">
      <img src="/banner.jpg" alt="Banner Buku Kenangan" class="w-full h-48 sm:h-64 object-cover" />
      
      <!-- Tombol Menuju Admin -->
      <a href="/admin" title="Dashboard Admin Verval" class="absolute top-4 right-4 p-2.5 bg-white/10 hover:bg-white/30 backdrop-blur-md rounded-full text-white transition-all shadow-sm group border border-white/10">
        <Shield class="w-5 h-5 opacity-70 group-hover:opacity-100 transform group-hover:scale-110 transition-all" />
      </a>
    </div>

    <div class="p-8">
      <!-- Search Combobox -->
      <div class="mb-8 relative">
        <label for="search" class="block text-sm font-semibold text-gray-700 mb-2">Pilih Nama / NIS Anda</label>
        <div class="relative">
          <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search class="h-5 w-5 text-gray-400" />
          </div>
          <input
            id="search"
            type="text"
            class="block w-full pl-10 pr-4 py-4 border border-gray-200 bg-gray-50/50 focus:bg-white rounded-2xl focus:ring-2 focus:ring-indigo-500 sm:text-sm transition-all shadow-sm"
            placeholder="Ketik nama atau NIS..."
            bind:value={searchQuery}
            oninput={handleSearchInput}
            onfocus={() => showDropdown = true}
            onblur={() => setTimeout(() => showDropdown = false, 200)}
          />
        </div>
        
        {#if showDropdown && searchQuery.length > 0}
          <ul class="absolute z-50 mt-2 w-full bg-white border border-gray-200 shadow-2xl max-h-64 rounded-xl overflow-y-auto focus:outline-none sm:text-sm divide-y divide-gray-50">
            {#each filteredSiswi as siswi}
              <!-- svelte-ignore a11y_click_events_have_key_events -->
              <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
              <li 
                class="text-gray-800 cursor-pointer select-none relative py-3 px-4 hover:bg-indigo-50 transition-colors"
                onclick={() => selectSiswi(siswi)}
              >
                <div class="flex items-center justify-between">
                  <span class="font-medium block truncate">
                    {siswi.nis ? `${siswi.nis} - ` : ''}{siswi.full_name}
                  </span>
                  {#if siswi.is_completed}
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 shadow-sm border border-green-200">
                      Sudah Mengisi
                    </span>
                  {/if}
                </div>
              </li>
            {/each}
            {#if filteredSiswi.length === 0}
              <li class="text-gray-500 cursor-default select-none relative py-3 px-4">
                Tidak ditemukan.
              </li>
            {/if}
          </ul>
        {/if}
      </div>

      {#if saveSuccess}
        <div class="mt-12 mb-12 text-center animate-fade-in">
          <div class="mx-auto flex items-center justify-center h-28 w-28 rounded-full bg-green-100 mb-6 shadow-inner">
            <CheckCircle class="h-14 w-14 text-green-600" />
          </div>
          <h2 class="text-3xl font-extrabold text-gray-900 mb-4">Terima Kasih!</h2>
          <p class="text-lg text-gray-600 mb-10 max-w-xl mx-auto">Biodata untuk <strong class="text-slate-800">{selectedSiswi?.full_name}</strong> telah berhasil disimpan dengan aman ke dalam database MAZEEDA.</p>
          <button type="button" onclick={() => { saveSuccess = false; selectedSiswi = null; searchQuery = ''; showDropdown = false; window.scrollTo({top: 0, behavior: 'smooth'}); }} class="inline-flex items-center justify-center px-8 py-4 border border-transparent shadow-lg text-lg font-bold rounded-2xl text-white bg-slate-700 hover:bg-slate-800 transform transition hover:-translate-y-1">
            📝 Kembali / Isi Data Siswi Lainnya
          </button>
        </div>
      {:else if selectedSiswi}
        <form onsubmit={handleSubmit} class="space-y-6 animate-fade-in">
          
          {#if formData.is_completed}
            <div class="bg-green-50 border border-green-200 rounded-lg p-4 mb-6 flex items-start">
              <CheckCircle class="h-5 w-5 text-green-600 mt-0.5 mr-3 flex-shrink-0" />
              <div>
                <h3 class="text-sm font-medium text-green-800">Anda sudah mengisi form ini sebelumnya!</h3>
                <p class="mt-1 text-sm text-green-700">Data lama Anda telah dimuat otomatis. Anda dapat memperbaruinya di bawah ini.</p>
              </div>
            </div>
          {/if}

          <div class="grid grid-cols-1 gap-y-8 gap-x-6 sm:grid-cols-2">
            <!-- SECTION 1 -->
            <div class="sm:col-span-2 pt-4 pb-2 border-b border-gray-100"><h4 class="text-lg font-bold text-indigo-900">1. Data Pribadi</h4></div>
            <!-- NIS -->
            <div>
              <label for="nis" class="block text-sm font-semibold text-gray-700">NIS</label>
              <input type="text" id="nis" bind:value={formData.nis} disabled class="mt-1 block w-full bg-gray-100/80 border border-gray-200 rounded-xl py-3 px-4 shadow-inner text-gray-600 font-medium sm:text-sm cursor-not-allowed" />
            </div>

            <!-- Full Name -->
            <div>
              <label for="full_name" class="block text-sm font-semibold text-gray-700">Nama Lengkap</label>
              <input type="text" id="full_name" bind:value={formData.full_name} disabled class="mt-1 block w-full bg-gray-100/80 border border-gray-200 rounded-xl py-3 px-4 shadow-inner text-gray-600 font-medium sm:text-sm cursor-not-allowed" />
            </div>

            <!-- Blood Type -->
            <div class="relative">
              <span class="block text-sm font-semibold text-gray-700 mb-1">Golongan Darah</span>
              <button 
                type="button"
                class="w-full bg-white border border-gray-200 bg-gray-50/50 hover:bg-white rounded-xl py-3 px-4 shadow-sm text-left cursor-pointer focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm flex items-center justify-between transition-all"
                onclick={() => showBloodTypeDropdown = !showBloodTypeDropdown}
                onblur={() => setTimeout(() => showBloodTypeDropdown = false, 200)}
              >
                <span class={formData.blood_type ? "text-gray-900" : "text-gray-500"}>
                  {formData.blood_type || 'Pilih Golongan Darah...'}
                </span>
                <ChevronDown class="h-4 w-4 text-gray-400" />
              </button>

              {#if showBloodTypeDropdown}
                <ul class="absolute z-50 mt-2 w-full bg-white border border-gray-200 shadow-2xl rounded-xl overflow-hidden focus:outline-none sm:text-sm divide-y divide-gray-50">
                  <!-- svelte-ignore a11y_click_events_have_key_events -->
                  <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
                  <li class="text-gray-500 cursor-pointer select-none relative py-2.5 px-4 hover:bg-gray-50 transition-colors" onclick={() => { formData.blood_type = ''; showBloodTypeDropdown = false; }}>
                    Kosongkan
                  </li>
                  {#each ['A', 'B', 'AB', 'O'] as type}
                    <!-- svelte-ignore a11y_click_events_have_key_events -->
                    <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
                    <li 
                      class="text-gray-800 font-medium cursor-pointer select-none relative py-2.5 px-4 hover:bg-indigo-50 transition-colors"
                      onclick={() => { formData.blood_type = type; showBloodTypeDropdown = false; }}
                    >
                      {type}
                    </li>
                  {/each}
                </ul>
              {/if}
            </div>

            <!-- Residence -->
            <div>
              <label for="residence" class="block text-sm font-semibold text-gray-700">Tempat Tinggal / Alamat</label>
              <input type="text" id="residence" bind:value={formData.residence} class="mt-1 block w-full border border-gray-200 bg-gray-50/50 focus:bg-white rounded-xl py-3 px-4 transition-all focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
            </div>

            <!-- Travel Route -->
            <div class="sm:col-span-2">
              <label for="travel_route" class="block text-sm font-semibold text-gray-700">Rute Perjalanan</label>
              <textarea id="travel_route" use:autoResizeAction={formData.travel_route} bind:value={formData.travel_route} placeholder="Misal: Angkot 02 -> Ojek" class="mt-1 block w-full border border-gray-200 bg-gray-50/50 focus:bg-white rounded-xl py-3 px-4 transition-all focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm overflow-hidden min-h-[80px]"></textarea>
            </div>

            <!-- SECTION 2 -->
            <div class="sm:col-span-2 pt-6 pb-2 border-b border-gray-100"><h4 class="text-lg font-bold text-indigo-900">2. Kontak & Sosial Media</h4></div>
            <!-- WhatsApp -->
            <div>
              <label for="whatsapp" class="block text-sm font-semibold text-gray-700">Nomor WhatsApp</label>
              <div class="mt-1 relative rounded-md shadow-sm">
                <input type="tel" id="whatsapp" value={formData.whatsapp_number} oninput={handleWhatsAppChange} placeholder="08xx..." class="block w-full border border-gray-300 rounded-md py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
              </div>
              {#if formData.whatsapp_number && formData.whatsapp_provider !== 'Unknown'}
                <div class="mt-2">
                  <span class={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getProviderColor(formData.whatsapp_provider)}`}>
                    {formData.whatsapp_provider}
                  </span>
                </div>
              {/if}
            </div>

            <!-- Email -->
            <div>
              <label for="email" class="block text-sm font-semibold text-gray-700">Email</label>
              <input type="email" id="email" bind:value={formData.email} class="mt-1 block w-full border border-gray-200 bg-gray-50/50 focus:bg-white rounded-xl py-3 px-4 transition-all focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
            </div>

            <!-- Social Media -->
            <div>
              <label for="instagram" class="block text-sm font-semibold text-gray-700">Instagram (@username)</label>
              <input type="text" id="instagram" bind:value={formData.instagram} class="mt-1 block w-full border border-gray-200 bg-gray-50/50 focus:bg-white rounded-xl py-3 px-4 transition-all focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
            </div>
            <div>
              <label for="tiktok" class="block text-sm font-semibold text-gray-700">TikTok (@username)</label>
              <input type="text" id="tiktok" bind:value={formData.tiktok} class="mt-1 block w-full border border-gray-200 bg-gray-50/50 focus:bg-white rounded-xl py-3 px-4 transition-all focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
            </div>
            <div>
              <label for="twitter_x" class="block text-sm font-semibold text-gray-700">Twitter / X (@username)</label>
              <input type="text" id="twitter_x" bind:value={formData.twitter_x} class="mt-1 block w-full border border-gray-200 bg-gray-50/50 focus:bg-white rounded-xl py-3 px-4 transition-all focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
            </div>

            <!-- SECTION 3 -->
            <div class="sm:col-span-2 pt-6 pb-2 border-b border-gray-100"><h4 class="text-lg font-bold text-indigo-900">3. Minat & Favorit</h4></div>
            <!-- Hobbies & Skills -->
            <div class="sm:col-span-2">
              <label for="hobbies" class="block text-sm font-semibold text-gray-700">Hobi</label>
              <textarea id="hobbies" use:autoResizeAction={formData.hobbies} bind:value={formData.hobbies} class="mt-1 block w-full border border-gray-200 bg-gray-50/50 focus:bg-white rounded-xl py-3 px-4 transition-all focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm overflow-hidden min-h-[60px]"></textarea>
            </div>
            <div class="sm:col-span-2">
              <label for="special_skills" class="block text-sm font-semibold text-gray-700">Keahlian Khusus</label>
              <textarea id="special_skills" use:autoResizeAction={formData.special_skills} bind:value={formData.special_skills} class="mt-1 block w-full border border-gray-200 bg-gray-50/50 focus:bg-white rounded-xl py-3 px-4 transition-all focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm overflow-hidden min-h-[60px]"></textarea>
            </div>

            <!-- Aspirations -->
            <div class="sm:col-span-2">
              <label for="aspirations" class="block text-sm font-semibold text-gray-700">Cita-cita</label>
              <input type="text" id="aspirations" bind:value={formData.aspirations} class="mt-1 block w-full border border-gray-200 bg-gray-50/50 focus:bg-white rounded-xl py-3 px-4 transition-all focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
            </div>

            <!-- Favorites -->
            <div>
              <label for="favorite_food" class="block text-sm font-semibold text-gray-700">Makanan Favorit</label>
              <input type="text" id="favorite_food" bind:value={formData.favorite_food} class="mt-1 block w-full border border-gray-200 bg-gray-50/50 focus:bg-white rounded-xl py-3 px-4 transition-all focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
            </div>
            <div>
              <label for="favorite_drink" class="block text-sm font-semibold text-gray-700">Minuman Favorit</label>
              <input type="text" id="favorite_drink" bind:value={formData.favorite_drink} class="mt-1 block w-full border border-gray-200 bg-gray-50/50 focus:bg-white rounded-xl py-3 px-4 transition-all focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
            </div>
            <div>
              <label for="favorite_music" class="block text-sm font-semibold text-gray-700">Musik / Lagu Favorit</label>
              <input type="text" id="favorite_music" bind:value={formData.favorite_music} class="mt-1 block w-full border border-gray-200 bg-gray-50/50 focus:bg-white rounded-xl py-3 px-4 transition-all focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
            </div>

            <div class="sm:col-span-2">
              <label for="favorite_color" class="block text-sm font-semibold text-gray-700">Warna Favorit</label>
              <input type="text" id="favorite_color" bind:value={formData.favorite_color} class="mt-1 block w-full border border-gray-200 bg-gray-50/50 focus:bg-white rounded-xl py-3 px-4 transition-all focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
            </div>
            <!-- SECTION 4 -->
            <div class="sm:col-span-2 pt-6 pb-2 border-b border-gray-100"><h4 class="text-lg font-bold text-indigo-900">4. Kesan & Pesan</h4></div>
            <!-- Quote & Messages -->
            <div class="sm:col-span-2">
              <label for="quote" class="block text-sm font-semibold text-gray-700">Quotes / Motto Hidup</label>
              <textarea id="quote" use:autoResizeAction={formData.quote} bind:value={formData.quote} class="mt-1 block w-full border border-gray-200 bg-gray-50/50 focus:bg-white rounded-xl py-3 px-4 transition-all focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm overflow-hidden min-h-[60px]"></textarea>
            </div>
            <div class="sm:col-span-2">
              <label for="impression" class="block text-sm font-semibold text-gray-700">Kesan Selama Sekolah</label>
              <textarea id="impression" use:autoResizeAction={formData.impression} bind:value={formData.impression} class="mt-1 block w-full border border-gray-200 bg-gray-50/50 focus:bg-white rounded-xl py-3 px-4 transition-all focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm overflow-hidden min-h-[80px]"></textarea>
            </div>
            <div class="sm:col-span-2">
              <label for="message" class="block text-sm font-semibold text-gray-700">Pesan</label>
              <textarea id="message" use:autoResizeAction={formData.message} bind:value={formData.message} class="mt-1 block w-full border border-gray-200 bg-gray-50/50 focus:bg-white rounded-xl py-3 px-4 transition-all focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm overflow-hidden min-h-[80px]"></textarea>
            </div>
          </div>

          
                    <!-- SECTION 5 -->
          <div class="sm:col-span-2 pt-6 pb-2 border-b border-gray-100"><h4 class="text-lg font-bold text-indigo-900">5. Arsip Formulir Kertas</h4></div>
          
          <div class="sm:col-span-2 mb-6">
            <p class="text-sm text-gray-600 mb-4">Khusus Tim Panitia: Silakan unggah foto formulir kertas fisik siswi sebagai arsip cadangan digital.</p>
            <div class="flex items-center space-x-6 p-6 bg-gradient-to-r from-gray-50 to-slate-50 border border-gray-200 rounded-3xl shadow-sm">
              <!-- Kiri: Foto Preview -->
              <div class="shrink-0 relative">
                {#if formData.paper_form_url}
                  <a href={formData.paper_form_url} target="_blank" class="block h-40 w-32 bg-gray-200 rounded-2xl overflow-hidden border-4 border-white shadow-lg hover:opacity-90 transition-opacity">
                    <img src={formData.paper_form_url} class="w-full h-full object-cover" alt="Arsip Formulir" />
                  </a>
                {:else}
                  <div class="h-40 w-32 bg-white rounded-2xl flex flex-col items-center justify-center border-4 border-gray-100 shadow-sm border-dashed">
                    <span class="text-gray-400 text-xs font-medium text-center px-2">Belum ada arsip</span>
                  </div>
                {/if}
              </div>
              
              <!-- Kanan: Tombol Icon Berjejer -->
              <div class="flex flex-col space-y-4">
                <!-- Button 1: Camera -->
                <button type="button" onclick={openCameraModal} class="flex items-center justify-center w-14 h-14 bg-gray-50 hover:bg-slate-700 text-slate-700 hover:text-white rounded-2xl shadow-sm transition-all border border-gray-200 hover:border-slate-700 group" title="Buka Kamera">
                  <Camera class="w-6 h-6" />
                </button>
                
                <!-- Button 2: Gallery -->
                <label class="flex items-center justify-center w-14 h-14 bg-gray-50 hover:bg-gray-700 text-gray-700 hover:text-white rounded-2xl shadow-sm transition-all border border-gray-200 hover:border-gray-700 cursor-pointer group" title="Buka Galeri (Pilih File)">
                  <FolderOpen class="w-6 h-6" />
                  <input type="file" accept="image/*" onchange={handleDocumentUpload} class="hidden"/>
                </label>
              </div>

              {#if isUploadingDoc}
                <div class="flex-1 pl-2">
                  <p class="text-sm text-indigo-600 font-semibold animate-pulse bg-indigo-50 py-3 px-4 rounded-2xl border border-indigo-100 inline-block shadow-sm">⏳ Sedang mengunggah...</p>
                </div>
              {/if}
            </div>
          </div>

          {#if errorMsg}
            <div class="rounded-md bg-red-50 p-4">
              <div class="flex">
                <div class="ml-3">
                  <h3 class="text-sm font-medium text-red-800">Error</h3>
                  <div class="mt-2 text-sm text-red-700">
                    <p>{errorMsg}</p>
                  </div>
                </div>
              </div>
            </div>
          {/if}



          <div class="pt-5">
            <div class="flex">
              <button
                type="submit"
                disabled={isSaving || isUploading || isUploadingDoc}
                class="w-full inline-flex justify-center py-4 px-6 border border-transparent shadow-lg text-lg font-bold rounded-2xl text-white bg-slate-700 hover:bg-slate-800 transform transition hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:transform-none"
              >
                {isSaving ? 'Menyimpan...' : 'Simpan Biodata'}
              </button>
            </div>
          </div>
        </form>
      {/if}

    </div>
  </div>
</div>

{#if showCameraModal}
  <div class="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-fade-in">
    <div class="bg-white rounded-3xl p-6 max-w-3xl w-full shadow-2xl relative flex flex-col">
      <h3 class="text-xl font-bold text-gray-900 mb-4">Ambil Foto Dokumen</h3>
      
      <div class="relative w-full max-w-sm mx-auto bg-black rounded-2xl overflow-hidden aspect-[3/4] flex items-center justify-center">
        <!-- svelte-ignore a11y_media_has_caption -->
        <video bind:this={videoElement} class="absolute inset-0 w-full h-full object-cover" autoplay playsinline></video>
        <!-- Overlay Frame Panduan -->
        <div class="absolute inset-0 border-4 border-white/60 m-4 rounded-xl pointer-events-none z-10 shadow-[0_0_0_9999px_rgba(0,0,0,0.5)]"></div>
        <div class="absolute top-8 text-white/80 text-sm font-bold bg-black/50 px-3 py-1 rounded-full z-20">Posisikan Kertas Dalam Kotak</div>
        <canvas bind:this={canvasElement} class="hidden"></canvas>
      </div>

      <!-- Panel Kontrol Kamera Bawah -->
      <div class="mt-6 flex items-center justify-between px-4">
        <button type="button" onclick={closeCameraModal} class="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold rounded-full transition-colors">
          Batal
        </button>
        
        <!-- Shutter Button (Bulat seperti kamera asli) -->
        <button type="button" onclick={capturePhoto} class="w-16 h-16 bg-white border-4 border-gray-200 hover:border-slate-400 rounded-full shadow-lg flex items-center justify-center transition-all transform hover:scale-105 group" title="Jepret Foto">
          <div class="w-12 h-12 bg-slate-700 group-hover:bg-slate-800 rounded-full flex items-center justify-center transition-colors">
            <Camera class="w-6 h-6 text-white" />
          </div>
        </button>
        
        <!-- Spacer untuk menyeimbangkan posisi tengah shutter -->
        <div class="w-16"></div>
      </div>
    </div>
  </div>
{/if}
