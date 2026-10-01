<script lang="ts">
  import { onMount } from 'svelte';
  import { supabase } from '$lib/supabaseClient';
  import { exportToExcel } from '$lib/utils/excelExport';
  import * as Papa from 'papaparse';
  import JSZip from 'jszip';
  import { Download, Upload as UploadIcon, Users, FileImage, Search, Filter, ChevronDown, Check, X, Phone, Mail, UserCircle2, Home } from 'lucide-svelte';

  let siswiList = $state<any[]>([]);
  let filteredList = $state<any[]>([]);
  let isLoading = $state(true);
  let isUploadingCsv = $state(false);
  let isDownloadingZip = $state(false);
  let csvError = $state('');
  let csvSuccess = $state('');
  
  // Stats
  let totalData = $derived(siswiList.length);
  let totalSudah = $derived(siswiList.filter(s => getStatusType(s) === 'Lengkap').length);
  let totalKurang = $derived(siswiList.filter(s => getStatusType(s) === 'Kurang').length);
  let totalBelum = $derived(siswiList.filter(s => getStatusType(s) === 'Belum').length);
  
  // Modal Detail state
  let selectedSiswiDetail = $state<any>(null);
  let showAddSiswiModal = $state(false);
  let toastMessage = $state({ show: false, type: 'success', title: '', message: '' });
  let confirmModal = $state({ show: false, title: '', message: '', type: 'warning', onConfirm: () => {} });
  let newSiswiNis = $state('');
  let newSiswiName = $state('');
  let isAddingSiswi = $state(false);
  
  // Image Preview state
  let previewImage = $state<{url: string, filename: string} | null>(null);
  let previewRotation = $state(0);

    
  
  // Fungsi untuk memutar gambar sesuai derajat
  async function rotateImageLeft(blob: Blob, angle = -90): Promise<Blob> {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement('canvas');
        if (Math.abs(angle) % 180 === 90) {
          canvas.width = img.height;
          canvas.height = img.width;
        } else {
          canvas.width = img.width;
          canvas.height = img.height;
        }
        
        const ctx = canvas.getContext('2d');
        if (ctx) {
          ctx.translate(canvas.width / 2, canvas.height / 2);
          ctx.rotate(angle * Math.PI / 180);
          ctx.drawImage(img, -img.width / 2, -img.height / 2);
          
          canvas.toBlob((rotatedBlob) => {
            resolve(rotatedBlob || blob); // Fallback ke original jika gagal
          }, blob.type || 'image/jpeg', 0.95);
        } else {
          resolve(blob as Blob);
        }
      };
      img.onerror = () => resolve(blob as Blob); // Fallback ke original jika error
      img.src = URL.createObjectURL(blob);
    });
  }

  async function downloadImage(url, filename) {
    try {
      showToast('success', 'Mengunduh...', 'Mohon tunggu, foto sedang diunduh.');
      const response = await fetch(url);
      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = blobUrl;
      const extMatch = url.match(/\.([^.?]+)(\?.*)?$/);
      const ext = extMatch ? extMatch[1] : 'jpg';
      a.download = `${filename}.${ext}`;
      
      document.body.appendChild(a);
      a.click();
      
      window.URL.revokeObjectURL(blobUrl);
      document.body.removeChild(a);
    } catch (error: any) {
      showToast('error', 'Gagal', 'Gagal mengunduh foto: ' + error.message);
    }
  }

  function showToast(type, title, message) {
    toastMessage = { show: true, type, title, message };
    setTimeout(() => {
      toastMessage.show = false;
    }, 4000);
  }

  function requestResetSiswi(siswiId) {
    confirmModal = {
      show: true,
      title: 'Reset Formulir Siswi?',
      message: 'Semua data yang diisi (foto, WA, hobi, dll) akan dihapus secara permanen, tetapi nama dan NIS tetap aman di database.',
      type: 'warning',
      onConfirm: () => resetSiswiForm(siswiId)
    };
  }

  async function resetSiswiForm(siswiId) {
    confirmModal.show = false;
    const { error } = await supabase
      .from('siswi')
      .update({
        whatsapp_number: null,
        whatsapp_provider: null,
        blood_type: null,
        residence: null,
        travel_route: null,
        email: null,
        instagram: null,
        tiktok: null,
        twitter_x: null,
        hobbies: null,
        aspirations: null,
        favorite_food: null,
        favorite_drink: null,
        favorite_music: null,
        favorite_color: null,
        quote: null,
        impression: null,
        message: null,
        paper_form_url: null,
        paper_form_url_2: null,
        is_completed: false,
        updated_at: null
      })
      .eq('id', siswiId);
      
    if (error) {
      showToast('error', 'Gagal Reset', error.message);
    } else {
      showToast('success', 'Berhasil', 'Formulir siswi berhasil direset.');
      selectedSiswiDetail = null;
      await fetchData();
    }
  }

  function requestDeleteSiswi(siswiId) {
    confirmModal = {
      show: true,
      title: 'Hapus Siswi Permanen?',
      message: 'PERINGATAN BAHAYA: Data nama dan NIS siswi ini akan musnah selamanya dari database. Tindakan ini tidak bisa dibatalkan!',
      type: 'danger',
      onConfirm: () => deleteSiswiData(siswiId)
    };
  }

  async function deleteSiswiData(siswiId) {
    confirmModal.show = false;
    const { error } = await supabase
      .from('siswi')
      .delete()
      .eq('id', siswiId);
      
    if (error) {
      showToast('error', 'Gagal Hapus', error.message);
    } else {
      showToast('success', 'Berhasil', 'Data siswi telah musnah secara permanen.');
      selectedSiswiDetail = null;
      await fetchData();
    }
  }

  // Helper untuk menentukan status Kelengkapan
  function getStatusType(siswi) {
    if (!siswi.is_completed) return 'Belum';
    
    // Cek apakah ada field penting yang masih kosong
    const importantFields = [
      'whatsapp_number', 'blood_type', 'hobbies', 
      'aspirations', 'quote', 'paper_form_url'
    ];
    
    const isKurang = importantFields.some(field => !siswi[field] || siswi[field].toString().trim() === '');
    
    if (isKurang) return 'Kurang';
    return 'Lengkap';
  }
  
  // Filter states
  let searchQuery = $state('');
  let statusFilter = $state('Semua');
  let showStatusDropdown = $state(false);

  onMount(async () => {
    await fetchData();
  });

    async function addSiswiManual() {
    if (!newSiswiName.trim()) {
      showToast('error', 'Peringatan', 'Nama lengkap tidak boleh kosong!');
      return;
    }
    
    isAddingSiswi = true;
    const { error } = await supabase
      .from('siswi')
      .insert({ 
        nis: newSiswiNis.trim() || null,
        full_name: newSiswiName.trim().toUpperCase(),
        is_completed: false
      });
      
    if (error) {
      showToast('error', 'Gagal Tambah', error.message);
    } else {
      showAddSiswiModal = false;
      newSiswiNis = '';
      newSiswiName = '';
      await fetchData();
      showToast('success', 'Berhasil', 'Siswi baru berhasil ditambahkan.');
    }
    isAddingSiswi = false;
  }

  async function fetchData() {
    isLoading = true;
    const { data, error } = await supabase
      .from('siswi')
      .select('*')
      .order('full_name');
    
    if (error) {
      console.error('Error fetching data:', error);
    } else {
      siswiList = data || [];
      applyFilters();
    }
    isLoading = false;
  }
  
  function applyFilters() {
    let result = siswiList;
    
    // Status Filter
    if (statusFilter === 'Sudah') {
      result = result.filter(s => getStatusType(s) === 'Lengkap');
    } else if (statusFilter === 'Kurang') {
      result = result.filter(s => getStatusType(s) === 'Kurang');
    } else if (statusFilter === 'Belum') {
      result = result.filter(s => getStatusType(s) === 'Belum');
    }
    
    // Search Query (Nama atau NIS)
    if (searchQuery.trim() !== '') {
      const q = searchQuery.toLowerCase();
      result = result.filter(s => 
        (s.full_name && s.full_name.toLowerCase().includes(q)) || 
        (s.nis && s.nis.toString().toLowerCase().includes(q))
      );
    }
    
    filteredList = result;
  }

  function handleCsvUpload(e: Event) {
    const target = e.target as HTMLInputElement;
    const file = target.files?.[0];
    if (!file) return;

    isUploadingCsv = true;
    csvError = '';
    csvSuccess = '';

    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      complete: async (results) => {
        const rows = results.data as any[];
        const toInsert = rows.map(row => {
          return {
            nis: row.nis || row.NIS || null,
            full_name: row.full_name || row.nama || row.Nama || row.NAMA || row['Nama Lengkap'] || row['NAMA LENGKAP'] || 'Tanpa Nama'
          };
        });

        if (toInsert.length === 0) {
          csvError = 'File CSV kosong atau format tidak sesuai.';
          isUploadingCsv = false;
          return;
        }

        const { error } = await supabase
          .from('siswi')
          .insert(toInsert);

        if (error) {
          csvError = 'Gagal import data: ' + error.message;
        } else {
          csvSuccess = `Berhasil import ${toInsert.length} data siswi.`;
          await fetchData();
        }
        isUploadingCsv = false;
        target.value = '';
      },
      error: (err) => {
        csvError = 'Error parsing CSV: ' + err.message;
        isUploadingCsv = false;
      }
    });
  }

  
  async function downloadAllPhotosZip() {
    isDownloadingZip = true;
    showToast('success', 'Mempersiapkan ZIP', 'Sedang mengambil foto, ini mungkin butuh waktu...');
    
    try {
      const zip = new JSZip();
      const folderDpn = zip.folder("Foto_Bagian_Depan");
      const folderBlk = zip.folder("Foto_Bagian_Belakang");
      let hasFiles = false;
      
      const withPhotos = siswiList.filter(s => s.paper_form_url || s.paper_form_url_2);
      
      if (withPhotos.length === 0) {
        showToast('error', 'Kosong', 'Belum ada foto yang diupload.');
        isDownloadingZip = false;
        return;
      }
      
      const fetchImage = async (url, filename, isDepan) => {
        try {
          const res = await fetch(url);
          let blob = await res.blob();
          
          // Memutar SEMUA foto 90 derajat ke kiri (karena instruksi ke siswi adalah memotret landscape)
          blob = await rotateImageLeft(blob, -90);
          
          if (isDepan && folderDpn) {
            folderDpn.file(filename, blob);
          } else if (folderBlk) {
            folderBlk.file(filename, blob);
          }
          hasFiles = true;
        } catch (e) {
          console.error('Failed to fetch', url, e);
        }
      };

      const promises = [];
      for (const siswi of withPhotos) {
        let nama = (siswi.full_name || 'Tanpa_Nama').trim();
        nama = nama.replace(/[^a-zA-Z0-9 ]/g, "").trim(); 
        
        if (siswi.paper_form_url) {
          let ext = siswi.paper_form_url.split('.').pop().split('?')[0];
          if (ext.length > 4 || !ext.match(/^[a-zA-Z]+$/)) ext = 'jpg';
          promises.push(fetchImage(siswi.paper_form_url, `(DPN) ${nama}.${ext}`, true));
        }
        if (siswi.paper_form_url_2) {
          let ext = siswi.paper_form_url_2.split('.').pop().split('?')[0];
          if (ext.length > 4 || !ext.match(/^[a-zA-Z]+$/)) ext = 'jpg';
          promises.push(fetchImage(siswi.paper_form_url_2, `(BLK) ${nama}.${ext}`, false));
        }
      }
      
      await Promise.all(promises);
      
      if (hasFiles) {
        showToast('success', 'Membuat ZIP', 'Sedang mengkompres file...');
        const content = await zip.generateAsync({type:"blob"});
        
        const url = window.URL.createObjectURL(content);
        const a = document.createElement('a');
        a.href = url;
        a.download = "Arsip_Foto_Siswi_Mazeeda.zip";
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showToast('success', 'Berhasil', 'File ZIP berhasil diunduh!');
      } else {
        showToast('error', 'Gagal', 'Gagal mengambil foto-foto tersebut.');
      }
    } catch (err: any) {
      showToast('error', 'Gagal', 'Terjadi kesalahan saat membuat ZIP: ' + err.message);
    }
    
    isDownloadingZip = false;
  }

  function doExport() {
    exportToExcel(siswiList, 'Rekap_Data_Siswi_Mazeeda.xlsx');
  }

