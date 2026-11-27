/**
 * CompRadar Frontend Engine
 * Features: Keyboard Navigation (j/k/s/c/w/o), In-Place Column Sorting,
 * Application Stage CRM, WhatsApp Formatted Sharing, and Real-Time Radar.
 */

const urlParams = new URLSearchParams(window.location.search);

// Per-user private browser storage for Bookmarks & Tracking Stages
function getLocalBookmarks() {
  try {
    return new Set(JSON.parse(localStorage.getItem('compradar_bookmarks') || '[]'));
  } catch {
    return new Set();
  }
}

function saveLocalBookmarks(bmSet) {
  localStorage.setItem('compradar_bookmarks', JSON.stringify(Array.from(bmSet)));
}

function getLocalStages() {
  try {
    return JSON.parse(localStorage.getItem('compradar_stages') || '{}');
  } catch {
    return {};
  }
}

function saveLocalStages(stagesObj) {
  localStorage.setItem('compradar_stages', JSON.stringify(stagesObj));
}

// State (hydrated from URLSearchParams for shareable filter links)
const state = {
  source: urlParams.get('source') || 'all',
  category: urlParams.get('category') || 'all',
  query: urlParams.get('q') || '',
  sort: urlParams.get('sort') || 'deadline',
  location: urlParams.get('location') || 'all',
  savedOnly: urlParams.get('saved') === 'true',
  urgentOnly: urlParams.get('urgent') === 'true',
  highPrizeOnly: urlParams.get('high_prize') === 'true',
  ppoOnly: urlParams.get('ppo') === 'true',
  mba1stOnly: urlParams.get('mba_1st') === 'true',
  viewMode: urlParams.get('view') || localStorage.getItem('compradar_view') || localStorage.getItem('oppscout_view') || 'list', // 'list' | 'grid'
  items: [],
  selectedItem: null,
  focusedIndex: -1,
  isScraping: false
};

function syncUrlFromState() {
  const params = new URLSearchParams();
  if (state.source !== 'all') params.set('source', state.source);
  if (state.category !== 'all') params.set('category', state.category);
  if (state.query) params.set('q', state.query);
  if (state.location !== 'all') params.set('location', state.location);
  if (state.sort !== 'deadline') params.set('sort', state.sort);
  if (state.viewMode !== 'list') params.set('view', state.viewMode);
  if (state.savedOnly) params.set('saved', 'true');
  if (state.urgentOnly) params.set('urgent', 'true');
  if (state.highPrizeOnly) params.set('high_prize', 'true');
  if (state.ppoOnly) params.set('ppo', 'true');
  if (state.mba1stOnly) params.set('mba_1st', 'true');

  const qs = params.toString();
  const nextUrl = qs ? `${window.location.pathname}?${qs}` : window.location.pathname;
  if (window.location.pathname + window.location.search !== nextUrl) {
    history.replaceState(null, '', nextUrl);
  }
}

// DOM References
const searchInput = document.getElementById('searchInput');
const clearSearch = document.getElementById('clearSearch');
const sortSelect = document.getElementById('sortSelect');
const locationSelect = document.getElementById('locationSelect');
const savedFilterBtn = document.getElementById('savedFilterBtn');
const filterBengaluruBtn = document.getElementById('filterBengaluruBtn');
const filterUrgentBtn = document.getElementById('filterUrgentBtn');
const filterHighPrizeBtn = document.getElementById('filterHighPrizeBtn');
const filterPpoBtn = document.getElementById('filterPpoBtn');
const filterMbaBtn = document.getElementById('filterMbaBtn');
const viewListBtn = document.getElementById('viewListBtn');
const viewGridBtn = document.getElementById('viewGridBtn');
const scrapeBtn = document.getElementById('scrapeBtn');
const emptyScrapeBtn = document.getElementById('emptyScrapeBtn');
const scrapeProgress = document.getElementById('scrapeProgress');
const opportunitiesContainer = document.getElementById('opportunitiesContainer');
const emptyState = document.getElementById('emptyState');
const resultsCount = document.getElementById('resultsCount');
const lastScrapedText = document.getElementById('lastScrapedText');
const liveDeadlineTicker = document.getElementById('liveDeadlineTicker');
const toastEl = document.getElementById('toast');

// State tracking for live ticker
state.lastFetchTime = Date.now();

// Stats Elements
const statTotal = document.getElementById('statTotal');
const statHackathons = document.getElementById('statHackathons');
const statCaseStudies = document.getElementById('statCaseStudies');
const statStrategy = document.getElementById('statStrategy');
const statMarketing = document.getElementById('statMarketing');
const statPrizePool = document.getElementById('statPrizePool');
const statBookmarks = document.getElementById('statBookmarks');
const headerLiveStatus = document.getElementById('headerLiveStatus');

// Export Dropdown
const exportBtn = document.getElementById('exportBtn');
const exportMenu = document.getElementById('exportMenu');
const exportCsv = document.getElementById('exportCsv');
const exportJson = document.getElementById('exportJson');

// Modal Elements
const importModal = document.getElementById('importModal');
const importModalBtn = document.getElementById('importModalBtn');
const closeModalBtn = document.getElementById('closeModalBtn');
const cancelModalBtn = document.getElementById('cancelModalBtn');
const submitImportBtn = document.getElementById('submitImportBtn');
const csvFileInput = document.getElementById('csvFileInput');
const csvTextInput = document.getElementById('csvTextInput');
const importAdminToken = document.getElementById('importAdminToken');

// Shortcuts Elements
const shortcutsPillBtn = document.getElementById('shortcutsPillBtn');
const shortcutsModal = document.getElementById('shortcutsModal');
const closeShortcutsBtn = document.getElementById('closeShortcutsBtn');

