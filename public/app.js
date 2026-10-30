const $ = (s) => document.querySelector(s);
const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
async function api(path, opts) {
  const r = await fetch(path, opts);
  if (!r.ok) { let m = r.statusText; try { const j = await r.json(); m = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail); } catch (e) {} throw new Error(m); }
  return r.json();
}
const demoParam = () => ($('#demo') && $('#demo').checked ? 'true' : 'false');
const badge = (d) => (d ? ' <span class="badge demo">DEMO DATA</span>' : '');
const COLORS = ['#5b8cff', '#34d399', '#fbbf24', '#f87171', '#a78bfa', '#22d3ee', '#fb923c'];
const charts = {};
function chart(id, type, labels, datasets, opts = {}) {
  if (charts[id]) charts[id].destroy();
  if (typeof Chart === 'undefined') { $('#' + id).replaceWith(Object.assign(document.createElement('p'), {textContent: 'Chart.js could not load (offline?). Tables below still work.'})); return; }
  Chart.defaults.color = '#8b97ad'; Chart.defaults.borderColor = '#263147';
  charts[id] = new Chart($('#' + id), {type, data: {labels, datasets}, options: Object.assign({responsive: true, plugins: {legend: {display: datasets.length > 1 || type === 'doughnut'}}}, opts)});
}
function table(sel, cols, rows) {
  const el = $(sel);
  if (!rows.length) { el.innerHTML = '<p style="color:var(--mute)">No data.</p>'; return; }
  el.innerHTML = '<div class="scroll"><table><thead><tr>' + cols.map((c, i) => `<th data-i="${i}">${esc(c[0])}</th>`).join('') +
    '</tr></thead><tbody>' + rows.map((r) => '<tr>' + cols.map((c) => `<td>${c[1](r)}</td>`).join('') + '</tr>').join('') + '</tbody></table></div>';
  el.querySelectorAll('th').forEach((th) => th.onclick = () => {
    const i = +th.dataset.i, body = el.querySelector('tbody'), dir = th.dataset.dir === 'asc' ? -1 : 1; th.dataset.dir = dir === 1 ? 'asc' : 'desc';
    const val = (tr) => tr.children[i].textContent.trim(), num = (s) => parseFloat(s.replace(/[^\d.-]/g, ''));
    [...body.rows].sort((a, b) => { const x = val(a), y = val(b), nx = num(x), ny = num(y); return (isNaN(nx) || isNaN(ny) ? x.localeCompare(y) : nx - ny) * dir; }).forEach((tr) => body.appendChild(tr));
  });
}
function banner(sum) {
  const el = $('#banner'); let h = '';
  if (sum.demo_responses > 0) h += `<div class="banner"><b>DEMO DATA included</b> (${sum.demo_responses} responses). These are synthetic, deliberately flawed samples, NOT results from any AI model.</div>`;
  if (sum.evaluated_responses === 0) h += '<div class="banner info">No evaluations yet. Use the Submit page, <code>python run.py submit</code>, <code>python run.py benchmark</code>, or load <code>python run.py demo</code>.</div>';
  el.innerHTML = h;
}
async function initDashboard() {
  const q = '?include_demo=' + demoParam();
  const [sum, models, tasks, diff, fail] = await Promise.all([api('/api/summary' + q), api('/api/models' + q), api('/api/task-performance' + q), api('/api/difficulty' + q), api('/api/failures' + q)]);
  banner(sum);
  const k = [['Benchmark tasks', sum.total_tasks], ['Evaluated responses', sum.evaluated_responses], ['Overall accuracy', sum.overall_accuracy_pct + '%'], ['Average score', sum.average_score + ' / 100'], ['Tests passed', sum.tests_passed], ['Tests failed', sum.tests_failed]];
  $('#kpis').innerHTML = k.map((x) => `<div class="kpi"><div class="l">${x[0]}</div><div class="v">${esc(x[1])}</div></div>`).join('');
  const lbl = (m) => m.model_name + (m.model_version ? ' ' + m.model_version : '') + (m.is_demo ? ' [DEMO]' : '');
  chart('cModels', 'bar', models.map(lbl), [{label: 'Average score', data: models.map((m) => m.avg_score), backgroundColor: COLORS[0]}, {label: 'Accuracy %', data: models.map((m) => m.accuracy_pct), backgroundColor: COLORS[1]}], {scales: {y: {max: 100, beginAtZero: true}}});
  chart('cDiff', 'bar', diff.map((d) => d.difficulty), [{label: 'Average score', data: diff.map((d) => d.avg_score), backgroundColor: COLORS[0]}, {label: 'Test failure rate %', data: diff.map((d) => d.failure_rate_pct), backgroundColor: COLORS[3]}], {scales: {y: {max: 100, beginAtZero: true}}});
  chart('cTasks', 'bar', tasks.map((t) => t.task_id), [{label: 'Average score', data: tasks.map((t) => t.avg_score), backgroundColor: COLORS[4]}], {scales: {y: {max: 100, beginAtZero: true}}});
  const cats = Object.entries(fail.by_category);
  chart('cFail', 'doughnut', cats.map((c) => c[0]), [{data: cats.map((c) => c[1]), backgroundColor: COLORS}]);
  table('#tModels', [['Model', (m) => esc(m.model_name) + badge(m.is_demo)], ['Version', (m) => esc(m.model_version)], ['Tasks attempted', (m) => m.tasks_attempted], ['Responses', (m) => m.attempts], ['Passed tests', (m) => m.tests_passed], ['Failed tests', (m) => m.tests_failed], ['Accuracy %', (m) => m.accuracy_pct], ['Avg score', (m) => m.avg_score], ['Common failures', (m) => m.common_failures.map((c) => `${esc(c.category)} (${c.count})`).join(', ') || '-']], models);
  table('#tTasks', [['Task', (t) => esc(t.task_id)], ['Title', (t) => esc(t.title)], ['Difficulty', (t) => esc(t.difficulty)], ['Attempts', (t) => t.attempts], ['Accuracy %', (t) => t.accuracy_pct], ['Avg score', (t) => t.avg_score], ['Failed tests', (t) => t.tests_failed]], tasks);
}
async function initFailures() {
  const f = await api('/api/failures?include_demo=' + demoParam());
  banner(f.summary);
  const rc = f.root_cause, tot = Object.values(rc).reduce((a, b) => a + b, 0) || 1;
  $('#rootcause').innerHTML = Object.entries(rc).map(([k, v]) => `<div class="kpi"><div class="l">${esc(k.replace(/_/g, ' '))}</div><div class="v">${v}</div><div class="l">${(100 * v / tot).toFixed(1)}% of failed tests</div></div>`).join('') || '<p style="color:var(--mute)">No failures recorded.</p>';
  $('#hardest').textContent = f.hardest_difficulty ? `Difficulty with the highest test failure rate: ${f.hardest_difficulty}` : 'No data yet.';
  chart('cKind', 'bar', Object.keys(f.by_kind), [{label: 'Failed tests', data: Object.values(f.by_kind), backgroundColor: COLORS[3]}]);
  chart('cDiffF', 'bar', f.difficulty.map((d) => d.difficulty), [{label: 'Failure rate %', data: f.difficulty.map((d) => d.failure_rate_pct), backgroundColor: COLORS[2]}], {scales: {y: {max: 100, beginAtZero: true}}});
  table('#tRanked', [['Task', (t) => esc(t.task_id + ' ' + t.title)], ['Difficulty', (t) => esc(t.difficulty)], ['Responses', (t) => t.attempts], ['With failures', (t) => t.submissions_with_failures], ['Failure rate %', (t) => t.failure_rate_pct]], f.tasks_ranked);
  table('#tEdge', [['Test', (e) => esc(e.test_id)], ['Kind', (e) => esc(e.kind)], ['What it checks', (e) => esc(e.note)], ['Failures', (e) => e.failures]], f.edge_cases);
  table('#tExamples', [['Model', (e) => esc(e.model_name) + badge(e.is_demo)], ['Test', (e) => esc(e.test_id)], ['Input', (e) => `<code>${esc(e.args)}</code>`], ['Correct (expected)', (e) => `<code class="pass">${esc(e.expected)}</code>`], ['Model output', (e) => `<code class="fail">${esc(e.actual)}</code>`], ['Category', (e) => esc(e.category)]], f.examples);
}
async function initSubmit() {
  const tasks = await api('/api/tasks'); const sel = $('#task');
  sel.innerHTML = tasks.map((t) => `<option value="${esc(t.id)}">${esc(t.id)} - ${esc(t.title)} (${esc(t.difficulty)})</option>`).join('');
  const show = () => { const t = tasks.find((x) => x.id === sel.value);
    $('#taskinfo').innerHTML = `<p>${esc(t.description)}</p><p><b>Input:</b> ${esc(t.input_format)}<br><b>Output:</b> ${esc(t.expected_output)}<br><b>Function name:</b> <code>${esc(t.function)}</code></p>` +
      '<b>Examples</b><pre>' + esc(t.examples.map((e) => `${t.function}(${e.args.map((a) => JSON.stringify(a)).join(', ')}) -> ${JSON.stringify(e.expected)}`).join('\n')) + '</pre>'; };
  sel.onchange = show; show();
  $('#go').onclick = async () => {
    const btn = $('#go'); btn.disabled = true; $('#result').innerHTML = '<p>Running tests (hidden tests may take a few seconds)...</p>';
    try {
      const mc = $('#mc').value;
      const r = await api('/api/evaluate', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({model_name: $('#mname').value, model_version: $('#mver').value, task_id: sel.value, code: $('#code').value, run_index: +$('#run').value || 1, manual_review: mc === '' ? null : {complexity: +mc}})});
      $('#result').innerHTML = `<div class="card"><h2>Score</h2><div class="kpi"><div class="v">${r.score} / 100</div></div><p>${Object.entries(r.breakdown).map(([k, v]) => `${esc(k)}: <b>${v}</b>`).join(' &middot; ')}</p></div><div id="rt"></div>`;
      table('#rt', [['Test', (t) => esc(t.test_id)], ['Result', (t) => t.passed ? '<span class="pass">PASS</span>' : '<span class="fail">FAIL</span>'], ['Category', (t) => esc(t.category || '-')], ['Details', (t) => t.hidden ? '<i style="color:var(--mute)">hidden test</i>' : `input <code>${esc(t.args_repr)}</code> expected <code>${esc(t.expected_repr)}</code> got <code>${esc(t.actual_repr)}</code>`]], r.tests);
    } catch (e) { $('#result').innerHTML = `<div class="banner">${esc(e.message)}</div>`; }
    btn.disabled = false;
  };
}
document.addEventListener('DOMContentLoaded', () => {
  const page = document.body.dataset.page; const init = {dashboard: initDashboard, failures: initFailures, submit: initSubmit}[page];
  const run = () => init().catch((e) => { $('#banner').innerHTML = `<div class="banner">${esc(e.message)}</div>`; });
  if ($('#demo')) $('#demo').onchange = run; run();
});