</script>

<div class="min-h-screen bg-slate-50 py-4 sm:py-12 px-4 sm:px-6 lg:px-8 font-sans">
  <div class="max-w-[90rem] mx-auto bg-white rounded-3xl shadow-xl ring-1 ring-black/5 overflow-hidden">
    
    <!-- Banner Header Polos -->
    <div class="relative h-48 sm:h-64 w-full bg-slate-200 group">
      <img src="/banner.jpg" alt="Banner Admin" class="w-full h-full object-cover" />
      
      <!-- Tombol Kembali ke Home -->
      <a href="/" title="Kembali ke Form Utama" class="absolute top-4 right-4 p-2.5 bg-white/10 hover:bg-white/30 backdrop-blur-md rounded-full text-white transition-all shadow-sm group border border-white/10">
        <Home class="w-5 h-5 opacity-70 group-hover:opacity-100 transform group-hover:scale-110 transition-all" />
      </a>
    </div>

    <div class="p-4 sm:p-8">
      
      <!-- Header Section & Actions -->
      <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-6 mb-8">
        
        <!-- Statistik (Tengah di Mobile, Kiri di Desktop) -->
        <div class="flex flex-wrap items-center justify-center lg:justify-start gap-3 w-full lg:w-auto">
          <div class="flex items-center px-5 py-2.5 bg-white rounded-xl border border-slate-200 shadow-sm">
            <span class="text-[11px] sm:text-xs font-bold text-slate-500 uppercase tracking-wider mr-3">Total</span>
            <span class="text-sm sm:text-base font-extrabold text-slate-800">{totalData}</span>
          </div>
          
          <div class="flex items-center px-5 py-2.5 bg-white rounded-xl border border-slate-200 shadow-sm">
            <span class="w-2 h-2 rounded-full bg-emerald-500 mr-2"></span>
            <span class="text-[11px] sm:text-xs font-bold text-slate-500 uppercase tracking-wider mr-3">Lengkap</span>
            <span class="text-sm sm:text-base font-extrabold text-slate-800">{totalSudah}</span>
          </div>
          
          <div class="flex items-center px-5 py-2.5 bg-white rounded-xl border border-slate-200 shadow-sm">
            <span class="w-2 h-2 rounded-full bg-amber-500 mr-2 animate-pulse"></span>
            <span class="text-[11px] sm:text-xs font-bold text-slate-500 uppercase tracking-wider mr-3">Kurang</span>
            <span class="text-sm sm:text-base font-extrabold text-slate-800">{totalKurang}</span>
          </div>
          
          <div class="flex items-center px-5 py-2.5 bg-white rounded-xl border border-slate-200 shadow-sm">
            <span class="w-2 h-2 rounded-full bg-slate-400 mr-2"></span>
            <span class="text-[11px] sm:text-xs font-bold text-slate-500 uppercase tracking-wider mr-3">Belum</span>
            <span class="text-sm sm:text-base font-extrabold text-slate-800">{totalBelum}</span>
          </div>
        </div>
        
        <!-- Tombol Aksi (Tengah di Mobile, Kanan di Desktop) -->
        <div class="flex flex-wrap items-center justify-center lg:justify-end gap-3 w-full lg:w-auto">
          <button 
                type="button" 
                onclick={downloadAllPhotosZip}
                disabled={isDownloadingZip}
                class="inline-flex items-center justify-center px-4 py-2 border border-slate-200 rounded-xl shadow-sm text-sm font-bold text-slate-700 bg-white hover:bg-slate-50 hover:border-slate-300 transition-all focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {#if isDownloadingZip}
                  <span class="w-4 h-4 rounded-full border-2 border-slate-200 border-t-slate-700 animate-spin sm:mr-2"></span>
                  <span class="hidden sm:inline text-slate-500">Memproses...</span>
                {:else}
                  <FileImage class="h-4 w-4 sm:mr-2 text-slate-800" />
                  <span class="hidden sm:inline">Download (.zip)</span>
                {/if}
              </button>
            <label class="cursor-pointer inline-flex items-center justify-center px-4 py-2 border border-slate-200 rounded-xl shadow-sm text-sm font-bold text-slate-700 bg-white hover:bg-slate-50 hover:border-slate-300 transition-all focus:outline-none">
            <UploadIcon class="h-4 w-4 sm:mr-2 text-slate-800" />
            <span class="hidden sm:inline">Import CSV</span>
            <input type="file" accept=".csv" class="hidden" onchange={handleCsvUpload} disabled={isUploadingCsv} />
          </label>
          
          <button onclick={doExport} class="inline-flex items-center justify-center px-4 py-2 border border-transparent rounded-xl shadow-md text-sm font-bold text-white bg-slate-700 hover:bg-slate-800 transition-all focus:outline-none">
            <Download class="h-4 w-4 sm:mr-2" />
            <span class="hidden sm:inline">Export Excel</span>
          </button>
        </div>
      </div>

      <!-- Alerts -->
      {#if csvError}
        <div class="mb-6 bg-red-50 border border-red-200 p-4 rounded-xl">
          <p class="text-sm font-semibold text-red-700">{csvError}</p>
        </div>
      {/if}
      {#if csvSuccess}
        <div class="mb-6 bg-green-50 border border-green-200 p-4 rounded-xl">
          <p class="text-sm font-semibold text-green-700">{csvSuccess}</p>
        </div>
      {/if}

      <!-- Filters Section -->
      <div class="flex flex-col sm:flex-row gap-4 mb-6 p-4 bg-slate-50 rounded-2xl border border-slate-100">
        <!-- Search Box -->
        <div class="relative flex-1">
          <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search class="h-5 w-5 text-slate-400" />
          </div>
          <input type="text" bind:value={searchQuery} oninput={applyFilters} placeholder="Cari Nama atau NIS..." class="block w-full pl-10 pr-3 py-2.5 border border-slate-200 rounded-xl leading-5 bg-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-400 focus:border-slate-400 sm:text-sm transition-colors" />
        </div>
        
        <!-- Tambah Siswi Button -->
          <button type="button" onclick={() => showAddSiswiModal = true} class="flex items-center justify-center px-4 py-2.5 bg-slate-800 text-white text-sm font-bold rounded-xl shadow-sm hover:bg-slate-700 transition-colors shrink-0">
            + Tambah
          </button>
          
          <!-- Status Filter Custom -->
        <div class="relative min-w-[180px]">
          <button 
            type="button" 
            onclick={() => showStatusDropdown = !showStatusDropdown}
            class="w-full flex items-center justify-between pl-3 pr-3 py-2.5 text-slate-700 border border-slate-200 rounded-xl leading-5 bg-white hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-slate-400 focus:border-slate-400 sm:text-sm font-medium cursor-pointer transition-colors"
          >
            <div class="flex items-center">
              <Filter class="h-4 w-4 text-slate-400 mr-2" />
              <span>{statusFilter === 'Semua' ? 'Semua Status' : statusFilter === 'Sudah' ? 'Lengkap' : statusFilter === 'Kurang' ? 'Kurang Lengkap' : 'Belum Mengisi'}</span>
            </div>
            <ChevronDown class="h-4 w-4 text-slate-400 {showStatusDropdown ? 'rotate-180' : ''} transition-transform duration-200" />
          </button>
          
          {#if showStatusDropdown}
            <!-- svelte-ignore a11y_click_events_have_key_events -->
            <!-- svelte-ignore a11y_no_static_element_interactions -->
            <div class="fixed inset-0 z-10" onclick={() => showStatusDropdown = false}></div>
            <div class="absolute z-20 mt-2 w-full bg-white border border-slate-200 rounded-xl shadow-lg overflow-hidden animate-fade-in origin-top-right">
              <div class="py-1">
                {#each ['Semua', 'Sudah', 'Kurang', 'Belum'] as status}
                  <button 
                    type="button"
                    class="w-full text-left px-4 py-2.5 text-sm hover:bg-slate-50 focus:outline-none flex items-center justify-between {statusFilter === status ? 'text-slate-800 font-bold bg-slate-100' : 'text-slate-700 font-medium'}"
                    onclick={() => { statusFilter = status; applyFilters(); showStatusDropdown = false; }}
                  >
                    {status === 'Semua' ? 'Semua Status' : status === 'Sudah' ? 'Lengkap' : status === 'Kurang' ? 'Kurang Lengkap' : 'Belum Mengisi'}
                    {#if statusFilter === status}
                      <Check class="h-4 w-4 text-slate-800" />
                    {/if}
                  </button>
                {/each}
              </div>
            </div>
          {/if}
        </div>
      </div>

      <!-- Tabel Data (Responsive Scroll) -->
      <div class="bg-white border border-slate-200 shadow-sm rounded-2xl overflow-hidden">
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-slate-200 border-x border-slate-200">
            <thead class="bg-slate-50">
              <tr class="divide-x divide-slate-200">
                <th scope="col" class="px-2 sm:px-6 py-3 sm:py-4 text-center text-[10px] sm:text-xs font-bold text-slate-500 uppercase tracking-wider w-12 sm:w-24">Status</th>
                <th scope="col" class="px-2 sm:px-6 py-3 sm:py-4 text-center text-[10px] sm:text-xs font-bold text-slate-500 uppercase tracking-wider w-12 sm:w-20">Arsip</th>
                <th scope="col" class="px-4 sm:px-6 py-3 sm:py-4 text-center text-[11px] sm:text-xs font-bold text-slate-500 uppercase tracking-wider w-32 hidden sm:table-cell">NIS</th>
                <th scope="col" class="px-3 sm:px-6 py-3 sm:py-4 text-center text-[10px] sm:text-xs font-bold text-slate-500 uppercase tracking-wider">Nama Lengkap</th>
                <th scope="col" class="px-4 sm:px-6 py-3 sm:py-4 text-center text-[11px] sm:text-xs font-bold text-slate-500 uppercase tracking-wider hidden sm:table-cell">Update Terakhir</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-slate-200">
              {#if isLoading}
                <tr>
                  <td colspan="5" class="px-6 py-12 text-center text-sm font-medium text-slate-400 border-x border-slate-200">
                    <div class="animate-pulse flex flex-col items-center">
                      <div class="w-8 h-8 border-4 border-slate-200 border-t-slate-500 rounded-full animate-spin mb-3"></div>
                      Memuat data...
                    </div>
                  </td>
                </tr>
              {:else if filteredList.length === 0}
                <tr>
                  <td colspan="5" class="px-6 py-12 text-center text-sm font-medium text-slate-500 border-x border-slate-200">
                    <div class="flex flex-col items-center">
                      <Users class="w-12 h-12 text-slate-300 mb-3" />
                      Tidak ada data yang cocok.
                    </div>
                  </td>
                </tr>
              {:else}
                {#each filteredList as siswi}
                  <tr onclick={() => selectedSiswiDetail = siswi} class="hover:bg-slate-50 transition-colors divide-x divide-slate-200 cursor-pointer relative group">
                    <!-- Status -->
                    <td class="px-2 sm:px-6 py-3 sm:py-4 whitespace-nowrap text-center">
                      {#if getStatusType(siswi) === 'Lengkap'}
                        <span class="inline-flex items-center px-1.5 py-0.5 sm:px-2.5 sm:py-1 rounded-full text-[10px] sm:text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-200" title="Data Lengkap">
                          <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 sm:mr-1.5"></span>
                          <span class="hidden sm:inline">Lengkap</span>
                        </span>
                      {:else if getStatusType(siswi) === 'Kurang'}
                        <span class="inline-flex items-center px-1.5 py-0.5 sm:px-2.5 sm:py-1 rounded-full text-[10px] sm:text-xs font-bold bg-amber-100 text-amber-800 border border-amber-200" title="Data Kurang Lengkap">
                          <span class="w-1.5 h-1.5 rounded-full bg-amber-500 sm:mr-1.5 animate-pulse"></span>
                          <span class="hidden sm:inline">Kurang</span>
                        </span>
                      {:else}
                        <span class="inline-flex items-center px-1.5 py-0.5 sm:px-2.5 sm:py-1 rounded-full text-[10px] sm:text-xs font-bold bg-slate-100 text-slate-600 border border-slate-200" title="Belum Mengisi">
                          <span class="w-1.5 h-1.5 rounded-full bg-slate-400 sm:mr-1.5"></span>
                          <span class="hidden sm:inline">Belum</span>
                        </span>
                      {/if}
                    </td>
                    <!-- Arsip -->
                    <td class="px-2 sm:px-6 py-3 sm:py-4 whitespace-nowrap text-center">
                      {#if siswi.paper_form_url}
                        <button type="button" title="Lihat Arsip Kertas" onclick={(e) => { e.stopPropagation(); previewImage = { url: siswi.paper_form_url, filename: `(DPN) ${siswi.full_name}` }; }} class="inline-flex items-center justify-center w-7 h-7 sm:w-8 sm:h-8 bg-slate-100 text-slate-800 rounded-lg hover:bg-slate-700 hover:text-white shadow-sm transition-colors border border-slate-200">
                          <FileImage class="w-3 h-3 sm:w-4 sm:h-4" />
                        </button>
                      {:else}
                        <span class="text-slate-300 text-[10px] sm:text-xs font-medium">-</span>
                      {/if}
                    </td>
                    <!-- NIS (Hanya Desktop) -->
                    <td class="px-4 sm:px-6 py-3 sm:py-4 whitespace-nowrap text-center hidden sm:table-cell">
                      <div class="text-sm font-semibold text-slate-600">{siswi.nis || '-'}</div>
                    </td>
                    <!-- Nama Lengkap (+ NIS & Waktu di Mobile) -->
                    <td class="px-3 sm:px-6 py-3 sm:py-4 text-left">
                      <div class="text-xs sm:text-sm font-medium text-slate-800 break-words">{siswi.full_name}</div>
                      <!-- NIS tampil di bawah nama khusus di HP -->
                      <div class="sm:hidden text-[10px] text-slate-500 font-semibold mt-1">NIS: {siswi.nis || '-'}</div>
                      <div class="sm:hidden text-[10px] text-slate-400 font-medium mt-0.5">
                        {siswi.updated_at ? new Date(siswi.updated_at).toLocaleString('id-ID', {day:'numeric', month:'short', year:'2-digit', hour:'2-digit', minute:'2-digit'}) : 'Belum diupdate'}
                      </div>
                    </td>
                    <!-- Update Terakhir (Hanya Desktop) -->
                    <td class="px-4 sm:px-6 py-3 sm:py-4 whitespace-nowrap text-center text-sm font-medium text-slate-500 hidden sm:table-cell">
                      {siswi.updated_at ? new Date(siswi.updated_at).toLocaleString('id-ID', {day:'numeric', month:'short', year:'numeric', hour:'2-digit', minute:'2-digit'}) : '-'}
                    </td>
                  </tr>
                {/each}
              {/if}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  </div>
</div>

<!-- MODAL DETAIL SISWI -->
{#if selectedSiswiDetail}
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
    <!-- Backdrop -->
    <div class="absolute inset-0 bg-slate-900/40 backdrop-blur-sm transition-opacity" onclick={() => selectedSiswiDetail = null}></div>
    
    <!-- Modal Content -->
    <div class="relative bg-white rounded-3xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col animate-fade-in">
      
      <!-- Header -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50">
        <h3 class="text-lg font-bold text-slate-800 flex items-center">
          <UserCircle2 class="w-5 h-5 mr-2 text-slate-500" />
          Biodata Lengkap Siswi
        </h3>
        <button type="button" onclick={() => selectedSiswiDetail = null} class="text-slate-400 hover:text-slate-600 bg-white hover:bg-slate-200 rounded-full p-2 transition-colors">
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Body (Scrollable) -->
      <div class="p-6 overflow-y-auto custom-scrollbar flex-1">
        
        <div class="flex flex-col sm:flex-row gap-6 mb-8">
          <!-- Kiri: Foto / Status -->
          <div class="flex flex-col items-center sm:items-start sm:w-1/3 gap-4">
            <div class="w-full aspect-[3/4] bg-slate-100 rounded-2xl border-4 border-white shadow-md flex items-center justify-center overflow-hidden cursor-pointer hover:opacity-90 transition-opacity" title="Klik untuk perbesar Halaman 1" onclick={() => { if(selectedSiswiDetail.paper_form_url) previewImage = { url: selectedSiswiDetail.paper_form_url, filename: `(DPN) ${selectedSiswiDetail.full_name}` }; }}>
              {#if selectedSiswiDetail.paper_form_url}
                <img src={selectedSiswiDetail.paper_form_url} class="w-full h-full object-cover" alt="Foto Arsip Halaman 1" />
              {:else}
                <div class="flex flex-col items-center text-slate-300">
                  <FileImage class="w-12 h-12 mb-2" />
                  <span class="text-xs font-semibold text-center px-2">Halaman 1 Kosong</span>
                </div>
              {/if}
            </div>
            
            {#if selectedSiswiDetail.paper_form_url_2}
            <div class="w-full aspect-[3/4] bg-slate-100 rounded-2xl border-4 border-white shadow-md flex items-center justify-center overflow-hidden cursor-pointer hover:opacity-90 transition-opacity" title="Klik untuk perbesar Halaman 2" onclick={() => { previewImage = { url: selectedSiswiDetail.paper_form_url_2, filename: `(BLK) ${selectedSiswiDetail.full_name}` }; }}>
              <img src={selectedSiswiDetail.paper_form_url_2} class="w-full h-full object-cover" alt="Foto Arsip Halaman 2" />
            </div>
            {/if}
            
            <div class="w-full mt-2">
            
            <div class="text-center sm:text-left w-full">
              {#if getStatusType(selectedSiswiDetail) === 'Lengkap'}
                <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 w-full justify-center sm:justify-start border border-emerald-200">
                  <span class="w-2 h-2 rounded-full bg-emerald-500 mr-2"></span>
                  Data Lengkap
                </span>
              {:else if getStatusType(selectedSiswiDetail) === 'Kurang'}
                <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 w-full justify-center sm:justify-start border border-amber-200">
                  <span class="w-2 h-2 rounded-full bg-amber-500 mr-2 animate-pulse"></span>
                  Kurang Lengkap
                </span>
              {:else}
                <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-slate-100 text-slate-600 w-full justify-center sm:justify-start border border-slate-200">
                  <span class="w-2 h-2 rounded-full bg-slate-400 mr-2"></span>
                  Belum Diisi
                </span>
              {/if}
            </div>
          </div>
          
          </div>
          
          <!-- Kanan: Info Utama -->
          <div class="flex-1">
            <h2 class="text-2xl font-extrabold text-slate-900 mb-1">{selectedSiswiDetail.full_name}</h2>
            <p class="text-sm font-semibold text-slate-500 mb-4">NIS: {selectedSiswiDetail.nis || 'Belum ada'}</p>
            
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div class="bg-slate-50 p-3 rounded-xl border border-slate-100">
                <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">WhatsApp</p>
                <div class="flex items-center text-sm font-semibold text-slate-700">
                  <Phone class="w-4 h-4 mr-2 text-slate-400" />
                  {#if selectedSiswiDetail.whatsapp_number}
                    <a href="https://wa.me/{selectedSiswiDetail.whatsapp_number.replace(/^0/, '62').replace(/\D/g, '')}" target="_blank" class="text-slate-800 font-bold hover:text-black underline decoration-slate-300 underline-offset-2">
                      {selectedSiswiDetail.whatsapp_number}
                    </a>
                  {:else}
                    -
                  {/if}
                  {#if selectedSiswiDetail.whatsapp_provider && selectedSiswiDetail.whatsapp_provider !== 'Unknown'}
                    <span class="ml-2 text-[10px] bg-white px-2 py-0.5 rounded border border-slate-200">{selectedSiswiDetail.whatsapp_provider}</span>
                  {/if}
                </div>
              </div>
              
              <div class="bg-slate-50 p-3 rounded-xl border border-slate-100">
                <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Instagram</p>
                <div class="flex items-center text-sm font-semibold text-slate-700">
                  <span class="mr-2 text-slate-400 font-bold">@</span>
                  {#if selectedSiswiDetail.instagram}
                    <a href="https://instagram.com/{selectedSiswiDetail.instagram.replace('@', '')}" target="_blank" class="text-slate-800 font-bold hover:text-black underline decoration-slate-300 underline-offset-2">
                      {selectedSiswiDetail.instagram}
                    </a>
                  {:else}
                    -
                  {/if}
                </div>
              </div>
              
              <div class="bg-slate-50 p-3 rounded-xl border border-slate-100">
                <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">TikTok</p>
                <div class="flex items-center text-sm font-semibold text-slate-700">
                  <span class="mr-2 text-slate-400 font-bold">♪</span>
                  {#if selectedSiswiDetail.tiktok}
                    <a href="https://tiktok.com/@{selectedSiswiDetail.tiktok.replace('@', '')}" target="_blank" class="text-slate-800 font-bold hover:text-black underline decoration-slate-300 underline-offset-2">
                      {selectedSiswiDetail.tiktok}
                    </a>
                  {:else}
                    -
                  {/if}
                </div>
              </div>

              <div class="bg-slate-50 p-3 rounded-xl border border-slate-100">
                <p class="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">Twitter / X</p>
                <div class="flex items-center text-sm font-semibold text-slate-700">
                  <span class="mr-2 text-slate-400 font-bold">𝕏</span>
                  {#if selectedSiswiDetail.twitter}
                    <a href="https://twitter.com/{selectedSiswiDetail.twitter.replace('@', '')}" target="_blank" class="text-slate-800 font-bold hover:text-black underline decoration-slate-300 underline-offset-2">
                      {selectedSiswiDetail.twitter}
                    </a>
                  {:else}
                    -
                  {/if}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Detail Grid -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <!-- Info Pribadi -->
          <div>
            <h4 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 border-b border-slate-100 pb-2">Informasi Pribadi</h4>
            <ul class="space-y-3">
              <li>
                <span class="block text-xs text-slate-500">Golongan Darah</span>
                <span class="block text-sm font-semibold text-slate-800">{selectedSiswiDetail.blood_type || '-'}</span>
              </li>
              <li>
                <span class="block text-xs text-slate-500">Tempat Tinggal</span>
                <span class="block text-sm font-semibold text-slate-800">{selectedSiswiDetail.residence || '-'}</span>
              </li>
              <li>
                <span class="block text-xs text-slate-500">Rute Perjalanan</span>
                <span class="block text-sm font-semibold text-slate-800">{selectedSiswiDetail.travel_route || '-'}</span>
              </li>
              <li>
                <span class="block text-xs text-slate-500">Alamat Email</span>
                <span class="block text-sm font-semibold text-slate-800">
                  {#if selectedSiswiDetail.email}
                    <a href="mailto:{selectedSiswiDetail.email}" class="text-slate-800 font-bold hover:text-black underline decoration-slate-300 underline-offset-2">{selectedSiswiDetail.email}</a>
                  {:else}
                    -
                  {/if}
                </span>
              </li>
            </ul>
          </div>

          <!-- Minat & Favorit -->
          <div>
            <h4 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 border-b border-slate-100 pb-2">Minat & Favorit</h4>
            <ul class="space-y-3">
              <li>
                <span class="block text-xs text-slate-500">Hobi</span>
                <span class="block text-sm font-semibold text-slate-800">{selectedSiswiDetail.hobbies || '-'}</span>
              </li>
              <li>
                <span class="block text-xs text-slate-500">Cita-cita</span>
                <span class="block text-sm font-semibold text-slate-800">{selectedSiswiDetail.aspirations || '-'}</span>
              </li>
              <li>
                <span class="block text-xs text-slate-500">Makanan Favorit</span>
                <span class="block text-sm font-semibold text-slate-800">{selectedSiswiDetail.favorite_food || '-'}</span>
              </li>
              <li>
                <span class="block text-xs text-slate-500">Minuman Favorit</span>
                <span class="block text-sm font-semibold text-slate-800">{selectedSiswiDetail.favorite_drink || '-'}</span>
              </li>
              <li>
                <span class="block text-xs text-slate-500">Musik / Lagu Favorit</span>
                <span class="block text-sm font-semibold text-slate-800">{selectedSiswiDetail.favorite_music || '-'}</span>
              </li>
              <li>
                <span class="block text-xs text-slate-500">Warna Favorit</span>
                <span class="block text-sm font-semibold text-slate-800">{selectedSiswiDetail.favorite_color || '-'}</span>
              </li>
            </ul>
          </div>
          
          <!-- Kesan Pesan -->
          <div class="sm:col-span-2">
            <h4 class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 border-b border-slate-100 pb-2">Buku Kenangan (Quotes & Kesan)</h4>
            <div class="space-y-4">
              <div class="bg-slate-50 p-4 rounded-xl border border-slate-100">
                <span class="block text-xs font-bold text-slate-500 mb-1">Motto Hidup (Quotes):</span>
                <p class="text-sm font-medium text-slate-800 italic">"{selectedSiswiDetail.quote || '-'}"</p>
              </div>
              <div class="bg-slate-50 p-4 rounded-xl border border-slate-100">
                <span class="block text-xs font-bold text-slate-500 mb-1">Kesan Selama Sekolah:</span>
                <p class="text-sm text-slate-700 whitespace-pre-wrap">{selectedSiswiDetail.impression || '-'}</p>
              </div>
              <div class="bg-slate-50 p-4 rounded-xl border border-slate-100">
                <span class="block text-xs font-bold text-slate-500 mb-1">Pesan Untuk Sekolah / Teman:</span>
                <p class="text-sm text-slate-700 whitespace-pre-wrap">{selectedSiswiDetail.message || '-'}</p>
              </div>
            </div>
          </div>
        </div>
        
      </div>
    
        <!-- Action Buttons (Reset / Hapus) -->
        <div class="border-t border-slate-100 p-4 bg-slate-50 flex justify-end gap-3 mt-auto shrink-0 z-20">
          <button type="button" onclick={() => requestResetSiswi(selectedSiswiDetail.id)} class="px-4 py-2 bg-orange-100 text-orange-700 hover:bg-orange-200 font-bold text-xs rounded-xl transition-colors border border-orange-200">
            Reset Formulir
          </button>
          <button type="button" onclick={() => requestDeleteSiswi(selectedSiswiDetail.id)} class="px-4 py-2 bg-red-100 text-red-700 hover:bg-red-200 font-bold text-xs rounded-xl transition-colors border border-red-200">
            Hapus Siswi
          </button>
        </div>
</div>
  </div>
{/if}

<!-- IMAGE PREVIEW MODAL -->
{#if previewImage}
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div class="fixed inset-0 z-[60] flex items-center justify-center p-4 sm:p-6">
    <div class="absolute inset-0 bg-slate-900/90 backdrop-blur-sm transition-opacity" onclick={() => {previewImage = null; previewRotation = 0; }}></div>
    
    <div class="relative max-w-4xl max-h-[90vh] flex flex-col items-center justify-center animate-fade-in w-full h-full">
      <button type="button" onclick={() => {previewImage = null; previewRotation = 0; }} class="absolute top-0 right-0 sm:-top-4 sm:-right-4 bg-white text-slate-800 rounded-full p-2.5 shadow-xl hover:bg-slate-200 transition-colors z-10">
        <X class="w-6 h-6" />
      </button>
      <!-- Tombol Rotate -->
      <div class="absolute top-4 left-1/2 -translate-x-1/2 flex gap-3 z-10 bg-white/10 backdrop-blur-md p-2 rounded-2xl">
        <button type="button" title="Rotate Kiri" onclick={(e) => {e.stopPropagation(); previewRotation -= 90; }} class="bg-white text-slate-800 p-2.5 rounded-xl shadow-lg hover:bg-slate-200 transition-colors">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>
        </button>
        <button type="button" title="Rotate Kanan" onclick={(e) => {e.stopPropagation(); previewRotation += 90; }} class="bg-white text-slate-800 p-2.5 rounded-xl shadow-lg hover:bg-slate-200 transition-colors">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/></svg>
        </button>
      </div>

      <img src={previewImage.url} alt="Arsip Kertas Full" class="max-w-full max-h-[85vh] object-contain rounded-xl shadow-2xl transition-transform duration-300" style="transform: rotate({previewRotation}deg);" />
      
      <!-- Tombol Download (Simpel) -->
      <button 
        type="button" 
        title="Download Foto"
        onclick={() => previewImage && downloadImage(previewImage.url, previewImage.filename)} 
        class="absolute top-0 left-0 sm:-top-4 sm:-left-4 bg-white text-slate-800 rounded-full p-2.5 shadow-xl hover:bg-slate-200 transition-colors z-10"
      >
        <Download class="w-6 h-6" />
      </button>
    </div>
  </div>
{/if}



<!-- ADD SISWI MODAL -->
{#if showAddSiswiModal}
  <div class="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6">
    <div class="absolute inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity" onclick={() => showAddSiswiModal = false}></div>
    <div class="relative bg-white rounded-[2rem] w-full max-w-md shadow-2xl animate-fade-in flex flex-col overflow-hidden transform transition-all border border-slate-100">
      
      <!-- Premium Header -->
      <div class="bg-gradient-to-br from-slate-800 via-slate-800 to-slate-900 p-8 flex flex-col items-center justify-center relative border-b-4 border-indigo-500">
        <button type="button" onclick={() => showAddSiswiModal = false} class="absolute top-4 right-4 p-2 text-slate-400 hover:text-white hover:bg-white/10 rounded-full transition-colors backdrop-blur-sm">
          <X class="w-5 h-5" />
        </button>
        <div class="w-20 h-20 bg-white/5 backdrop-blur-md rounded-full flex items-center justify-center mb-4 ring-1 ring-white/20 shadow-inner">
          <Users class="w-10 h-10 text-indigo-400" />
        </div>
        <h3 class="text-2xl font-extrabold text-white tracking-tight">Tambah Siswi</h3>
        <p class="text-sm text-slate-400 mt-2 font-medium text-center">Masukkan data siswi secara manual ke database.</p>
      </div>
      
      <!-- Body -->
      <div class="p-8 space-y-6 bg-slate-50/50">
        <div>
          <label for="new_nis" class="block text-xs font-black text-slate-500 uppercase tracking-wider mb-2">Nomor Induk Siswi (Opsional)</label>
          <div class="relative">
            <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <span class="text-slate-400 font-mono text-sm">#</span>
            </div>
            <input type="text" id="new_nis" bind:value={newSiswiNis} placeholder="Contoh: 12345" class="w-full pl-10 pr-4 py-3.5 rounded-2xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-sm font-semibold text-slate-800 bg-white shadow-sm transition-all" />
          </div>
        </div>
        
        <div>
          <label for="new_name" class="block text-xs font-black text-slate-500 uppercase tracking-wider mb-2">Nama Lengkap Siswi <span class="text-red-500">*</span></label>
          <div class="relative">
            <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <UserCircle2 class="w-5 h-5 text-slate-400" />
            </div>
            <input type="text" id="new_name" bind:value={newSiswiName} placeholder="Masukkan nama lengkap..." class="w-full pl-11 pr-4 py-3.5 rounded-2xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 text-sm font-semibold text-slate-800 bg-white shadow-sm uppercase transition-all" />
          </div>
        </div>
      </div>
      
      <!-- Footer -->
      <div class="p-6 border-t border-slate-100 bg-white flex justify-end gap-4">
        <button type="button" onclick={() => showAddSiswiModal = false} class="px-6 py-3 text-sm font-bold text-slate-500 bg-slate-50 border border-slate-200 hover:bg-slate-100 rounded-2xl transition-all">Batal</button>
        <button type="button" onclick={addSiswiManual} disabled={isAddingSiswi} class="px-6 py-3 text-sm font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-2xl shadow-lg shadow-indigo-600/30 transition-all disabled:opacity-50 disabled:shadow-none flex items-center">
          {#if isAddingSiswi}
            <span class="w-4 h-4 rounded-full border-2 border-white/30 border-t-white animate-spin mr-2"></span>
            Menyimpan...
          {:else}
            <Check class="w-5 h-5 mr-2" />
            Simpan Data
          {/if}

        </button>
      </div>
    </div>
  </div>
{/if}


<!-- CUSTOM CONFIRM MODAL -->
{#if confirmModal.show}
  <div class="fixed inset-0 z-[200] flex items-center justify-center p-4 sm:p-6">
    <div class="absolute inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity" onclick={() => confirmModal.show = false}></div>
    <div class="relative bg-white rounded-3xl w-full max-w-sm shadow-2xl animate-fade-in flex flex-col overflow-hidden transform transition-all border border-slate-100">
      
      <div class="p-8 flex flex-col items-center text-center">
        {#if confirmModal.type === 'danger'}
          <div class="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mb-5 ring-8 ring-red-50">
            <X class="w-10 h-10 text-red-600" />
          </div>
          <h3 class="text-2xl font-extrabold text-slate-800 mb-3">{confirmModal.title}</h3>
          <p class="text-sm font-medium text-slate-500 leading-relaxed">{confirmModal.message}</p>
        {:else}
          <div class="w-20 h-20 bg-orange-100 rounded-full flex items-center justify-center mb-5 ring-8 ring-orange-50">
            <span class="text-4xl">⚠️</span>
          </div>
          <h3 class="text-2xl font-extrabold text-slate-800 mb-3">{confirmModal.title}</h3>
          <p class="text-sm font-medium text-slate-500 leading-relaxed">{confirmModal.message}</p>
        {/if}
      </div>
      
      <div class="p-6 border-t border-slate-100 bg-slate-50 flex gap-4">
        <button type="button" onclick={() => confirmModal.show = false} class="flex-1 py-3.5 text-sm font-bold text-slate-600 bg-white border border-slate-200 hover:bg-slate-100 rounded-xl transition-all">
          Batal
        </button>
        <button type="button" onclick={confirmModal.onConfirm} class="flex-1 py-3.5 text-sm font-bold text-white rounded-xl shadow-lg transition-all {confirmModal.type === 'danger' ? 'bg-red-600 hover:bg-red-700 shadow-red-600/30' : 'bg-orange-500 hover:bg-orange-600 shadow-orange-500/30'}">
          Ya, Lanjutkan
        </button>
      </div>
      
    </div>
  </div>
{/if}


<!-- CUSTOM TOAST NOTIFICATION -->
{#if toastMessage.show}
  <div class="fixed top-6 left-1/2 -translate-x-1/2 z-[300] animate-fade-in">
    <div class="flex items-center p-4 pr-6 rounded-2xl shadow-2xl {toastMessage.type === 'success' ? 'bg-emerald-600' : 'bg-red-600'} text-white space-x-4 min-w-[300px]">
      <div class="flex-shrink-0 bg-white/20 p-2 rounded-full">
        {#if toastMessage.type === 'success'}
          <Check class="w-6 h-6 text-white" />
        {:else}
          <X class="w-6 h-6 text-white" />
        {/if}
      </div>
      <div>
        <h4 class="text-sm font-extrabold">{toastMessage.title}</h4>
        <p class="text-xs font-medium text-white/90 mt-0.5">{toastMessage.message}</p>
      </div>
    </div>
  </div>
{/if}
