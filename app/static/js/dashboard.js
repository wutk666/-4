// 更健壮的 dashboard 脚本：动态加载 Chart.js，显示调试信息
(function(){
  const CDN = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js';
  const DEBUG_ID = 'dashboard-debug';
  const notifyEl = () => document.getElementById('notify');

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

  function drawLine(ctx, labels, data){
      if(trendChart) trendChart.destroy();
      trendChart = new Chart(ctx, {
          type: 'line',
          data: { labels, datasets:[{ label:'攻击次数', data, borderColor:'#ff6b6b', backgroundColor:'rgba(255,107,107,0.12)', tension:0.25, pointRadius:3 }]},
          options: { responsive:true, plugins:{legend:{display:false}}, animation:{duration:800}}
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
          type: 'pie',
          data: { labels, datasets:[{ data, backgroundColor:['#ffd66b','#5ce0a0','#6bc1ff','#ff7bbf'] }]},
          options: { responsive:true, animation:{duration:700}}
      });
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
      const types = await fetchJson('/api/stats/types');
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

  window.addEventListener('load', loadAll);
})();