// Drawer Elements
const detailsDrawer = document.getElementById('detailsDrawer');
const detailsDrawerBackdrop = document.getElementById('detailsDrawerBackdrop');
const closeDrawerBtn = document.getElementById('closeDrawerBtn');
const drawerBadges = document.getElementById('drawerBadges');
const drawerTitle = document.getElementById('drawerTitle');
const drawerOrganizer = document.getElementById('drawerOrganizer');
const drawerDeadline = document.getElementById('drawerDeadline');
const drawerPrize = document.getElementById('drawerPrize');
const drawerLocation = document.getElementById('drawerLocation');
const drawerSource = document.getElementById('drawerSource');
const drawerTags = document.getElementById('drawerTags');
const drawerApplyLink = document.getElementById('drawerApplyLink');
const drawerCopyBtn = document.getElementById('drawerCopyBtn');
const drawerShareBtn = document.getElementById('drawerShareBtn');
const drawerStageControl = document.getElementById('drawerStageControl');

// Initialize on Load
document.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
  applyViewMode(state.viewMode);
  loadStats();
  fetchOpportunities();
  startLiveTickers();
});

// Pointer tracking for tactile card illumination
document.addEventListener('pointermove', (e) => {
  if (state.viewMode !== 'grid') return;
  const card = e.target.closest('.grid-card');
  if (card) {
    const rect = card.getBoundingClientRect();
    card.style.setProperty('--mx', `${e.clientX - rect.left}px`);
    card.style.setProperty('--my', `${e.clientY - rect.top}px`);
  }
}, { passive: true });

