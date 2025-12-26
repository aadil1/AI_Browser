/**
 * SafeBrowse Dashboard JavaScript
 */

// Configuration
const isDev = window.location.port === '8001';
let CONFIG = {
    backendUrl: isDev ? 'http://localhost:8000' : '',
    apiKey: ''
};

// --- Initialization ---

document.addEventListener('DOMContentLoaded', async () => {
    // Initialize
    loadConfig();
    setupNavigation();

    // Initial Data Load
    await checkBackendStatus();

    if (CONFIG.apiKey && CONFIG.apiKey !== 'test-key') {
        loadSectionData('overview');
        loadStats();
        loadRecentActivity();
    } else {
        // Show login if needed, or just load overview
        if (!CONFIG.apiKey) showLoginModal();
        loadSectionData('overview');
    }

    // Setup Event Listeners
    if (filterSelect) {
        filterSelect.addEventListener('change', loadAuditLogs);
    }

    // Connect "Generate New Key" button to form
    const jumpToKeyBtn = document.getElementById('generate-key-btn');
    if (jumpToKeyBtn) {
        jumpToKeyBtn.addEventListener('click', () => {
            const input = document.getElementById('key-name');
            if (input) {
                input.scrollIntoView({ behavior: 'smooth', block: 'center' });
                input.focus();
            }
        });
    }
});

// --- Core Functions ---

function loadConfig() {
    const saved = localStorage.getItem('safebrowse-dashboard-config');
    if (saved) {
        CONFIG = { ...CONFIG, ...JSON.parse(saved) };
    }
    const urlInput = document.getElementById('backend-url');
    const keyInput = document.getElementById('dashboard-api-key');
    if (urlInput) urlInput.value = CONFIG.backendUrl;
    if (keyInput) keyInput.value = CONFIG.apiKey;
}

async function saveSettings() {
    const urlInput = document.getElementById('backend-url');
    const keyInput = document.getElementById('dashboard-api-key');
    const saveBtn = document.getElementById('save-config');

    let newUrl = urlInput.value.trim().replace(/\/$/, '');
    if (!newUrl) newUrl = window.location.origin;

    const newKey = keyInput.value.trim();

    const originalText = saveBtn.innerText || 'Save';
    saveBtn.innerText = 'Testing Connection...';
    saveBtn.disabled = true;

    try {
        console.log(`Testing connection to ${newUrl}...`);
        const response = await fetch(`${newUrl}/health`, {
            headers: { 'Content-Type': 'application/json' }
        });

        if (!response.ok) throw new Error(`Backend returned ${response.status}`);

        CONFIG.backendUrl = newUrl;
        CONFIG.apiKey = newKey;

        localStorage.setItem('safebrowse-dashboard-config', JSON.stringify(CONFIG));
        alert('Connection Verified & Saved!');
        location.reload();

    } catch (error) {
        console.error(error);
        alert(`Connection Failed: ${error.message}\n\nSettings were NOT saved.`);
    } finally {
        saveBtn.innerText = originalText;
        saveBtn.disabled = false;
    }
}

async function apiCall(endpoint, options = {}) {
    const url = `${CONFIG.backendUrl}${endpoint}`;
    const headers = {
        'Content-Type': 'application/json',
        'X-API-Key': CONFIG.apiKey,
        ...options.headers
    };

    try {
        const response = await fetch(url, { ...options, headers });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();

            // Switch Active Tab
            navItems.forEach(n => n.classList.remove('active'));
            item.classList.add('active');

            // Switch Section Content
            const sectionId = item.dataset.section;
            document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
            const targetSection = document.getElementById(`section-${sectionId}`);
            if (targetSection) targetSection.classList.add('active');

            // Update Title
            const titleEl = document.getElementById('page-title');
            if (titleEl) titleEl.textContent = item.textContent.trim();

            // Load Data
            loadSectionData(sectionId);
        });
    });
}

function loadSectionData(section) {
    console.log('Loading section:', section);
    switch (section) {
        case 'overview':
            loadStats();
            loadRecentActivity();
            break;
        case 'audit':
            loadAuditLogs();
            break;
        case 'api-keys':
            loadApiKeys();
            loadOrgStatus();
            break;
        case 'settings':
            loadCapabilities();
            break;
    }
}

async function checkBackendStatus() {
    const indicator = document.querySelector('.status-indicator');
    if (!indicator) return;
    try {
        await apiCall('/health');
        indicator.className = 'status-indicator online';
        indicator.innerHTML = '● Backend Online';
    } catch (error) {
        indicator.className = 'status-indicator';
        indicator.innerHTML = '○ Backend Offline';
    }
}

