const API_BASE = '/api';
const REFRESH_INTERVAL = 3000; // 3 seconds

let currentFilter = '';

async function fetchStats() {
    const response = await fetch(`${API_BASE}/stats`);
    return response.json();
}

async function fetchJobs(status = '') {
    const url = status 
        ? `${API_BASE}/jobs?status=${status}`
        : `${API_BASE}/jobs`;
    const response = await fetch(url);
    return response.json();
}

async function fetchJob(jobId) {
    const response = await fetch(`${API_BASE}/jobs/${jobId}`);
    if (!response.ok) {
        throw new Error('Job not found');
    }
    return response.json();
}

function updateStats(stats) {
    document.getElementById('stat-pending').textContent = stats.pending;
    document.getElementById('stat-processing').textContent = stats.processing;
    document.getElementById('stat-completed').textContent = stats.completed;
    document.getElementById('stat-failed').textContent = stats.failed;
    document.getElementById('stat-total').textContent = stats.total;
    document.getElementById('last-updated').textContent = new Date().toLocaleTimeString();
}

function renderJobs(jobs) {
    const tbody = document.getElementById('jobs-body');
    
    if (jobs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="loading">No jobs found</td></tr>';
        return;
    }
    
    tbody.innerHTML = jobs.map(job => `
        <tr>
            <td><code>${job.id.slice(0, 8)}...</code></td>
            <td>${job.template_name}</td>
            <td><span class="status-badge ${job.status}">${job.status}</span></td>
            <td>${new Date(job.created_at).toLocaleString()}</td>
            <td>
                <button class="view-btn" onclick="viewJob('${job.id}')">View</button>
            </td>
        </tr>
    `).join('');
}

async function viewJob(jobId) {
    try {
        const job = await fetchJob(jobId);
        const modal = document.getElementById('job-modal');
        const title = document.getElementById('modal-title');
        const body = document.getElementById('modal-body');
        
        title.textContent = `Job: ${job.id.slice(0, 8)}...`;
        body.innerHTML = `
            <div class="job-detail-row">
                <span class="job-detail-label">ID:</span>
                <span class="job-detail-value"><code>${job.id}</code></span>
            </div>
            <div class="job-detail-row">
                <span class="job-detail-label">Template:</span>
                <span class="job-detail-value">${job.template_name}</span>
            </div>
            <div class="job-detail-row">
                <span class="job-detail-label">Status:</span>
                <span class="job-detail-value"><span class="status-badge ${job.status}">${job.status}</span></span>
            </div>
            <div class="job-detail-row">
                <span class="job-detail-label">Created:</span>
                <span class="job-detail-value">${new Date(job.created_at).toLocaleString()}</span>
            </div>
            ${job.started_at ? `
            <div class="job-detail-row">
                <span class="job-detail-label">Started:</span>
                <span class="job-detail-value">${new Date(job.started_at).toLocaleString()}</span>
            </div>
            ` : ''}
            ${job.completed_at ? `
            <div class="job-detail-row">
                <span class="job-detail-label">Completed:</span>
                <span class="job-detail-value">${new Date(job.completed_at).toLocaleString()}</span>
            </div>
            ` : ''}
            ${job.error ? `
            <div class="job-detail-row">
                <span class="job-detail-label">Error:</span>
                <span class="job-detail-value">${job.error}</span>
            </div>
            ` : ''}
            <div class="job-detail-row">
                <span class="job-detail-label">Payload:</span>
                <span class="job-detail-value">
                    <pre>${JSON.stringify(job.payload, null, 2)}</pre>
                </span>
            </div>
            ${job.result !== null && job.result !== undefined ? `
            <div class="job-detail-row">
                <span class="job-detail-label">Result:</span>
                <span class="job-detail-value">
                    <pre>${typeof job.result === 'object' ? JSON.stringify(job.result, null, 2) : job.result}</pre>
                </span>
            </div>
            ` : ''}
        `;
        
        modal.classList.add('active');
    } catch (error) {
        alert('Error loading job details: ' + error.message);
    }
}

async function refresh() {
    try {
        const [stats, jobs] = await Promise.all([
            fetchStats(),
            fetchJobs(currentFilter)
        ]);
        updateStats(stats);
        renderJobs(jobs);
    } catch (error) {
        console.error('Failed to refresh:', error);
    }
}

// Modal close handler
document.querySelector('.modal-close').addEventListener('click', () => {
    document.getElementById('job-modal').classList.remove('active');
});

document.querySelector('.modal').addEventListener('click', (e) => {
    if (e.target.classList.contains('modal')) {
        e.target.classList.remove('active');
    }
});

// Filter change handler
document.getElementById('status-filter').addEventListener('change', (e) => {
    currentFilter = e.target.value;
    refresh();
});

// Initial load and auto-refresh
refresh();
setInterval(refresh, REFRESH_INTERVAL);