function setupEventListeners() {
  // Delegated click handler for opportunitiesContainer (avoids 300+ per-row closures)
  opportunitiesContainer.addEventListener('click', (e) => {
    const sortTh = e.target.closest('.th-sortable');
    if (sortTh) {
      const field = sortTh.dataset.sortField;
      if (field === 'deadline') {
        state.sort = state.sort === 'deadline' ? 'deadline_desc' : 'deadline';
      } else if (field === 'prize') {
        state.sort = state.sort === 'prize' ? 'deadline' : 'prize';
      } else if (field === 'title') {
        state.sort = state.sort === 'title' ? 'deadline' : 'title';
      }
      sortSelect.value = state.sort.startsWith('deadline') ? 'deadline' : state.sort;
      fetchOpportunities();
      return;
    }

    const rowOrCard = e.target.closest('.table-row, .grid-card');
    if (!rowOrCard) return;
    const index = parseInt(rowOrCard.dataset.index, 10);
    const opp = state.items[index];
    if (!opp) return;

    if (e.target.closest('.bookmark-btn')) {
      e.stopPropagation();
      toggleBookmark(opp.id);
      return;
    }

    if (e.target.closest('.share-wa-btn')) {
      e.stopPropagation();
      copyWhatsAppSummary(opp);
      return;
    }

    if (e.target.closest('a[href]')) {
      e.stopPropagation();
      return;
    }

    setFocusRow(index);
    openDrawer(opp);
  });
  // Global Keyboard shortcuts
  document.addEventListener('keydown', (e) => {
    // If typing inside an input or textarea, only allow Escape
    if (['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName)) {
      if (e.key === 'Escape') {
        document.activeElement.blur();
      }
      return;
    }

    // '/' Focus search
    if (e.key === '/') {
      e.preventDefault();
      searchInput.focus();
      return;
    }

    // '?' Toggle shortcuts
    if (e.key === '?') {
      e.preventDefault();
      shortcutsModal.classList.toggle('hidden');
      return;
    }

    // 'Escape' Close drawers / modals
    if (e.key === 'Escape') {
      closeDrawer();
      hideModal();
      shortcutsModal.classList.add('hidden');
      return;
    }

    // Table / Grid Row Navigation (j / k or ArrowDown / ArrowUp)
    if (['j', 'ArrowDown'].includes(e.key)) {
      e.preventDefault();
      moveFocus(1);
      return;
    }
    if (['k', 'ArrowUp'].includes(e.key)) {
      e.preventDefault();
      moveFocus(-1);
      return;
    }

    // If we have an active focused row
    if (state.focusedIndex >= 0 && state.focusedIndex < state.items.length) {
      const current = state.items[state.focusedIndex];

      // 'Enter' or 'Space' -> Open drawer
      if (['Enter', ' '].includes(e.key)) {
        e.preventDefault();
        openDrawer(current);
        return;
      }
      // 's' -> Star / Bookmark
      if (e.key === 's') {
        e.preventDefault();
        toggleBookmark(current.id);
        return;
      }
      // 'c' -> Copy link
      if (e.key === 'c') {
        e.preventDefault();
        copyUrl(current.url);
        return;
      }
      // 'w' -> Copy formatted WhatsApp text
      if (e.key === 'w') {
        e.preventDefault();
        copyWhatsAppSummary(current);
        return;
      }
      // 'o' -> Open link in new tab
      if (e.key === 'o') {
        e.preventDefault();
        window.open(current.url, '_blank');
        return;
      }
    }
  });

  // Search input debounced
  let searchTimer;
  searchInput.addEventListener('input', (e) => {
    state.query = e.target.value.trim();
    if (state.query) {
      clearSearch.classList.remove('hidden');
    } else {
      clearSearch.classList.add('hidden');
    }
    clearTimeout(searchTimer);
    searchTimer = setTimeout(fetchOpportunities, 220);
  });

  clearSearch.addEventListener('click', () => {
    searchInput.value = '';
    state.query = '';
    clearSearch.classList.add('hidden');
    fetchOpportunities();
    searchInput.focus();
  });

  // Sort dropdown
  sortSelect.addEventListener('change', (e) => {
    state.sort = e.target.value;
    fetchOpportunities();
  });

  // Location dropdown & Bengaluru quick-preset sync
  if (locationSelect) {
    locationSelect.value = state.location;
    locationSelect.addEventListener('change', (e) => {
      state.location = e.target.value;
      if (filterBengaluruBtn) {
        filterBengaluruBtn.classList.toggle('active', state.location === 'bengaluru');
      }
      fetchOpportunities();
    });
  }

  if (filterBengaluruBtn) {
    filterBengaluruBtn.classList.toggle('active', state.location === 'bengaluru');
    filterBengaluruBtn.addEventListener('click', () => {
      state.location = state.location === 'bengaluru' ? 'all' : 'bengaluru';
      filterBengaluruBtn.classList.toggle('active', state.location === 'bengaluru');
      if (locationSelect) locationSelect.value = state.location;
      fetchOpportunities();
    });
  }

  // Hydrate initial UI controls from URL state
  if (state.query && searchInput) {
    searchInput.value = state.query;
    if (clearSearch) clearSearch.classList.remove('hidden');
  }
  if (sortSelect) sortSelect.value = state.sort.startsWith('deadline') ? 'deadline' : state.sort;
  document.querySelectorAll('[data-source]').forEach(t => {
    t.classList.toggle('active', t.dataset.source === state.source);
  });
  document.querySelectorAll('[data-category]').forEach(c => {
    c.classList.toggle('active', c.dataset.category === state.category);
  });
  if (savedFilterBtn) savedFilterBtn.classList.toggle('active', state.savedOnly);
  if (filterUrgentBtn) filterUrgentBtn.classList.toggle('active', state.urgentOnly);
  if (filterHighPrizeBtn) filterHighPrizeBtn.classList.toggle('active', state.highPrizeOnly);
  if (filterPpoBtn) filterPpoBtn.classList.toggle('active', state.ppoOnly);
  if (filterMbaBtn) filterMbaBtn.classList.toggle('active', state.mba1stOnly);

  // Source segmented tabs
  document.querySelectorAll('[data-source]').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('[data-source]').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      state.source = tab.dataset.source;
      fetchOpportunities();
    });
  });

  // Category filter chips
  document.querySelectorAll('[data-category]').forEach(chip => {
    chip.addEventListener('click', () => {
      document.querySelectorAll('[data-category]').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      state.category = chip.dataset.category;
      fetchOpportunities();
    });
  });

  // Saved bookmark filter
  savedFilterBtn.addEventListener('click', () => {
    state.savedOnly = !state.savedOnly;
    savedFilterBtn.classList.toggle('active', state.savedOnly);
    fetchOpportunities();
  });

  // Preset Filters
  if (filterUrgentBtn) {
    filterUrgentBtn.addEventListener('click', () => {
      state.urgentOnly = !state.urgentOnly;
      filterUrgentBtn.classList.toggle('active', state.urgentOnly);
      fetchOpportunities();
    });
  }

  if (filterHighPrizeBtn) {
    filterHighPrizeBtn.addEventListener('click', () => {
      state.highPrizeOnly = !state.highPrizeOnly;
      filterHighPrizeBtn.classList.toggle('active', state.highPrizeOnly);
      fetchOpportunities();
    });
  }

  if (filterPpoBtn) {
    filterPpoBtn.addEventListener('click', () => {
      state.ppoOnly = !state.ppoOnly;
      filterPpoBtn.classList.toggle('active', state.ppoOnly);
      fetchOpportunities();
    });
  }

  if (filterMbaBtn) {
    filterMbaBtn.addEventListener('click', () => {
      state.mba1stOnly = !state.mba1stOnly;
      filterMbaBtn.classList.toggle('active', state.mba1stOnly);
      fetchOpportunities();
    });
  }

  // View mode switcher
  viewListBtn.addEventListener('click', () => applyViewMode('list'));
  viewGridBtn.addEventListener('click', () => applyViewMode('grid'));

  // Scrape triggers
  scrapeBtn.addEventListener('click', triggerScrape);
  if (emptyScrapeBtn) emptyScrapeBtn.addEventListener('click', triggerScrape);

  // Export dropdown popover
  exportBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    exportMenu.classList.toggle('hidden');
  });

  document.addEventListener('click', () => {
    exportMenu.classList.add('hidden');
  });

  exportCsv.addEventListener('click', (e) => {
    e.preventDefault();
    downloadExport('csv');
  });

  exportJson.addEventListener('click', (e) => {
    e.preventDefault();
    downloadExport('json');
  });

  // Modal interactions
  if (importModalBtn) {
    importModalBtn.addEventListener('click', () => {
      importModal.classList.remove('hidden');
    });
  }

  const hideModal = () => {
    if (importModal) importModal.classList.add('hidden');
  };

  if (closeModalBtn) closeModalBtn.addEventListener('click', hideModal);
  if (cancelModalBtn) cancelModalBtn.addEventListener('click', hideModal);

  if (csvFileInput) {
    csvFileInput.addEventListener('change', (e) => {
      const file = e.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (event) => {
        csvTextInput.value = event.target.result;
      };
      reader.readAsText(file);
    });
  }

  if (submitImportBtn) {
    submitImportBtn.addEventListener('click', async () => {
      const text = csvTextInput.value.trim();
      if (!text) {
        showToast('Paste CSV content or select a file first.');
        return;
      }
      submitImportBtn.disabled = true;
      submitImportBtn.textContent = 'Ingesting...';
      try {
        const adminToken = importAdminToken ? importAdminToken.value.trim() : '';
        const res = await fetch('/api/import-csv', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(adminToken ? { 'X-Admin-Token': adminToken } : {})
          },
          body: JSON.stringify({ csv_text: text, admin_token: adminToken })
        });
        const data = await res.json();
        if (!res.ok) {
          showToast(data.error || 'Import rejected by server.');
          return;
        }
        showToast(`Ingested ${data.saved_count || 0} competitions!`);
        hideModal();
        csvTextInput.value = '';
        await loadStats();
        await fetchOpportunities();
      } catch (err) {
        console.error('Import error:', err);
        showToast('Error importing CSV data.');
      } finally {
        submitImportBtn.disabled = false;
        submitImportBtn.textContent = 'Ingest & Save Opportunities';
      }
    });
  }

  // Shortcuts Modal
  if (shortcutsPillBtn) {
    shortcutsPillBtn.addEventListener('click', () => {
      shortcutsModal.classList.toggle('hidden');
    });
  }
  if (closeShortcutsBtn) {
    closeShortcutsBtn.addEventListener('click', () => {
      shortcutsModal.classList.add('hidden');
    });
  }

  // Drawer interactions
  if (closeDrawerBtn) closeDrawerBtn.addEventListener('click', closeDrawer);
  if (detailsDrawerBackdrop) detailsDrawerBackdrop.addEventListener('click', closeDrawer);

  // Application Stage buttons in Drawer
  if (drawerStageControl) {
    drawerStageControl.querySelectorAll('.stage-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        if (!state.selectedItem) return;
        const newStage = btn.dataset.stage;
        updateItemStage(state.selectedItem.id, newStage);
      });
    });
  }
}

