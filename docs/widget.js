const DATA_URL = 'stories.json';
const MAX_VISIBLE = 10;
const REFRESH_MS = 5 * 60 * 1000;
const COLORS = { cato:'#64748b', cbpp:'#ef4444', epi:'#a16207', itep:'#f97316', taxfoundation:'#2563eb', tpc:'#52525b', ybl:'#7c3aed' };

let data = { stories: [], sources: [], updated_at: null, errors: [] };
let query = '';
let source = 'all';
const lastVisitKey = 'taxPolicyWidgetLastVisit';
const previousVisit = localStorage.getItem(lastVisitKey) || '1970-01-01T00:00:00Z';

const $ = (id) => document.getElementById(id);

function escapeHtml(str = '') {
  return str.replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
}

function storyTime(story) { return story.published_at || story.first_seen_at || data.updated_at; }

function age(iso) {
  if (!iso) return '';
  const diff = Date.now() - new Date(iso).getTime();
  const min = Math.max(1, Math.round(diff / 60000));
  if (min < 60) return `${min}m`;
  const hrs = Math.round(min / 60);
  if (hrs < 24) return `${hrs}h`;
  const days = Math.round(hrs / 24);
  if (days < 7) return `${days}d`;
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

function fullDate(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleString(undefined, { month:'short', day:'numeric', hour:'numeric', minute:'2-digit' });
}

function isNew(story) {
  return (story.first_seen_at || storyTime(story) || '') > previousVisit;
}

function filteredStories() {
  const q = query.trim().toLowerCase();
  return data.stories.filter(s => {
    if (source !== 'all' && s.source_id !== source) return false;
    if (!q) return true;
    return [s.title, s.source, s.summary].join(' ').toLowerCase().includes(q);
  }).slice(0, MAX_VISIBLE);
}

function renderSources() {
  const sel = $('sourceFilter');
  const current = sel.value || 'all';
  sel.innerHTML = '<option value="all">All sources</option>' + (data.sources || []).map(s =>
    `<option value="${escapeHtml(s.id)}">${escapeHtml(s.short || s.name)}</option>`
  ).join('');
  sel.value = current;
}

function render() {
  const stories = filteredStories();
  const newCount = data.stories.filter(isNew).length;
  $('status').textContent = newCount ? `${newCount} new since last visit` : `${data.stories.length} tracked stories`;
  $('summary').hidden = !newCount;
  $('summary').textContent = newCount ? `NEW (${newCount})` : '';
  $('updated').textContent = data.updated_at ? `Updated ${fullDate(data.updated_at)}` : 'Updated unknown';

  if (!stories.length) {
    $('stories').innerHTML = '<div class="empty">No matching stories.</div>';
    return;
  }

  $('stories').innerHTML = stories.map(story => {
    const t = storyTime(story);
    const color = COLORS[story.source_id] || '#2563eb';
    return `<a class="story" data-source="${escapeHtml(story.source_id)}" href="${escapeHtml(story.url)}" target="_blank" rel="noopener" title="${escapeHtml(story.source)} • ${escapeHtml(fullDate(t))}">
      <span class="dot" style="background:${color}"></span>
      <span>
        <span class="story-title">${escapeHtml(story.title)}</span>
        <span class="meta">
          ${isNew(story) ? '<span class="new">NEW</span>' : ''}
          <span class="badge">${escapeHtml(story.source_short || story.source)}</span>
          <span>${escapeHtml(story.source)}</span>
        </span>
      </span>
      <span class="age">${escapeHtml(age(t))}</span>
    </a>`;
  }).join('');
}

async function load() {
  $('status').textContent = 'Loading stories...';
  try {
    const res = await fetch(`${DATA_URL}?v=${Date.now()}`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    data = await res.json();
    data.stories = data.stories || [];
    data.sources = data.sources || [];
    renderSources();
    render();
  } catch (err) {
    $('status').textContent = 'Could not load stories';
    $('stories').innerHTML = `<div class="empty">${escapeHtml(err.message)}</div>`;
  }
}

$('search').addEventListener('input', e => { query = e.target.value; render(); });
$('sourceFilter').addEventListener('change', e => { source = e.target.value; render(); });
$('refresh').addEventListener('click', load);
window.addEventListener('beforeunload', () => localStorage.setItem(lastVisitKey, new Date().toISOString()));
setTimeout(() => localStorage.setItem(lastVisitKey, new Date().toISOString()), 2500);
load();
setInterval(load, REFRESH_MS);
