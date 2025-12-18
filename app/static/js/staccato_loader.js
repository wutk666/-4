(function(){
  const loader = document.getElementById('staccato-loader');
  if (!loader) return;

  window.__stLoaderEvents = window.__stLoaderEvents || [];

  const wordEl = loader.querySelector('[data-loader-word]');
  const words = ['OBSERVE', 'THINK', 'CREATE'];
  let wordIdx = 0;
  let wordTimer = null;

  function startWords(){
    if (!wordEl || wordTimer) return;
    wordTimer = setInterval(() => {
      wordIdx = (wordIdx + 1) % words.length;
      wordEl.textContent = words[wordIdx];
    }, 140);
  }

  function stopWords(){
    if (!wordTimer) return;
    clearInterval(wordTimer);
    wordTimer = null;
  }

  function restartProgress(){
    const fill = loader.querySelector('.progress-fill');
    if (!fill) return;
    fill.style.animation = 'none';
    void fill.offsetHeight;
    fill.style.animation = '';
  }

  function armFailsafe(){
    const tempo = (typeof window.__stLoaderTempoMs === 'number' && isFinite(window.__stLoaderTempoMs))
      ? window.__stLoaderTempoMs
      : (parseInt(window.__stLoaderTempoMs, 10) || 980);

    const hardResetMs = Math.max(1300, tempo + 350);
    try { loader.style.setProperty('--st-failsafe-ms', hardResetMs + 'ms'); } catch (e) {}

    if (window.__stLoaderAutoHideTimer) {
      clearTimeout(window.__stLoaderAutoHideTimer);
    }
    window.__stLoaderAutoHideTimer = setTimeout(() => {
      try {
        if (window.StaccatoLoader && typeof window.StaccatoLoader.hide === 'function') {
          window.StaccatoLoader.hide();
        }
      } catch (e) {}
    }, tempo);

    if (window.__stLoaderHardResetTimer) {
      clearTimeout(window.__stLoaderHardResetTimer);
    }
    window.__stLoaderHardResetTimer = setTimeout(() => {
      try {
        stopWords();
        document.body.classList.remove('staccato-loading');
        loader.setAttribute('data-show','0');
        loader.setAttribute('aria-hidden','true');
        loader.classList.remove('closing');
      } catch (e) {}
    }, hardResetMs);
  }

  window.StaccatoLoader = window.StaccatoLoader || {};

  window.StaccatoLoader.show = function(){
    if (loader.getAttribute('data-show') === '1' && !loader.classList.contains('closing')) {
      restartProgress();
      startWords();
      document.body.classList.add('staccato-loading');
      armFailsafe();
      return;
    }
    window.__stLoaderEvents = window.__stLoaderEvents || [];
    window.__stLoaderEvents.push({ type: 'show', ts: Date.now() });
    loader.classList.remove('closing');
    document.body.classList.add('staccato-loading');
    loader.setAttribute('data-show','1');
    loader.setAttribute('aria-hidden','false');
    restartProgress();
    startWords();
    armFailsafe();
  };

  window.StaccatoLoader.hide = function(){
    if (loader.getAttribute('data-show') !== '1') {
      document.body.classList.remove('staccato-loading');
      return;
    }
    if (loader.classList.contains('closing')) return;
    window.__stLoaderEvents = window.__stLoaderEvents || [];
    window.__stLoaderEvents.push({ type: 'hide', ts: Date.now() });
    loader.classList.add('closing');
    stopWords();
    setTimeout(() => {
      document.body.classList.remove('staccato-loading');
      loader.setAttribute('data-show','0');
      loader.setAttribute('aria-hidden','true');
      loader.classList.remove('closing');
    }, 220);
  };
})();