function applyViewMode(mode) {
  state.viewMode = mode;
  localStorage.setItem('compradar_view', mode);
  syncUrlFromState();

  viewListBtn.classList.toggle('active', mode === 'list');
  viewGridBtn.classList.toggle('active', mode === 'grid');

  opportunitiesContainer.className = mode === 'list' ? 'view-list' : 'view-grid';
  state.focusedIndex = -1;
  renderOpportunities(state.items);
}

// Smooth Number Counter Animation
function animateValue(el, end, duration = 350) {
  if (!el) return;
  const target = parseInt(end, 10);
  if (isNaN(target)) {
    el.textContent = end;
    return;
  }
  const start = parseInt(el.textContent.replace(/[^0-9]/g, ''), 10) || 0;
  if (start === target) {
    el.textContent = target;
    return;
  }
  const startTime = performance.now();
  function step(now) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const ease = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(start + (target - start) * ease);
    if (progress < 1) {
      requestAnimationFrame(step);
    } else {
      el.textContent = target;
    }
  }
  requestAnimationFrame(step);
}

// Fetch stats ribbon with smooth counting
async function loadStats() {
  try {
    const res = await fetch('/api/stats');
    if (!res.ok) return;
    const stats = await res.json();
    animateValue(statTotal, stats.total || 0);
    animateValue(statHackathons, stats.hackathons || 0);
    animateValue(statCaseStudies, stats.case_studies || 0);
    if (statStrategy) animateValue(statStrategy, stats.strategy || 0);
    if (statMarketing) animateValue(statMarketing, stats.marketing || 0);
    if (statPrizePool) statPrizePool.textContent = stats.total_prize_pool || '₹4.2 Cr+';
    animateValue(statBookmarks, getLocalBookmarks().size);
    if (headerLiveStatus) {
      headerLiveStatus.textContent = `${stats.total || 0} Live Listings`;
    }
  } catch (err) {
    console.error('Stats error:', err);
  }
}

// Fetch opportunities with AbortController to cancel stale requests
let fetchAbortController = null;
async function fetchOpportunities() {
  syncUrlFromState();
  if (fetchAbortController) {
    fetchAbortController.abort();
  }
  fetchAbortController = new AbortController();
  opportunitiesContainer.style.opacity = '0.4';

  const params = new URLSearchParams({
    source: state.source,
    category: state.category,
    query: state.query,
    sort: state.sort,
    location: state.location,
    urgent: state.urgentOnly,
    high_prize: state.highPrizeOnly,
    ppo: state.ppoOnly,
    mba_1st: state.mba1stOnly
  });

  try {
    const res = await fetch(`/api/opportunities?${params.toString()}`, {
      signal: fetchAbortController.signal
    });
    const data = await res.json();
    const bmSet = getLocalBookmarks();
    const stageMap = getLocalStages();
    let items = (data.opportunities || []).map(opp => ({
      ...opp,
      is_bookmarked: bmSet.has(opp.id),
      application_status: stageMap[opp.id] || 'None'
    }));
    if (state.savedOnly) {
      items = items.filter(opp => opp.is_bookmarked);
    }
    state.items = items;
    state.focusedIndex = -1;
    state.lastFetchTime = Date.now();
    renderOpportunities(state.items);
    resultsCount.textContent = `Showing ${state.items.length} opportunities`;
    updateLiveTickers();
  } catch (err) {
    if (err.name === 'AbortError') return;
    console.error('Fetch error:', err);
    showToast('Failed to load competitions.');
  } finally {
    opportunitiesContainer.style.opacity = '1';
  }
}

// Live Real-Time Activity and Countdown Tickers (pauses when tab is hidden)
function startLiveTickers() {
  updateLiveTickers();
  setInterval(() => {
    if (!document.hidden) updateLiveTickers();
  }, 1000);
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) updateLiveTickers();
  });
}