async function loadStats() {
    try {
        const stats = await apiCall('/audit/stats?hours=24');
        const set = (id, val) => {
            const el = document.getElementById(id);
            if (el) el.textContent = val;
        };
        set('total-requests', stats.total_requests || 0);
        set('blocked-requests', stats.blocked_requests || 0);
        set('allowed-requests', stats.allowed_requests || 0);
        set('block-rate', `${stats.block_rate || 0}%`);
    } catch (error) {
        console.error('Failed to load stats:', error);
        if (error.message.includes('403')) {
            const grid = document.querySelector('.stats-grid');
            if (grid) {
                grid.innerHTML = `
                  <div class="upgrade-banner" style="grid-column: 1 / -1; background: #f8f9fa; padding: 32px; text-align: center; border-radius: 8px; border: 1px dashed #ccc;">
                      <h3 style="margin: 0 0 8px 0; font-size: 18px;">📊 Unlock Analytics</h3>
                      <p style="margin: 0 0 16px 0; color: #666; font-size: 14px;">Detailed statistics are available on the Pro plan.</p>
                      <a href="https://forms.gle/vGtps8qX4PeXJqn9A" target="_blank" class="btn btn-primary" style="display: inline-block;">Upgrade Now</a>
                  </div>
              `;
            }
        }
    }
}

