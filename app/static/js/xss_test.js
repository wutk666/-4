// 像素方块粒子 + 提交逻辑
(() => {
  // Canvas 粒子（方块像素风）
  const canvas = document.getElementById('particle-canvas');
  const ctx = canvas && canvas.getContext ? canvas.getContext('2d') : null;
  let particles = [];

  function resize(){
    if(!canvas) return;
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  function rand(min, max){ return Math.random()*(max-min)+min }

  function initParticles(){
    if(!ctx) return;
    resize();
    particles = [];
    const count = Math.floor((canvas.width * canvas.height) / 40000); // 适配大小
    const cols = ['#0f2b3a', '#123e52', '#7be0ff', '#ff7bbf'];
    for(let i=0;i<Math.max(30, count);i++){
      particles.push({
        x: rand(0, canvas.width),
        y: rand(0, canvas.height),
        s: Math.floor(rand(2,8)), // 方块大小
        vx: rand(-0.25,0.25),
        vy: rand(-0.25,0.25),
        c: cols[Math.floor(rand(0, cols.length))]
      });
    }
    window.addEventListener('resize', resize);
    requestAnimationFrame(tick);
  }

  function tick(){
    if(!ctx) return;
    ctx.clearRect(0,0,canvas.width,canvas.height);
    particles.forEach(p=>{
      p.x += p.vx; p.y += p.vy;
      if(p.x < -10) p.x = canvas.width+10;
      if(p.x > canvas.width+10) p.x = -10;
      if(p.y < -10) p.y = canvas.height+10;
      if(p.y > canvas.height+10) p.y = -10;
      ctx.fillStyle = p.c;
      // 画像素方块（避免抗锯齿）
      ctx.fillRect(Math.round(p.x), Math.round(p.y), p.s, p.s);
    });
    requestAnimationFrame(tick);
  }

  // 提交与 UI
  async function sendPayload(payload){
    const resultEl = document.getElementById('result');
    resultEl.classList.remove('error');
    resultEl.textContent = '发送中……';
    try{
      const r = await fetch('/test_xss', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({input: payload})
      });
      const j = await r.json();
      if(!r.ok){
        resultEl.classList.add('error');
        resultEl.textContent = '防御触发：' + (j.message || j.error || JSON.stringify(j));
      } else {
        resultEl.textContent = '响应：' + (j.message || JSON.stringify(j));
      }
    }catch(err){
      resultEl.classList.add('error');
      resultEl.textContent = '网络错误：' + (err.message || err);
    }
  }

  async function loadMascotCard(){
    const card = document.getElementById('mascotCard');
    if(!card) return;
    try{
      const res = await fetch('/get_current_mascot', { cache: 'no-store' });
      if(!res.ok) return;
      const data = await res.json();
      const mascots = Array.isArray(data.mascots) ? data.mascots : [];
      const latest = mascots[0];
      if(latest && latest.url){
        card.style.backgroundImage = `url('${latest.url}')`;
      }
    } catch(err){
      // ignore, fallback to默认图片
    }
  }

  // 绑定事件
  window.addEventListener('load', ()=>{
    initParticles();
    loadMascotCard();

    const input = document.getElementById('payload');
    const sendBtn = document.getElementById('sendBtn');
    const clearBtn = document.getElementById('clearBtn');

    sendBtn?.addEventListener('click', ()=>{
      const v = input.value || '';
      sendPayload(v);
    });
    clearBtn?.addEventListener('click', ()=>{
      input.value = '';
      document.getElementById('result').textContent = '已清空。';
      document.getElementById('result').classList.remove('error');
    });

    // 回车提交
    input?.addEventListener('keydown', (e)=>{
      if(e.key === 'Enter'){ e.preventDefault(); sendBtn.click(); }
    });
  });
})();