function updateLiveTickers() {
  // 1. Elapsed time since last fetch
  if (lastScrapedText && state.lastFetchTime) {
    const sec = Math.floor((Date.now() - state.lastFetchTime) / 1000);
    if (sec < 5) {
      lastScrapedText.textContent = 'Synced just now • Live';
    } else if (sec < 60) {
      lastScrapedText.textContent = `Synced ${sec}s ago • Live`;
    } else {
      const mins = Math.floor(sec / 60);
      lastScrapedText.textContent = `Synced ${mins}m ago • Live`;
    }
  }

  // 2. Real-time countdown for nearest closing deadline
  if (liveDeadlineTicker && state.items && state.items.length > 0) {
    const valid = state.items.filter(x => x.days_left_num !== undefined && x.days_left_num >= 0);
    if (valid.length > 0) {
      const nearest = valid.reduce((min, curr) => curr.days_left_num < min.days_left_num ? curr : min, valid[0]);
      const days = nearest.days_left_num;
      const now = new Date();
      const secondsLeftInDay = 86400 - (now.getHours() * 3600 + now.getMinutes() * 60 + now.getSeconds());
      const hours = Math.floor(secondsLeftInDay / 3600);
      const mins = Math.floor((secondsLeftInDay % 3600) / 60);
      const secs = secondsLeftInDay % 60;
      
      const pad = (n) => String(n).padStart(2, '0');
      const timeStr = `${days}d ${pad(hours)}h ${pad(mins)}m ${pad(secs)}s`;
      const shortTitle = nearest.title.length > 24 ? nearest.title.slice(0, 22) + '...' : nearest.title;
      liveDeadlineTicker.textContent = `Next Closing: ${shortTitle} in ${timeStr}`;
    } else {
      liveDeadlineTicker.textContent = 'All listings current & monitored';
    }
  }
}

// Render Table vs Grid
function renderOpportunities(items) {
  opportunitiesContainer.innerHTML = '';

  if (items.length === 0) {
    emptyState.classList.remove('hidden');
    return;
  }
  emptyState.classList.add('hidden');

  if (state.viewMode === 'list') {
    renderListView(items);
  } else {
    renderGridView(items);
  }
}

// High-Density Data Table View with DocumentFragment batching
function renderListView(items) {
  const fragment = document.createDocumentFragment();
  const header = document.createElement('div');
  header.className = 'list-table-header';

  const deadlineSortArrow = state.sort === 'deadline' ? ' &uarr;' : (state.sort === 'deadline_desc' ? ' &darr;' : '');
  const prizeSortArrow = state.sort === 'prize' ? ' &uarr;' : '';
  const titleSortArrow = state.sort === 'title' ? ' &uarr;' : '';

  header.innerHTML = `
    <span class="th-sortable ${state.sort === 'title' ? 'active-sort' : ''}" data-sort-field="title">
      Opportunity / Host ${titleSortArrow}
    </span>
    <span>Track</span>
    <span>Source</span>
    <span class="th-sortable ${state.sort.startsWith('deadline') ? 'active-sort' : ''}" data-sort-field="deadline">
      Deadline ${deadlineSortArrow}
    </span>
    <span class="th-sortable ${state.sort === 'prize' ? 'active-sort' : ''}" data-sort-field="prize">
      Reward ${prizeSortArrow}
    </span>
    <span style="text-align: right;">Action</span>
  `;

  fragment.appendChild(header);

  items.forEach((opp, index) => {
    const row = document.createElement('div');
    row.className = 'table-row';
    row.dataset.index = index;
    row.style.setProperty('--i', Math.min(index, 20));

    const isUrgent = opp.days_left_num !== undefined && opp.days_left_num >= 0 && opp.days_left_num <= 3;
    const isBookmarked = !!opp.is_bookmarked;
    const trackBadgeHtml = getTrackBadgeHtml(opp.category);
    const sourceHtml = getSourceBadge(opp.source);
    const deadlineHtml = getDeadlineBadge(opp);
    const rewardHtml = getRewardBadge(opp.prize);
    const stageTagHtml = getStageTagHtml(opp.application_status);
    const avatarHtml = getOrganizerAvatarHtml(opp.organizer, opp.category);

    row.innerHTML = `
      <div class="col-primary">
        ${avatarHtml}
        <div class="primary-text-wrap">
          <div class="row-title" title="${escapeHtml(opp.title)}">
            ${escapeHtml(opp.title)}
            ${stageTagHtml}
          </div>
          <div class="row-org">
            <span class="status-dot ${isUrgent ? 'urgent' : 'normal'}"></span>
            <span>${escapeHtml(opp.organizer)} &bull; ${escapeHtml(opp.location || 'Online')}</span>
          </div>
        </div>
      </div>
      <div class="col-meta-cell">
        ${trackBadgeHtml}
      </div>
      <div class="col-meta-cell">
        ${sourceHtml}
      </div>
      <div class="countdown-cell col-meta-cell">
        ${deadlineHtml}
      </div>
      <div class="reward-cell col-meta-cell">
        ${rewardHtml}
      </div>
      <div class="row-actions">
        <button class="btn-icon-subtle bookmark-btn ${isBookmarked ? 'bookmarked' : ''}" title="${isBookmarked ? 'Saved (Press s)' : 'Save (Press s)'}">
          ${isBookmarked ? '★' : '☆'}
        </button>
        <button class="btn-icon-subtle share-wa-btn" title="Copy for WhatsApp (Press w)">
          💬
        </button>
        <a href="${opp.url}" target="_blank" rel="noopener noreferrer" class="btn-icon-subtle" title="Open Page ↗ (Press o)">
          ↗
        </a>
      </div>
    `;

    fragment.appendChild(row);
  });

  opportunitiesContainer.appendChild(fragment);
}

