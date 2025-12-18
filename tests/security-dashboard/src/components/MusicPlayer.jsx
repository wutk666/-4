import React, { useEffect, useMemo, useRef, useState } from 'react';
import gsap from 'gsap';

function fmt(t) {
  if (!Number.isFinite(t) || t <= 0) return '0:00';
  const m = Math.floor(t / 60);
  const s = Math.floor(t % 60);
  return `${m}:${String(s).padStart(2, '0')}`;
}

export default function MusicPlayer({ tracks, resolveUrl }) {
  const barRef = useRef(null);
  const fillRef = useRef(null);
  const audioRef = useRef(null);
  const fileRef = useRef(null);
  const urlMapRef = useRef(new Map());

  const [idx, setIdx] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [pos, setPos] = useState(0);
  const [dur, setDur] = useState(0);

  const [localTracks, setLocalTracks] = useState([]);
  const activeTracks = useMemo(() => {
    const base = Array.isArray(tracks) ? tracks : [];
    const extra = Array.isArray(localTracks) ? localTracks : [];
    return extra.length ? extra : base;
  }, [tracks, localTracks]);

  const track = useMemo(() => (activeTracks && activeTracks.length ? activeTracks[idx] : null), [activeTracks, idx]);
  const hasTracks = Boolean(activeTracks && activeTracks.length);

  const openDb = () => new Promise((resolve, reject) => {
    const req = indexedDB.open('security_dashboard_audio', 1);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains('tracks')) {
        db.createObjectStore('tracks', { keyPath: 'id' });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });

  const dbGetAll = async () => {
    const db = await openDb();
    return await new Promise((resolve, reject) => {
      const tx = db.transaction('tracks', 'readonly');
      const store = tx.objectStore('tracks');
      const req = store.getAll();
      req.onsuccess = () => resolve(req.result || []);
      req.onerror = () => reject(req.error);
      tx.oncomplete = () => db.close();
      tx.onerror = () => db.close();
    });
  };

  const dbPut = async (rec) => {
    const db = await openDb();
    return await new Promise((resolve, reject) => {
      const tx = db.transaction('tracks', 'readwrite');
      tx.objectStore('tracks').put(rec);
      tx.oncomplete = () => {
        db.close();
        resolve();
      };
      tx.onerror = () => {
        db.close();
        reject(tx.error);
      };
    });
  };

  const dbDelete = async (id) => {
    const db = await openDb();
    return await new Promise((resolve, reject) => {
      const tx = db.transaction('tracks', 'readwrite');
      tx.objectStore('tracks').delete(id);
      tx.oncomplete = () => {
        db.close();
        resolve();
      };
      tx.onerror = () => {
        db.close();
        reject(tx.error);
      };
    });
  };

  const hydrateFromRecords = (records) => {
    const sorted = (records || []).slice().sort((a, b) => Number(a.addedAt || 0) - Number(b.addedAt || 0));
    const next = [];
    sorted.forEach((r) => {
      if (!r || !r.id || !r.blob) return;
      const url = URL.createObjectURL(r.blob);
      urlMapRef.current.set(r.id, url);
      next.push({ id: r.id, title: r.title || r.name || 'Track', src: url, __objectUrl: true });
    });
    setLocalTracks(next);
    setIdx(0);
    setPos(0);
    setDur(0);
  };

  useEffect(() => {
    let mounted = true;
    dbGetAll()
      .then((records) => {
        if (!mounted) return;
        hydrateFromRecords(records);
      })
      .catch(() => {
        if (!mounted) return;
      });
    return () => {
      mounted = false;
      try {
        urlMapRef.current.forEach((url) => URL.revokeObjectURL(url));
        urlMapRef.current.clear();
      } catch (_err) {
        // ignore
      }
    };
  }, []);

  useEffect(() => {
    if (!track) return;

    const rawSrc = track.src;
    const isAbsolute = typeof rawSrc === 'string' && (/^https?:\/\//i.test(rawSrc) || /^blob:/i.test(rawSrc) || /^data:/i.test(rawSrc));
    const src = resolveUrl && !isAbsolute ? resolveUrl(rawSrc) : rawSrc;
    const a = new Audio(src);
    a.loop = true;
    audioRef.current = a;

    const onLoaded = () => setDur(a.duration || 0);
    const onTime = () => setPos(a.currentTime || 0);
    const onEnd = () => {
      setPlaying(false);
      setPos(0);
    };

    a.addEventListener('loadedmetadata', onLoaded);
    a.addEventListener('timeupdate', onTime);
    a.addEventListener('ended', onEnd);

    if (playing) {
      a.play().catch(() => {
        setPlaying(false);
      });
    }

    return () => {
      try {
        a.pause();
      } catch (_err) {
        // ignore
      }
      a.removeEventListener('loadedmetadata', onLoaded);
      a.removeEventListener('timeupdate', onTime);
      a.removeEventListener('ended', onEnd);
    };
  }, [track, resolveUrl]);

  useEffect(() => {
    if (!audioRef.current) return;
    const a = audioRef.current;
    if (playing) {
      a.play().catch(() => {
        setPlaying(false);
      });
    } else {
      try {
        a.pause();
      } catch (_err) {
        // ignore
      }
    }
  }, [playing]);

  useEffect(() => {
    if (!fillRef.current) return;
    const ratio = dur > 0 ? Math.min(1, Math.max(0, pos / dur)) : 0;
    gsap.to(fillRef.current, { width: `${ratio * 100}%`, duration: 0.15, ease: 'power2.out' });
  }, [pos, dur]);

  const onSeek = (e) => {
    if (!audioRef.current || !barRef.current || dur <= 0) return;
    const rect = barRef.current.getBoundingClientRect();
    const x = Math.min(rect.width, Math.max(0, e.clientX - rect.left));
    const t = (x / rect.width) * dur;
    audioRef.current.currentTime = t;
    setPos(t);
  };

  const prev = () => {
    if (!hasTracks) return;
    setPos(0);
    setPlaying(false);
    setIdx((v) => (activeTracks && activeTracks.length ? (v - 1 + activeTracks.length) % activeTracks.length : 0));
  };

  const next = () => {
    if (!hasTracks) return;
    setPos(0);
    setPlaying(false);
    setIdx((v) => (activeTracks && activeTracks.length ? (v + 1) % activeTracks.length : 0));
  };

  const onPickFile = () => {
    if (!fileRef.current) return;
    fileRef.current.click();
  };

  const onFileChange = async (e) => {
    const files = e.target && e.target.files ? Array.from(e.target.files) : [];
    if (!files.length) return;

    const added = [];
    for (const f of files) {
      if (!f) continue;
      const id = `track_${Date.now()}_${Math.random().toString(16).slice(2)}`;
      const rec = { id, title: f.name || 'Track', blob: f, addedAt: Date.now() };
      try {
        await dbPut(rec);
        added.push(rec);
      } catch (_err) {
        // ignore
      }
    }

    try {
      const records = await dbGetAll();
      urlMapRef.current.forEach((url) => URL.revokeObjectURL(url));
      urlMapRef.current.clear();
      hydrateFromRecords(records);
      setPlaying(true);
    } catch (_err) {
      // ignore
    }

    if (fileRef.current) fileRef.current.value = '';
  };

  const select = (i) => {
    if (!Number.isFinite(i)) return;
    setIdx(i);
    setPos(0);
    setDur(0);
  };

  const remove = async (id) => {
    if (!id) return;
    try {
      await dbDelete(id);
    } catch (_err) {
      // ignore
    }
    try {
      const url = urlMapRef.current.get(id);
      if (url) URL.revokeObjectURL(url);
      urlMapRef.current.delete(id);
    } catch (_err) {
      // ignore
    }
    try {
      const records = await dbGetAll();
      urlMapRef.current.forEach((url) => URL.revokeObjectURL(url));
      urlMapRef.current.clear();
      hydrateFromRecords(records);
    } catch (_err) {
      // ignore
    }
  };

  return (
    <div className="player">
      <input ref={fileRef} type="file" accept="audio/*" multiple style={{ display: 'none' }} onChange={onFileChange} />
      <div className="player__row">
        <div className="player__title">{track ? track.title : 'No music selected'}</div>
        <div className="player__time">{fmt(pos)} / {fmt(dur)}</div>
      </div>

      <div className="player__bar" ref={barRef} onClick={onSeek} role="presentation">
        <div className="player__fill" ref={fillRef} />
      </div>

      <div className="player__controls">
        <button className="btn" type="button" onClick={prev} disabled={!hasTracks}>Prev</button>
        <button className="btn btn--primary" type="button" onClick={() => setPlaying((v) => !v)} disabled={!hasTracks}>{playing ? 'Music: ON' : 'Music: OFF'}</button>
        <button className="btn" type="button" onClick={next} disabled={!hasTracks}>Next</button>
        <button className="btn" type="button" onClick={onPickFile}>Import</button>
      </div>

      {Array.isArray(localTracks) && localTracks.length ? (
        <div className="player__list" role="list">
          {localTracks.map((t, i) => (
            <div key={t.id} className={i === idx ? 'player__item player__item--active' : 'player__item'} role="listitem">
              <button className="player__pick" type="button" onClick={() => select(i)}>{t.title}</button>
              <button className="player__remove" type="button" onClick={() => remove(t.id)}>Remove</button>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
