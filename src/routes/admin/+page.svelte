<script lang="ts">
  import { onMount } from 'svelte';
  import { supabase } from '$lib/supabaseClient';
  import { exportToExcel } from '$lib/utils/excelExport';
  import * as Papa from 'papaparse';
  import { Download, Upload as UploadIcon, Users, FileImage, Search, Filter, ChevronDown, Check, X, Phone, Mail, UserCircle2, Home } from 'lucide-svelte';

  let siswiList = $state<any[]>([]);
  let filteredList = $state<any[]>([]);
  let isLoading = $state(true);
  let isUploadingCsv = $state(false);
  let csvError = $state('');
  let csvSuccess = $state('');
  
  // Stats
  let totalData = $derived(siswiList.length);
  let totalSudah = $derived(siswiList.filter(s => getStatusType(s) === 'Lengkap').length);
  let totalKurang = $derived(siswiList.filter(s => getStatusType(s) === 'Kurang').length);
  let totalBelum = $derived(siswiList.filter(s => getStatusType(s) === 'Belum').length);
  
  // Modal Detail state
  let selectedSiswiDetail = $state<any>(null);
  
  // Image Preview state
  let previewImageUrl = $state<string | null>(null);

  async function resetSiswiForm(siswiId) {
    if (!confirm('Yakin ingin mereset formulir siswi ini? Semua data yang diisi (foto, WA, hobi, dll) akan dihapus, tetapi nama dan NIS tetap ada di database.')) return;
    
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
        twitter: null,
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
      alert('Gagal mereset data: ' + error.message);
    } else {
      alert('Formulir berhasil direset!');
      selectedSiswiDetail = null;
      await fetchSiswiList();
    }
  }

  async function deleteSiswiData(siswiId) {
    if (!confirm('PERINGATAN BAHAYA: Yakin ingin menghapus siswi ini secara PERMANEN dari database? Data nama dan NIS akan hilang selamanya.')) return;
    
    const { error } = await supabase
      .from('siswi')
      .delete()
      .eq('id', siswiId);
      
    if (error) {
      alert('Gagal menghapus data: ' + error.message);
    } else {
      alert('Data siswi berhasil dihapus permanen!');
      selectedSiswiDetail = null;
      await fetchSiswiList();
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
                        <button type="button" title="Lihat Arsip Kertas" onclick={(e) => { e.stopPropagation(); previewImageUrl = siswi.paper_form_url; }} class="inline-flex items-center justify-center w-7 h-7 sm:w-8 sm:h-8 bg-slate-100 text-slate-800 rounded-lg hover:bg-slate-700 hover:text-white shadow-sm transition-colors border border-slate-200">
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
            <div class="w-full aspect-[3/4] bg-slate-100 rounded-2xl border-4 border-white shadow-md flex items-center justify-center overflow-hidden cursor-pointer hover:opacity-90 transition-opacity" title="Klik untuk perbesar Halaman 1" onclick={() => { if(selectedSiswiDetail.paper_form_url) previewImageUrl = selectedSiswiDetail.paper_form_url; }}>
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
            <div class="w-full aspect-[3/4] bg-slate-100 rounded-2xl border-4 border-white shadow-md flex items-center justify-center overflow-hidden cursor-pointer hover:opacity-90 transition-opacity" title="Klik untuk perbesar Halaman 2" onclick={() => { previewImageUrl = selectedSiswiDetail.paper_form_url_2; }}>
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
    </div>
  </div>
{/if}

<!-- IMAGE PREVIEW MODAL -->
{#if previewImageUrl}
  <!-- svelte-ignore a11y_click_events_have_key_events -->
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div class="fixed inset-0 z-[60] flex items-center justify-center p-4 sm:p-6">
    <div class="absolute inset-0 bg-slate-900/90 backdrop-blur-sm transition-opacity" onclick={() => previewImageUrl = null}></div>
    
    <div class="relative max-w-4xl max-h-[90vh] flex flex-col items-center justify-center animate-fade-in w-full h-full">
      <button type="button" onclick={() => previewImageUrl = null} class="absolute top-0 right-0 sm:-top-4 sm:-right-4 bg-white text-slate-800 rounded-full p-2.5 shadow-xl hover:bg-slate-200 transition-colors z-10">
        <X class="w-6 h-6" />
      </button>
      <img src={previewImageUrl} alt="Arsip Kertas Full" class="max-w-full max-h-[85vh] object-contain rounded-xl shadow-2xl" />
    </div>
  </div>
{/if}