// Precision Grid View with DocumentFragment batching
function renderGridView(items) {
  const fragment = document.createDocumentFragment();

  items.forEach((opp, index) => {
    const card = document.createElement('div');
    card.className = 'grid-card';
    card.dataset.index = index;
    card.style.setProperty('--i', Math.min(index, 20));

    const isUrgent = opp.days_left_num !== undefined && opp.days_left_num >= 0 && opp.days_left_num <= 3;
    const isBookmarked = !!opp.is_bookmarked;
    const sourceHtml = getSourceBadge(opp.source);
    const deadlineHtml = getDeadlineBadge(opp);
    const rewardHtml = getRewardBadge(opp.prize);
    const stageTagHtml = getStageTagHtml(opp.application_status);
    const trackBadgeHtml = getTrackBadgeHtml(opp.category);
    const avatarHtml = getOrganizerAvatarHtml(opp.organizer, opp.category);

    const tagsHtml = (opp.tags || [])
      .slice(0, 3)
      .map(t => `<span class="pill-track track-default">${escapeHtml(t)}</span>`)
      .join('');

    card.innerHTML = `
      <div>
        <div class="card-top-meta">
          <div class="card-header-cluster">
            ${avatarHtml}
            <div style="display: flex; align-items: center; gap: 0.4rem;">
              ${sourceHtml}
              ${stageTagHtml}
            </div>
          </div>
          <button class="btn-icon-subtle bookmark-btn ${isBookmarked ? 'bookmarked' : ''}" title="${isBookmarked ? 'Saved' : 'Save'}">
            ${isBookmarked ? '★' : '☆'}
          </button>
        </div>

        <h3 class="card-title-text" title="${escapeHtml(opp.title)}">${escapeHtml(opp.title)}</h3>
        <p class="card-org-text">
          <span class="status-dot ${isUrgent ? 'urgent' : 'normal'}"></span>
          <span>${escapeHtml(opp.organizer)} &bull; ${escapeHtml(opp.location || 'Online')}</span>
        </p>

        <div style="margin-bottom: 0.85rem;">
          ${trackBadgeHtml}
        </div>

        <div class="card-data-strip">
          <div>
            <div class="data-box-label">Deadline</div>
            <div class="data-box-val">${deadlineHtml}</div>
          </div>
          <div>
            <div class="data-box-label">Reward</div>
            <div class="data-box-val">${rewardHtml}</div>
          </div>
        </div>

        <div class="card-tags-cloud">
          ${tagsHtml}
        </div>
      </div>

      <div class="card-footer-strip">
        <button class="btn-icon-subtle share-wa-btn" title="Copy for WhatsApp">
          💬
        </button>
        <a href="${opp.url}" target="_blank" rel="noopener noreferrer" class="apply-button-direct">
          Open Official Portal ↗
        </a>
      </div>
    `;

    fragment.appendChild(card);
  });

  opportunitiesContainer.appendChild(fragment);
}

// Visual helpers for Ultra-Elevated Design
function getTrackClass(category) {
  const c = (category || '').toLowerCase();
  if (c.includes('strategy') || c.includes('consulting')) return 'track-strategy';
  if (c.includes('marketing') || c.includes('brand')) return 'track-marketing';
  if (c.includes('hackathon') || c.includes('code')) return 'track-tech';
  if (c.includes('case')) return 'track-case';
  if (c.includes('operation') || c.includes('supply')) return 'track-ops';
  return 'track-default';
}