async function loadRecentActivity() {
    try {
        const data = await apiCall('/audit/logs?limit=5');
        const tbody = document.querySelector('#recent-activity tbody');
        if (!tbody) return;

        if (!data.logs || data.logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="loading">No recent activity</td></tr>';
            return;
        }

        tbody.innerHTML = data.logs.map(log => `
            <tr>
                <td>${formatTime(log.timestamp)}</td>
                <td>${truncateUrl(log.url)}</td>
                <td><span class="badge ${log.status === 'ok' ? 'badge-success' : 'badge-danger'}">${log.status === 'ok' ? 'Allowed' : 'Blocked'}</span></td>
                <td>${(log.risk_score * 100).toFixed(0)}%</td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Failed to load activity:', error);
        const tbody = document.querySelector('#recent-activity tbody');
        if (tbody && error.message.includes('403')) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; padding: 20px; color: #666; font-size: 13px;">🔒 Upgrade to Pro to view activity</td></tr>';
        }
    }
}

async function loadApiKeys() {
    try {
        const keys = await apiCall('/auth/keys');
        const list = document.getElementById('api-keys-list');
        if (!list) return;

        if (!keys || keys.length === 0) {
            list.innerHTML = '<div class="empty-state">No API keys found. Generate one above.</div>';
            return;
        }

        list.innerHTML = keys.map(key => `
            <div class="api-key-item">
                <div class="key-info">
                    <span class="key-name">${key.label}</span>
                    <code class="key-value">${key.prefix}</code>
                    <span class="key-active-status ${key.is_active ? 'active' : 'inactive'}">● Active</span>
                </div>
                <div class="key-meta" style="font-size: 12px; color: var(--text-muted);">
                    Created: ${new Date(key.created_at).toLocaleDateString()}
                    ${key.last_used_at ? `| Last used: ${new Date(key.last_used_at).toLocaleDateString()}` : ''}
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Failed to load keys:', error);
        const list = document.getElementById('api-keys-list');
        if (list) list.innerHTML = '<div class="error-state">Failed to load API keys</div>';
    }
}

async function loadOrgStatus() {
    try {
        const status = await apiCall('/org/status');

        // Update Tier
        const tierEl = document.getElementById('plan-tier');
        if (tierEl) tierEl.textContent = status.tier;

        // Update Usage
        const usageText = document.getElementById('usage-text');
        if (usageText) usageText.textContent = `${status.requests_today} / ${status.daily_limit}`;

        // Update Bar
        const usageBar = document.getElementById('usage-bar');
        if (usageBar) {
            const pct = Math.min((status.requests_today / status.daily_limit) * 100, 100);
            usageBar.style.width = `${pct}%`;

            // Color coding
            if (pct > 90) usageBar.style.backgroundColor = '#fa5252'; // Red
            else if (pct > 75) usageBar.style.backgroundColor = '#fcc419'; // Yellow
            else usageBar.style.backgroundColor = 'var(--primary)'; // Blue
        }

    } catch (error) {
        console.error('Failed to load org status:', error);
    }
}

async function loadAuditLogs() {
    const filterEl = document.getElementById('status-filter');
    const statusFilter = filterEl ? filterEl.value : '';
    const query = statusFilter ? `?status=${statusFilter}&limit=50` : '?limit=50';

    try {
        const data = await apiCall(`/audit/logs${query}`);
        const tbody = document.getElementById('audit-logs-body');
        if (!tbody) return;

        if (!data.logs || data.logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="loading">No audit logs found</td></tr>';
            return;
        }

        tbody.innerHTML = data.logs.map(log => `
            <tr>
                <td><code style="font-size: 11px;">${log.request_id.substring(0, 8)}...</code></td>
                <td>${formatTime(log.timestamp)}</td>
                <td title="${log.url}">${truncateUrl(log.url)}</td>
                <td><span class="badge ${log.status === 'ok' ? 'badge-success' : 'badge-danger'}">${log.status === 'ok' ? 'Allowed' : 'Blocked'}</span></td>
                <td>${(log.risk_score * 100).toFixed(0)}%</td>
                <td>${log.reasons?.slice(0, 2).join(', ') || '-'}</td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Failed to load audit logs:', error);
        const tbody = document.getElementById('audit-logs-body');
        if (tbody) {
            if (error.message.includes('403')) {
                tbody.innerHTML = `
                 <tr>
                     <td colspan="6" style="text-align:center; padding: 60px 20px;">
                         <div style="display: flex; flex-direction: column; align-items: center; gap: 12px;">
                             <div style="font-size: 32px;">🔒</div>
                             <h3 style="margin: 0; font-size: 18px;">Audit Logs Locked</h3>
                             <p style="margin: 0; color: #666; max-width: 400px; line-height: 1.5;">Access to detailed request logs, compliance data, and advanced filtering is available on Pro and Enterprise tiers.</p>
                             <a href="https://forms.gle/vGtps8qX4PeXJqn9A" target="_blank" class="btn btn-primary" style="margin-top: 12px;">Upgrade Plan</a>
                         </div>
                     </td>
                 </tr>
              `;
            } else {
                tbody.innerHTML = '<tr><td colspan="6" class="loading">Failed to load logs</td></tr>';
            }
        }
    }
}

async function loadCapabilities() {
    try {
        const caps = await apiCall('/capabilities');
        const list = document.getElementById('capabilities-list');
        if (!list) return;

        list.innerHTML = Object.entries(caps)
            .filter(([key]) => !key.endsWith('_status'))
            .map(([key, value]) => {
                const statusKey = `${key}_status`;
                const status = caps[statusKey];
                const isEnabled = value === true;

                return `
                <div class="status-item">
                    <span class="status-name">
                        ${isEnabled ? '✅' : '❌'} ${formatCapabilityName(key)}
                    </span>
                    <span style="color: var(--text-muted); font-size: 12px;">
                        ${status || (isEnabled ? 'Available' : 'Not available')}
                    </span>
                </div>
            `;
            }).join('');
    } catch (error) {
        console.error('Failed to load capabilities:', error);
    }
}

async function generateApiKey() {
    const keyName = document.getElementById('key-name').value || 'New Key';
    const generateBtn = document.querySelector('button[onclick="generateApiKey()"]');

    try {
        if (generateBtn) {
            generateBtn.disabled = true;
            generateBtn.textContent = 'Generating...';
        }

        const result = await apiCall('/auth/keys', {
            method: 'POST',
            body: JSON.stringify({ label: keyName })
        });

        const key = result.api_key;

        // Show the generated key
        const keyDisplay = document.getElementById('generated-key');
        if (keyDisplay) keyDisplay.textContent = key;

        const container = document.getElementById('generated-key-container');
        if (container) container.style.display = 'block';

        // Add to list
        const list = document.getElementById('api-keys-list');
        if (list) {
            const newItem = document.createElement('div');
            newItem.className = 'api-key-item';
            newItem.innerHTML = `
            <div class="key-info">
                <span class="key-name">${result.label}</span>
                <code class="key-value">${result.prefix}</code>
            </div>
            <div class="key-actions">
                <button class="btn btn-sm btn-copy" onclick="copyKey('${key}')">Copy</button>
            </div>
        `;
            list.appendChild(newItem);
        }

    } catch (error) {
        alert('Failed to generate key: ' + error.message);
        console.error(error);
    } finally {
        if (generateBtn) {
            generateBtn.disabled = false;
            generateBtn.textContent = 'Generate New Key';
        }
    }
}

function copyKey(key) {
    navigator.clipboard.writeText(key).then(() => {
        alert('Key copied to clipboard!');
    });
}

function copyGeneratedKey() {
    const keyEl = document.getElementById('generated-key');
    if (keyEl) copyKey(keyEl.textContent);
}

// Utility functions
function formatTime(timestamp) {
    if (!timestamp) return '-';
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
}

function truncateUrl(url) {
    if (!url) return '-';
    if (url.length > 40) {
        return url.substring(0, 40) + '...';
    }
    return url;
}

function formatCapabilityName(name) {
    return name
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase());
}

function showLoginModal() {
    const modal = document.getElementById('login-modal');
    if (modal) modal.style.display = 'flex';
}

function handleLogin() {
    const keyInput = document.getElementById('login-api-key');
    const key = keyInput.value.trim();

    if (!key) {
        alert('Please enter an API Key');
        return;
    }

    // Save and reload
    CONFIG.apiKey = key;
    localStorage.setItem('safebrowse-dashboard-config', JSON.stringify(CONFIG));

    const modal = document.getElementById('login-modal');
    if (modal) modal.style.display = 'none';
    location.reload();
}

// Expose functions globally for onclick handlers
window.saveSettings = saveSettings;
window.generateApiKey = generateApiKey;
window.copyKey = copyKey;
window.copyGeneratedKey = copyGeneratedKey;
window.loadAuditLogs = loadAuditLogs;
window.handleLogin = handleLogin;
window.showLoginModal = showLoginModal;
