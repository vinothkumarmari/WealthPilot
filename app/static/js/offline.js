/**
 * MyWealthPilot Offline Queue — IndexedDB + Background Sync
 * Stores expenses/income entries when offline, syncs when back online.
 */

const DB_NAME = 'mywealthpilot_offline';
const DB_VERSION = 1;
const STORE_NAME = 'pending_entries';

// ======================== IndexedDB Helpers ========================

function openDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, DB_VERSION);
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            if (!db.objectStoreNames.contains(STORE_NAME)) {
                const store = db.createObjectStore(STORE_NAME, { keyPath: 'id', autoIncrement: true });
                store.createIndex('type', 'type', { unique: false });
                store.createIndex('created', 'created', { unique: false });
            }
        };
    });
}

async function addPendingEntry(entry) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_NAME, 'readwrite');
        const store = tx.objectStore(STORE_NAME);
        entry.created = new Date().toISOString();
        entry.synced = false;
        const request = store.add(entry);
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

async function getPendingEntries() {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_NAME, 'readonly');
        const store = tx.objectStore(STORE_NAME);
        const request = store.getAll();
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

async function deletePendingEntry(id) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_NAME, 'readwrite');
        const store = tx.objectStore(STORE_NAME);
        const request = store.delete(id);
        request.onsuccess = () => resolve();
        request.onerror = () => reject(request.error);
    });
}

async function getPendingCount() {
    const entries = await getPendingEntries();
    return entries.length;
}

// ======================== Sync Logic ========================

async function syncPendingEntries() {
    const entries = await getPendingEntries();
    if (entries.length === 0) return { synced: 0, failed: 0 };

    let synced = 0, failed = 0;
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;

    for (const entry of entries) {
        try {
            const url = entry.type === 'expense' ? '/add-expense' : '/add-income';
            const formData = new FormData();
            formData.append('csrf_token', csrfToken);

            if (entry.type === 'expense') {
                formData.append('category', entry.category);
                formData.append('amount', entry.amount);
                formData.append('date', entry.date);
                formData.append('description', entry.description || '');
                if (entry.is_recurring) formData.append('is_recurring', 'on');
            } else {
                formData.append('source', entry.source);
                formData.append('income_type', entry.income_type);
                formData.append('amount', entry.amount);
                formData.append('date', entry.date);
                formData.append('frequency', entry.frequency || 'one-time');
                formData.append('description', entry.description || '');
            }

            const response = await fetch(url, {
                method: 'POST',
                body: formData,
                redirect: 'follow'
            });

            if (response.ok || response.redirected) {
                await deletePendingEntry(entry.id);
                synced++;
            } else {
                failed++;
            }
        } catch (err) {
            failed++;
        }
    }

    return { synced, failed };
}

// ======================== Online/Offline Detection ========================

function updateOfflineBanner() {
    let banner = document.getElementById('offlineBanner');
    if (!navigator.onLine) {
        if (!banner) {
            banner = document.createElement('div');
            banner.id = 'offlineBanner';
            banner.style.cssText = 'position:fixed;bottom:0;left:0;right:0;z-index:9999;padding:10px 16px;background:linear-gradient(135deg,#FF6B6B,#EE5A24);color:#fff;text-align:center;font-size:14px;font-weight:600;display:flex;align-items:center;justify-content:center;gap:8px;';
            banner.innerHTML = '<span class="material-icons-outlined" style="font-size:20px;">cloud_off</span> You are offline. Expenses will be saved locally and synced when online.';
            document.body.appendChild(banner);
        }
    } else if (banner) {
        banner.remove();
    }
}

async function showPendingBadge() {
    try {
        const count = await getPendingCount();
        let badge = document.getElementById('pendingSyncBadge');
        if (count > 0) {
            if (!badge) {
                badge = document.createElement('div');
                badge.id = 'pendingSyncBadge';
                badge.style.cssText = 'position:fixed;bottom:60px;right:20px;z-index:9998;background:var(--accent,#6C5CE7);color:#fff;padding:8px 16px;border-radius:12px;font-size:13px;font-weight:600;cursor:pointer;box-shadow:0 4px 12px rgba(0,0,0,0.2);display:flex;align-items:center;gap:6px;';
                badge.onclick = async () => {
                    badge.innerHTML = '<span class="material-icons-outlined" style="font-size:18px;animation:spin 1s linear infinite;">sync</span> Syncing...';
                    const result = await syncPendingEntries();
                    if (result.synced > 0) {
                        badge.innerHTML = '<span class="material-icons-outlined" style="font-size:18px;">check_circle</span> ' + result.synced + ' synced!';
                        badge.style.background = '#4CAF50';
                        setTimeout(() => { badge.remove(); location.reload(); }, 1500);
                    } else {
                        badge.innerHTML = '<span class="material-icons-outlined" style="font-size:18px;">error</span> Sync failed. Tap to retry.';
                        badge.style.background = '#f44336';
                    }
                };
                document.body.appendChild(badge);
            }
            badge.innerHTML = '<span class="material-icons-outlined" style="font-size:18px;">sync_problem</span> ' + count + ' pending — tap to sync';
        } else if (badge) {
            badge.remove();
        }
    } catch (e) { /* IndexedDB not available */ }
}

// ======================== Offline Expense Save ========================

async function saveExpenseOffline(data) {
    const entry = {
        type: 'expense',
        category: data.category,
        amount: data.amount,
        date: data.date || new Date().toISOString().split('T')[0],
        description: data.description || 'Added offline',
        is_recurring: data.is_recurring || false
    };
    await addPendingEntry(entry);
    showPendingBadge();
    return true;
}

// ======================== Init ========================

window.addEventListener('online', () => {
    updateOfflineBanner();
    // Auto-sync when back online
    syncPendingEntries().then(result => {
        if (result.synced > 0) {
            showPendingBadge();
            // Show toast
            const toast = document.createElement('div');
            toast.style.cssText = 'position:fixed;top:80px;right:20px;z-index:9999;background:#4CAF50;color:#fff;padding:12px 20px;border-radius:12px;font-size:14px;font-weight:500;box-shadow:0 4px 12px rgba(0,0,0,0.2);display:flex;align-items:center;gap:8px;';
            toast.innerHTML = '<span class="material-icons-outlined">check_circle</span> ' + result.synced + ' offline entries synced!';
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 4000);
        }
    });
});
window.addEventListener('offline', updateOfflineBanner);

// Check on page load
document.addEventListener('DOMContentLoaded', () => {
    updateOfflineBanner();
    showPendingBadge();
});