function getTrackBadgeHtml(category) {
  const cls = getTrackClass(category);
  let iconSvg = '';
  if (cls === 'track-strategy') {
    iconSvg = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>`;
  } else if (cls === 'track-marketing') {
    iconSvg = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>`;
  } else if (cls === 'track-tech') {
    iconSvg = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>`;
  } else if (cls === 'track-case') {
    iconSvg = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>`;
  } else if (cls === 'track-ops') {
    iconSvg = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>`;
  }
  return `<span class="pill-track">${iconSvg}${escapeHtml(category)}</span>`;
}

function getOrganizerAvatarHtml(organizer, category) {
  const org = (organizer || 'Opp').trim();
  let mono = '';
  const upper = org.toUpperCase();

  if (upper.includes('IIM BANGALORE') || upper.includes('IIMB')) mono = 'IIMB';
  else if (upper.includes('IIM AHMEDABAD') || upper.includes('IIMA')) mono = 'IIMA';
  else if (upper.includes('IIM CALCUTTA') || upper.includes('IIMC')) mono = 'IIMC';
  else if (upper.includes('XLRI')) mono = 'XLRI';
  else if (upper.includes('FMS')) mono = 'FMS';
  else if (upper.includes('IIT')) mono = 'IIT';
  else if (upper.includes('DEVPOST')) mono = 'DEV';
  else if (upper.includes('UNSTOP')) mono = 'UNS';
  else if (upper.includes('MICROSOFT')) mono = 'MSFT';
  else if (upper.includes('GOOGLE')) mono = 'GOOG';
  else {
    const parts = org.split(/\s+/).filter(Boolean);
    if (parts.length >= 2) {
      mono = (parts[0][0] + parts[1][0]).toUpperCase();
    } else {
      mono = org.slice(0, 3).toUpperCase();
    }
  }

  return `<div class="org-avatar">${escapeHtml(mono)}</div>`;
}

function getDeadlineBadge(opp) {
  const d = opp.days_left_num;
  const label = opp.days_left || opp.deadline || 'Ongoing';

  if (d !== undefined && d >= 0 && d <= 3) {
    return `<span class="deadline-pill urgent"><span class="status-dot-sm urgent"></span>${escapeHtml(label)}</span>`;
  }
  if (d !== undefined && d >= 0 && d <= 7) {
    return `<span class="deadline-pill warning"><span class="status-dot-sm warning"></span>${escapeHtml(label)}</span>`;
  }
  return `<span class="deadline-pill standard">${escapeHtml(label)}</span>`;
}

function getRewardBadge(prize) {
  const p = prize || 'Awards & Certificates';
  const isCash = p.includes('₹') || p.includes('$') || p.toLowerCase().includes('lakh') || p.toLowerCase().includes('crore');
  if (isCash) {
    return `<span class="reward-tag cash" title="${escapeHtml(p)}">${escapeHtml(p)}</span>`;
  }
  return `<span class="reward-tag normal" title="${escapeHtml(p)}">${escapeHtml(p)}</span>`;
}

function getSourceBadge(source) {
  const s = (source || '').toLowerCase();
  let label = source;
  if (s.includes('unstop')) label = 'Unstop';
  else if (s.includes('devpost')) label = 'Devpost';
  else if (s.includes('curated')) label = 'Curated Feed';
  return `<span class="src-pill"><span class="src-dot"></span>${escapeHtml(label)}</span>`;
}

// Stage tag helper
function getStageTagHtml(status) {
  if (!status || status === 'None') return '';
  const clean = status.toLowerCase();
  return `<span class="stage-tag ${clean}">${escapeHtml(status)}</span>`;
}

// Keyboard navigation row focus
function moveFocus(delta) {
  if (state.items.length === 0) return;
  let newIdx = state.focusedIndex + delta;
  if (newIdx < 0) newIdx = 0;
  if (newIdx >= state.items.length) newIdx = state.items.length - 1;
  setFocusRow(newIdx);
}

function setFocusRow(index) {
  state.focusedIndex = index;
  const elements = opportunitiesContainer.querySelectorAll('.table-row, .grid-card');
  elements.forEach((el, idx) => {
    if (idx === index) {
      el.classList.add('kb-focused');
      el.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    } else {
      el.classList.remove('kb-focused');
    }
  });
}

// Helper: Source class
function getSourceClass(source) {
  const s = (source || '').toLowerCase();
  if (s.includes('unstop')) return 'unstop';
  if (s.includes('devpost')) return 'devpost';
  if (s.includes('curated')) return 'curated';
  return '';
}

// Open Details Drawer
function openDrawer(opp) {
  state.selectedItem = opp;

  drawerTitle.textContent = opp.title;
  drawerOrganizer.textContent = `${opp.organizer} (${opp.location || 'Online'})`;
  drawerDeadline.textContent = `${opp.days_left || 'Ongoing'} (${opp.deadline || 'No date specified'})`;
  drawerPrize.textContent = opp.prize || 'Awards & Certificates';
  drawerLocation.textContent = opp.location || 'Online National';
  drawerSource.textContent = opp.source;
  drawerApplyLink.href = opp.url;

  const drawerAvatar = document.getElementById('drawerAvatarContainer');
  if (drawerAvatar) {
    drawerAvatar.innerHTML = getOrganizerAvatarHtml(opp.organizer, opp.category);
  }

  drawerBadges.innerHTML = `
    ${getTrackBadgeHtml(opp.category)}
    ${getSourceBadge(opp.source)}
  `;

  drawerTags.innerHTML = (opp.tags || [])
    .map(t => `<span class="pill-track track-default">${escapeHtml(t)}</span>`)
    .join('');

  // Set active stage in drawer
  const curStage = opp.application_status || 'None';
  drawerStageControl.querySelectorAll('.stage-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.stage === curStage);
  });

  drawerCopyBtn.onclick = () => copyUrl(opp.url);
  drawerShareBtn.onclick = () => copyWhatsAppSummary(opp);

  detailsDrawerBackdrop.classList.remove('hidden');
  detailsDrawer.classList.remove('hidden');
}

function closeDrawer() {
  detailsDrawerBackdrop.classList.add('hidden');
  detailsDrawer.classList.add('hidden');
  state.selectedItem = null;
}

// Application Stage update (stored privately per user in localStorage)
function updateItemStage(id, newStage) {
  const stageMap = getLocalStages();
  if (!newStage || newStage === 'None') {
    delete stageMap[id];
  } else {
    stageMap[id] = newStage;
  }
  saveLocalStages(stageMap);

  const savedStage = stageMap[id] || 'None';
  const item = state.items.find(x => x.id === id);
  if (item) {
    item.application_status = savedStage;
  }
  if (state.selectedItem && state.selectedItem.id === id) {
    state.selectedItem.application_status = savedStage;
    drawerStageControl.querySelectorAll('.stage-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.stage === savedStage);
    });
  }
  renderOpportunities(state.items);
  if (state.focusedIndex >= 0) setFocusRow(state.focusedIndex);
  showToast(`Stage updated to: ${savedStage}`);
}

// Pre-filled WhatsApp Team Pitch
function copyWhatsAppSummary(opp) {
  openWhatsAppPitch(opp);
}

function openWhatsAppPitch(opp) {
  const text = `🔥 *Team Up for ${opp.title}!*
🏛 *Host:* ${opp.organizer} (${opp.location || 'Online'})
💰 *Prize Pool:* ${opp.prize || 'Awards & Certificates'}
⏳ *Deadline:* ${opp.days_left || opp.deadline || 'Ongoing'}
📁 *Track:* ${opp.category}

👉 *Details & Registration:* ${opp.url}

_Found via CompRadar_`;

  if (navigator.clipboard) {
    navigator.clipboard.writeText(text).catch(() => {});
  }
  const waUrl = `https://api.whatsapp.com/send?text=${encodeURIComponent(text)}`;
  window.open(waUrl, '_blank');
  showToast('Opening WhatsApp & copied pitch to clipboard!');
}

function copyUrl(url) {
  navigator.clipboard.writeText(url).then(() => {
    showToast('Link copied to clipboard!');
  });
}

// Trigger Live Scrape
async function triggerScrape() {
  if (state.isScraping) return;
  state.isScraping = true;
  scrapeBtn.disabled = true;
  scrapeProgress.classList.remove('hidden');

  try {
    const payload = {
      category: state.category,
      query: state.query || undefined,
      limit: 30
    };

    const res = await fetch('/api/scrape', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    showToast(`Aggregated ${data.scraped_count || 0} competitions!`);
    await loadStats();
    await fetchOpportunities();
  } catch (err) {
    console.error('Scrape error:', err);
    showToast('Error syncing scrapers. Check terminal.');
  } finally {
    state.isScraping = false;
    scrapeBtn.disabled = false;
    scrapeProgress.classList.add('hidden');
  }
}

// Toggle Bookmark (stored privately per user in localStorage)
function toggleBookmark(id) {
  const bmSet = getLocalBookmarks();
  let isSaved;
  if (bmSet.has(id)) {
    bmSet.delete(id);
    isSaved = false;
  } else {
    bmSet.add(id);
    isSaved = true;
  }
  saveLocalBookmarks(bmSet);

  const item = state.items.find(x => x.id === id);
  if (item) item.is_bookmarked = isSaved;

  animateValue(statBookmarks, bmSet.size);
  showToast(isSaved ? '★ Saved to bookmarks (Press s)' : '☆ Removed from bookmarks');

  if (state.savedOnly) {
    fetchOpportunities();
  } else {
    renderOpportunities(state.items);
    if (state.focusedIndex >= 0) setFocusRow(state.focusedIndex);
  }
}

// Export Downloader
function downloadExport(format) {
  const params = new URLSearchParams({
    format,
    source: state.source,
    category: state.category,
    query: state.query,
    location: state.location,
    bookmarked: state.savedOnly,
    urgent: state.urgentOnly,
    high_prize: state.highPrizeOnly,
    ppo: state.ppoOnly,
    mba_1st: state.mba1stOnly
  });
  window.location.href = `/api/export?${params.toString()}`;
  showToast(`Exporting data as ${format.toUpperCase()}...`);
}

// Toast
let toastTimer;
function showToast(msg) {
  toastEl.textContent = msg;
  toastEl.classList.remove('hidden');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toastEl.classList.add('hidden');
  }, 2300);
}

