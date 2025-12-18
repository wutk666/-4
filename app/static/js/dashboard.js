// 更健壮的 dashboard 脚本：动态加载 Chart.js，显示调试信息
(function(){
  const CDN = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js';
  const DEBUG_ID = 'dashboard-debug';
  const notifyEl = () => document.getElementById('notify');
  const alertBannerEl = () => document.getElementById('alertBanner');

  function ensureDebugEl(){
    let el = document.getElementById(DEBUG_ID);
    if(!el){
      el = document.createElement('div');
      el.id = DEBUG_ID;
      el.style.cssText = 'position:fixed;left:12px;top:12px;z-index:9999;background:rgba(0,0,0,0.6);color:#fff;padding:8px 10px;border-radius:6px;font-size:12px;max-width:320px;backdrop-filter:blur(4px);';
      document.body.appendChild(el);
    }
    return el;
  }
  function debug(msg){
    console.error('[dashboard]', msg);
    const el = ensureDebugEl();
    el.textContent = String(msg).slice(0,1000);
  }

  function notify(message, type){
    const host = notifyEl();
    if(!host) return;
    host.innerHTML = `
      <div class="alert alert-${type} alert-dismissible fade show" role="alert">
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
      </div>
    `;
  }

  function showAlertBanner(message, type){
    const host = alertBannerEl();
    if(!host) return;
    if(!message){
      host.innerHTML = '';
      return;
    }
    host.innerHTML = `
      <div class="alert alert-${type} alert-dismissible fade show" role="alert">
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
      </div>
    `;
  }

  function loadScript(src, timeout=8000){
    return new Promise((resolve, reject)=>{
      const s = document.createElement('script');
      s.src = src; s.async = true;
      s.onload = ()=> resolve();
      s.onerror = (e)=> reject(new Error('load error '+src));
      document.head.appendChild(s);
      setTimeout(()=> reject(new Error('load timeout '+src)), timeout);
    });
  }

  async function ensureChart(){
    if(window.Chart) return;
    try{
      await loadScript(CDN);
      if(!window.Chart) throw new Error('Chart not available after load');
    }catch(e){
      debug('无法加载 Chart.js：' + e.message + ' — 请检查网络或改为本地文件');
      throw e;
    }
  }

  async function fetchJson(url){
    const r = await fetch(url, {credentials:'same-origin'});
    if(!r.ok){
      const txt = await r.text().catch(()=> '');
      throw new Error(`${url} => ${r.status} ${r.statusText} ${txt}`);
    }
    return r.json();
  }

  async function uploadFile(url, fieldName, file){
    const fd = new FormData();
    fd.append(fieldName, file);
    const r = await fetch(url, { method:'POST', body: fd, credentials:'same-origin' });
    const data = await r.json().catch(()=> ({}));
    if(!r.ok){
      throw new Error(data.error || `${r.status} ${r.statusText}`);
    }
    return data;
  }

  let trendChart, topIpChart, typeChart;

  let selectedAttackType = '';
  let attackLogsCache = [];
  let searchDebounceTimer = null;
  const ALERT_STORAGE_KEY = 'securityDashboard.alertConfig';
  const defaultAlertConfig = {
    enabled: false,
    severity: 'high',
    windowMinutes: 5,
    minCount: 3,
    channel: 'ui'
  };
  let alertConfig = { ...defaultAlertConfig };

  function genColors(n){
    const base = ['#ffd66b','#5ce0a0','#6bc1ff','#ff7bbf','#ff6b6b','#b88bff','#3ee7ff','#ffb86b'];
    const colors = [];
    const count = Math.max(0, Number(n || 0));

    for(let i=0;i<count;i++){
      if(i < base.length){
        colors.push(base[i]);
        continue;
      }
      const hue = (i * 47) % 360;
      colors.push(`hsl(${hue} 78% 62%)`);
    }
    return colors;
  }

  function axisStyle(){
    return {
      ticks: { color: 'rgba(255,255,255,0.75)', font: { size: 10 } },
      grid: { color: 'rgba(255,255,255,0.08)', drawBorder: false }
    };
  }

  function drawLine(ctx, labels, data){
      if(trendChart) trendChart.destroy();
      trendChart = new Chart(ctx, {
          type: 'line',
          data: {
            labels,
            datasets:[{
              label:'攻击次数',
              data,
              borderColor:'#ff2d2d',
              backgroundColor:'rgba(255,45,45,0.0)',
              tension:0.25,
              pointRadius:0,
              borderWidth:2
            }]
          },
          options: {
            responsive:true,
            plugins:{
              legend:{display:false},
              tooltip:{
                backgroundColor:'rgba(0,0,0,0.75)',
                borderColor:'rgba(255,45,45,0.25)',
                borderWidth:1,
                titleColor:'rgba(255,255,255,0.9)',
                bodyColor:'rgba(255,255,255,0.85)'
              }
            },
            animation:{duration:800},
            scales:{
              x: axisStyle(),
              y: axisStyle()
            }
          }
      });
  }

  function drawBar(ctx, labels, data){
      if(topIpChart) topIpChart.destroy();
      topIpChart = new Chart(ctx, {
          type: 'bar',
          data: { labels, datasets:[{ label:'次数', data, backgroundColor:'#6bc1ff' }]},
          options: { indexAxis:'y', responsive:true, plugins:{legend:{display:false}}, animation:{duration:700}}
      });
  }

  function drawPie(ctx, labels, data){
    if(typeChart) typeChart.destroy();
    typeChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels,
        datasets:[{
          data,
          backgroundColor: genColors(Array.isArray(labels) ? labels.length : 0),
          borderColor: 'rgba(0,0,0,0.35)',
          borderWidth: 2,
          hoverOffset: 8
        }]
      },
      options: {
        responsive:true,
        cutout: '60%',
        layout: { padding: { top: 6, left: 6, right: 6, bottom: 0 } },
        plugins:{
          legend:{
            display:true,
            position:'top',
            labels:{
              color:'rgba(255,255,255,0.78)',
              boxWidth: 14,
              boxHeight: 8,
              padding: 10,
              font: { size: 10 }
            }
          },
          tooltip:{
            backgroundColor:'rgba(0,0,0,0.75)',
            borderColor:'rgba(255,196,0,0.25)',
            borderWidth:1,
            titleColor:'rgba(255,255,255,0.9)',
            bodyColor:'rgba(255,255,255,0.85)'
          }
        },
        animation:{duration:700},
        onClick: (_evt, elements) => {
          try{
            if(!elements || !elements.length) return;

            const idx = elements[0].index;
            const label = typeChart?.data?.labels?.[idx];
            if(!label) return;
            toggleTypeFilter(String(label));
          }catch(_e){
            return;
          }
        }
      }
    });
  }

  function setTypeFilterLabel(){
    const el = document.getElementById('typeFilterLabel');
    if(!el) return;
    el.textContent = selectedAttackType ? selectedAttackType : '无';
  }

  function toggleTypeFilter(t){
    selectedAttackType = (selectedAttackType === t) ? '' : t;
    setTypeFilterLabel();
    loadAttackLogs().catch(()=>{});
  }

  function escapeHtml(s){
    return String(s)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#39;');
  }

  function renderAttackLogsTable(logs){
    const tbody = document.getElementById('attackLogTbody');
    if(!tbody) return;
    if(!logs || !logs.length){
      tbody.innerHTML = '<tr><td colspan="6" class="text-muted">暂无数据</td></tr>';
      return;
    }
    tbody.innerHTML = logs.map((l)=>{
      const time = String(l.time || '').replace('T',' ').slice(0,19);
      const blocked = l.blocked ? 'yes' : 'no';
      const payload = escapeHtml(l.payload || '');
      const ip = escapeHtml(l.ip || '');
      const type = escapeHtml(l.attack_type || '');
      const sev = escapeHtml(l.severity || '');
      return `
        <tr>
          <td class="text-nowrap">${escapeHtml(time)}</td>
          <td>${type}</td>
          <td>${sev}</td>
          <td class="text-nowrap">${ip}</td>
          <td>${blocked}</td>
          <td title="${payload}">${payload}</td>
        </tr>
      `;
    }).join('');
  }

  function buildAttackLogsUrl(){
    const u = new URL('/api/attack/logs', window.location.origin);
    u.searchParams.set('limit', '80');
    if(selectedAttackType) u.searchParams.set('type', selectedAttackType);
    const q = (document.getElementById('attackLogSearch')?.value || '').trim();
    if(q) u.searchParams.set('q', q);
    return u.pathname + u.search;
  }

  async function loadAttackLogs(){
    const tbody = document.getElementById('attackLogTbody');
    if(tbody) tbody.innerHTML = '<tr><td colspan="6" class="text-muted">加载中...</td></tr>';
    try{
      const data = await fetchJson(buildAttackLogsUrl());
      const logs = Array.isArray(data.logs) ? data.logs : [];
      attackLogsCache = logs;
      renderAttackLogsTable(logs);
      evaluateAlert();
    }catch(e){
      debug('/api/attack/logs 获取失败：' + e.message);
      renderAttackLogsTable([]);
    }
  }

  function loadAlertConfig(){
    try{
      const raw = window.localStorage.getItem(ALERT_STORAGE_KEY);
      if(!raw) return;
      const parsed = JSON.parse(raw);
      if(!parsed || typeof parsed !== 'object') return;
      alertConfig = { ...alertConfig, ...parsed };
    }catch(_e){
      return;
    }
  }

  function syncAlertForm(){
    const enabled = document.getElementById('alertEnabled');
    const severity = document.getElementById('alertSeverity');
    const windowMinutes = document.getElementById('alertWindowMinutes');
    const minCount = document.getElementById('alertMinCount');
    const channel = document.getElementById('alertChannel');
    if(enabled) enabled.checked = !!alertConfig.enabled;
    if(severity) severity.value = alertConfig.severity || 'high';
    if(windowMinutes) windowMinutes.value = String(alertConfig.windowMinutes || 5);
    if(minCount) minCount.value = String(alertConfig.minCount || 3);
    if(channel) channel.value = alertConfig.channel || 'ui';
  }

  function saveAlertConfigFromForm(){
    const enabled = document.getElementById('alertEnabled')?.checked;
    const severity = document.getElementById('alertSeverity')?.value;
    const windowMinutes = Number(document.getElementById('alertWindowMinutes')?.value || 5);
    const minCount = Number(document.getElementById('alertMinCount')?.value || 3);
    const channel = document.getElementById('alertChannel')?.value;
    alertConfig = {
      enabled: !!enabled,
      severity: String(severity || 'high'),
      windowMinutes: Math.max(1, windowMinutes || 5),
      minCount: Math.max(1, minCount || 3),
      channel: String(channel || 'ui')
    };
    try{
      window.localStorage.setItem(ALERT_STORAGE_KEY, JSON.stringify(alertConfig));
    }catch(_e){
      // ignore
    }
    evaluateAlert();
    notify('✅ 告警配置已保存（本地）', 'success');
  }

  function evaluateAlert(){
    if(!alertConfig.enabled){
      showAlertBanner('', 'danger');
      return;
    }
    const order = { low: 1, medium: 2, high: 3, critical: 4 };
    const minLevel = order[String(alertConfig.severity || 'high')] || 3;
    const now = Date.now();
    const windowMs = Math.max(1, Number(alertConfig.windowMinutes || 5)) * 60 * 1000;
    const count = (attackLogsCache || []).filter((l) => {
      const ts = Date.parse(l.time);
      const sev = order[String(l.severity || 'medium')] || 2;
      return Number.isFinite(ts) && now - ts <= windowMs && sev >= minLevel;
    }).length;
    const minCount = Math.max(1, Number(alertConfig.minCount || 3));
    if(count >= minCount){
      const channelHint = alertConfig.channel && alertConfig.channel !== 'ui'
        ? `（渠道 ${escapeHtml(alertConfig.channel)} 未接入，仅 UI 提示）`
        : '';
      showAlertBanner(
        `ALERT: 最近 ${escapeHtml(alertConfig.windowMinutes)} 分钟内 ${count} 条 ${escapeHtml(alertConfig.severity)}+ 攻击触发${channelHint}`,
        'danger'
      );
      return;
    }
    showAlertBanner('', 'danger');
  }

  async function loadAll(){
    try{
      await ensureChart();
    }catch(e){
      // 已在 ensureChart 中 debug
      return;
    }

    try{
      const s = await fetchJson('/api/stats/summary');
      const totalEl = document.getElementById('metricTotal');
      const blockedEl = document.getElementById('metricBlocked');
      const bannedEl = document.getElementById('metricBanned');
      if(totalEl) totalEl.textContent = s.total_attacks ?? '--';
      if(blockedEl) blockedEl.textContent = s.blocked_attacks ?? '--';
      if(bannedEl) bannedEl.textContent = s.banned_ips ?? '--';
    }catch(e){
      debug('/api/stats/summary 获取失败：' + e.message);
    }

    try{
      const trend = await fetchJson('/api/stats/attacks');
      drawLine(document.getElementById('trendChart'), trend.labels, trend.data);
    }catch(e){
      debug(e);
    }

    try{
      const top = await fetchJson('/api/stats/top_ips');
      drawBar(document.getElementById('topIpChart'), top.labels, top.data);
    }catch(e){
      debug(e);
    }

    try{
      const types = await fetchJson('/api/attack/type_breakdown');
      drawPie(document.getElementById('typeChart'), types.labels, types.data);
    }catch(e){
      debug(e);
    }

    try{
      const logs = await fetchJson('/logs');
      const txt = logs.map(l=> `${l.time} ${l.ip} blocked=${l.blocked}\n${l.payload}\n---`).join('\n');
      document.getElementById('recentLogs').innerText = txt || '暂无日志';
    }catch(e){
      // /logs 可能需要登录，显示提示
      debug('/logs 获取失败：' + e.message);
      const el = document.getElementById('recentLogs');
      if(el) el.innerText = '无法获取日志：请登录或检查 /logs 接口';
    }

    // 卡片入场
    document.querySelectorAll('.animated-card').forEach((el, idx) => {
        setTimeout(()=> el.classList.add('visible'), 80 * idx);
    });

    // 新增：攻击详情表格 & 告警配置
    setTypeFilterLabel();
    loadAlertConfig();
    syncAlertForm();
    await loadAttackLogs();
  }

  document.getElementById('refresh')?.addEventListener('click', loadAll);
  document.getElementById('btnUploadMascot')?.addEventListener('click', async ()=>{
    const input = document.getElementById('inputMascot');
    const file = input?.files?.[0];
    if(!file){
      notify('请选择要上传的吉祥物图片', 'warning');
      return;
    }
    try{
      const res = await uploadFile('/upload_mascot', 'mascot', file);
      notify(`✅ ${res.message || '上传成功'}。正在刷新页面...`, 'success');
      setTimeout(()=> window.location.reload(), 800);
    }catch(e){
      notify(`❌ 上传失败：${e.message}`, 'danger');
    }
  });

  document.getElementById('btnUploadDashboardBg')?.addEventListener('click', async ()=>{
    const input = document.getElementById('inputDashboardBg');
    const file = input?.files?.[0];
    if(!file){
      notify('请选择要上传的背景图片', 'warning');
      return;
    }
    try{
      const res = await uploadFile('/upload_dashboard_bg', 'dashboard_bg', file);
      if(res.url){
        document.body.style.setProperty('--dashboard-bg-url', `url('${res.url}?t=${Date.now()}')`);
      }
      notify(`✅ ${res.message || '上传成功'}。建议强制刷新以清除缓存。`, 'success');
    }catch(e){
      notify(`❌ 上传失败：${e.message}`, 'danger');
    }
  });

  document.getElementById('btnClearTypeFilter')?.addEventListener('click', ()=>{
    selectedAttackType = '';
    setTypeFilterLabel();
    loadAttackLogs().catch(()=>{});
  });

  document.getElementById('btnReloadAttackLogs')?.addEventListener('click', ()=>{
    loadAttackLogs().catch(()=>{});
  });

  document.getElementById('attackLogSearch')?.addEventListener('input', ()=>{
    if(searchDebounceTimer) window.clearTimeout(searchDebounceTimer);
    searchDebounceTimer = window.setTimeout(()=>{
      loadAttackLogs().catch(()=>{});
    }, 350);
  });

  document.getElementById('btnSaveAlert')?.addEventListener('click', ()=>{
    saveAlertConfigFromForm();
  });

  document.getElementById('alertEnabled')?.addEventListener('change', ()=>{
    saveAlertConfigFromForm();
  });

  window.addEventListener('load', loadAll);
})();