// Register Service Worker for PWA Offline Support
// Theme Management (System auto-detection + Manual Light/Dark override)
const themeToggleBtn = document.getElementById('themeToggleBtn');
const themeIconSvg = document.getElementById('themeIconSvg');
const themeColorMeta = document.getElementById('themeColorMeta');
const systemThemeMq = window.matchMedia ? window.matchMedia('(prefers-color-scheme: light)') : null;

function getEffectiveTheme(pref) {
  if (pref === 'light' || pref === 'dark') return pref;
  return systemThemeMq && systemThemeMq.matches ? 'light' : 'dark';
}

function applyTheme(pref, announce = false) {
  const validPref = ['system', 'light', 'dark'].includes(pref) ? pref : 'system';
  localStorage.setItem('compradar_theme', validPref);
  const effective = getEffectiveTheme(validPref);

  document.documentElement.setAttribute('data-theme', effective);
  document.body.classList.toggle('theme-light', effective === 'light');
  document.body.classList.toggle('theme-dark', effective === 'dark');
  if (themeColorMeta) {
    themeColorMeta.setAttribute('content', effective === 'light' ? '#f7f7f8' : '#08080a');
  }

  if (themeIconSvg) {
    if (validPref === 'light') {
      themeIconSvg.innerHTML = '<circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>';
    } else if (validPref === 'dark') {
      themeIconSvg.innerHTML = '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>';
    } else {
      themeIconSvg.innerHTML = '<rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line>';
    }
  }

  if (themeToggleBtn) {
    const label = validPref === 'system' ? `System (${effective})` : validPref.charAt(0).toUpperCase() + validPref.slice(1);
    themeToggleBtn.title = `Theme: ${label} — Click to switch`;
  }

  if (announce) {
    const msg = validPref === 'system' ? `Theme: System (${effective})` : `Theme: ${validPref.charAt(0).toUpperCase() + validPref.slice(1)}`;
    showToast(msg);
  }
}

if (themeToggleBtn) {
  themeToggleBtn.addEventListener('click', () => {
    const cur = localStorage.getItem('compradar_theme') || 'system';
    const next = cur === 'system' ? 'light' : (cur === 'light' ? 'dark' : 'system');
    applyTheme(next, true);
  });
}

if (systemThemeMq) {
  systemThemeMq.addEventListener('change', () => {
    const cur = localStorage.getItem('compradar_theme') || 'system';
    if (cur === 'system') applyTheme('system', false);
  });
}

applyTheme(localStorage.getItem('compradar_theme') || 'system', false);

// Register Service Worker & 1-Tap PWA Install Prompt
let deferredInstallPrompt = null;
const installAppBtn = document.getElementById('installAppBtn');

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredInstallPrompt = e;
  if (installAppBtn) {
    installAppBtn.style.display = 'inline-flex';
    installAppBtn.classList.remove('hidden');
  }
});

if (installAppBtn) {
  installAppBtn.addEventListener('click', async () => {
    if (!deferredInstallPrompt) return;
    deferredInstallPrompt.prompt();
    const { outcome } = await deferredInstallPrompt.userChoice;
    deferredInstallPrompt = null;
    installAppBtn.style.display = 'none';
    if (outcome === 'accepted') {
      showToast('Installing CompRadar App...');
    }
  });
}

window.addEventListener('appinstalled', () => {
  deferredInstallPrompt = null;
  if (installAppBtn) installAppBtn.style.display = 'none';
});

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then((reg) => console.log('[CompRadar PWA] Service worker registered, scope:', reg.scope))
      .catch((err) => console.log('[CompRadar PWA] SW registration notice:', err));
  });
}

// HTML Escaper
function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}
