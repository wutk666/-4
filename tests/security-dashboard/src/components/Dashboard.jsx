import React, { useEffect, useMemo, useRef, useState } from 'react';
import gsap from 'gsap';

import DashboardCard from './DashboardCard';
import FloatingIcon from './FloatingIcon';
import MusicPlayer from './MusicPlayer';
import { dashboardData, getBackendBaseUrl, musicTracks } from '../data';
import { useGlitchTitle } from '../hooks/useGSAPAnimations';

function resolveUrl(base, href) {
  if (!href) return null;
  if (/^https?:\/\//i.test(href)) return href;
  const b = String(base || '').replace(/\/$/, '');
  const p = String(href).startsWith('/') ? String(href) : `/${href}`;
  return `${b}${p}`;
}

export default function Dashboard() {
  const rootRef = useRef(null);
  const heroRef = useRef(null);
  const flashRef = useRef(null);
  const baseUrl = useMemo(() => getBackendBaseUrl(), []);
  const [stats, setStats] = useState({ total: 0, blocked: 0, types: 0, success: '0%' });
  const [isRedAlert, setIsRedAlert] = useState(false);

  useGlitchTitle(heroRef);

  const go = (href) => {
    const url = resolveUrl(baseUrl, href);
    if (!url) return;
    const w = window.top || window;
    w.location.assign(url);
  };

  useEffect(() => {
    if (!rootRef.current) return;
    const q = rootRef.current.querySelectorAll('.st-card, .hero, .topbar');
    if (!q || !q.length) return;
    gsap.fromTo(
      q,
      { opacity: 0, y: 16 },
      { opacity: 1, y: 0, duration: 0.5, stagger: 0.06, ease: 'power2.out' }
    );
  }, []);

  useEffect(() => {
    let mounted = true;
    fetch('/api/attack/stats', { credentials: 'include' })
      .then((r) => r.json())
      .then((data) => {
        if (!mounted) return;
        const total = Number(data.total || 0);
        const blocked = Number(data.blocked || 0);
        const types = Number(data.types || 0);
        const success = total > 0 ? `${Math.round((blocked / total) * 100)}%` : '0%';
        setStats({ total, blocked, types, success });
      })
      .catch(() => {
        if (!mounted) return;
      });
    return () => {
      mounted = false;
    };
  }, [baseUrl]);

  useEffect(() => {
    if (!flashRef.current) return;
    if (!isRedAlert) {
      gsap.to(flashRef.current, { opacity: 0, duration: 0.2, ease: 'power2.out' });
      return;
    }
    gsap.fromTo(
      flashRef.current,
      { opacity: 0 },
      { opacity: 0.85, duration: 0.06, yoyo: true, repeat: 6, ease: 'steps(1)' }
    );
  }, [isRedAlert]);

  useEffect(() => {
    const fog = document.querySelector('.bg-fog');
    if (isRedAlert) {
      gsap.to('body', { backgroundColor: '#1a0000', duration: 1.5 });
      if (fog) gsap.to(fog, { filter: 'hue-rotate(300deg) saturate(300%)', duration: 1.5 });
      if (rootRef.current) {
        gsap.to(rootRef.current, {
          x: 5,
          y: 5,
          duration: 0.1,
          repeat: -1,
          yoyo: true,
          ease: 'rough({ strength: 1, points: 20, randomize: true })',
        });
      }
    } else {
      gsap.to('body', { backgroundColor: '#050505', duration: 1.5 });
      if (fog) gsap.to(fog, { filter: 'none', duration: 1.5 });
      if (rootRef.current) {
        gsap.killTweensOf(rootRef.current);
        gsap.to(rootRef.current, { x: 0, y: 0, duration: 0.2, ease: 'power2.out' });
      }
    }
  }, [isRedAlert]);

  const itemRoute = (name) => {
    const table = {
      XSS: '/test_xss',
      SQL: '/test_sqli',
      Command: '/test_cmdi',
      Traversal: '/test_path_traversal',
      Auth: '/attack/auth_security',
      'Brute Force': null,
      DoS: null,
      Privilege: null,
      Upload: null,
    };
    return Object.prototype.hasOwnProperty.call(table, name) ? table[name] : null;
  };

  return (
    <div className={isRedAlert ? 'page red-alert' : 'page'} ref={rootRef}>
      <div className="bg-fog" />
      <div className="bg-overlay" />
      <div className="red-alert-flash" ref={flashRef} />
      <header className="topbar">
        <div className="topbar__brand">
          <div className="brand__title st-font">Attack Hub</div>
          <div className="brand__sub">前后端分离开发 / 生产单文件集成</div>
        </div>
        <div className="topbar__right">
          <a className="link" href={resolveUrl(baseUrl, '/login')} target="_top" rel="noreferrer">Login</a>
          <a className="link" href={resolveUrl(baseUrl, '/console')} target="_top" rel="noreferrer">Console</a>
          <button className={isRedAlert ? 'btn btn--primary' : 'btn'} type="button" onClick={() => setIsRedAlert((v) => !v)}>
            {isRedAlert ? 'CLOSE RIFT' : 'OPEN RIFT'}
          </button>
        </div>
      </header>

      <div className="hero">
        <div className="hero__title st-font" ref={heroRef}>SECURITY DASHBOARD</div>
        <div className="hero__sub">The Upside Down is watching your traffic.</div>
      </div>

      <main className="st-container">
        <div className="st-stat-grid">
          {dashboardData.stats.map((s) => {
            const Icon = s.icon;
            const value = s.key === 'total'
              ? stats.total
              : s.key === 'blocked'
                ? stats.blocked
                : s.key === 'types'
                  ? stats.types
                  : stats.success;
            return (
              <DashboardCard key={s.key} color={s.color} isRedAlert={isRedAlert} className="st-stat-card">
                <FloatingIcon intensity={0.5} className="st-stat-bgicon">
                  {Icon ? <Icon size={88} /> : null}
                </FloatingIcon>
                <div className="st-stat-value">{value}</div>
                <div className="st-stat-label">{s.label}</div>
              </DashboardCard>
            );
          })}
        </div>

        <div className="st-row-list">
          {dashboardData.rows.map((row) => {
            const RowIcon = row.mainIcon;
            return (
              <DashboardCard key={row.id} color={row.color} isRedAlert={isRedAlert} className="st-row-card">
                <div className="st-row-main">
                  <div className="st-row-mainicon">
                    <FloatingIcon intensity={1.5} className="st-row-mainicon-inner">
                      {RowIcon ? <RowIcon size={42} /> : null}
                    </FloatingIcon>
                  </div>
                  <div className="st-row-text">
                    <div className="st-row-title">{row.title}</div>
                    <div className="st-row-subtitle">{row.subTitle}</div>
                  </div>
                </div>

                <div className="st-row-items">
                  {row.items.map((it) => {
                    const href = itemRoute(it);
                    if (!href) {
                      return (
                        <div key={it} className="st-row-item st-row-item--disabled">
                          <FloatingIcon intensity={0.25} className="st-row-item-dot">
                            <span className="st-dot" />
                          </FloatingIcon>
                          <span className="st-row-item-label">{it}</span>
                        </div>
                      );
                    }
                    return (
                      <a
                        key={it}
                        className="st-row-item"
                        href={resolveUrl(baseUrl, href)}
                        target="_top"
                        rel="noreferrer"
                      >
                        <FloatingIcon intensity={0.8} className="st-row-item-dot">
                          <span className="st-dot" />
                        </FloatingIcon>
                        <span className="st-row-item-label">{it}</span>
                      </a>
                    );
                  })}
                </div>
              </DashboardCard>
            );
          })}
        </div>

        <div className="st-music">
          <MusicPlayer
            tracks={musicTracks}
            resolveUrl={(src) => resolveUrl(baseUrl, src)}
          />
        </div>
      </main>

      <footer className="footer">
        <span className="muted">Backend: {baseUrl}</span>
      </footer>
    </div>
  );
}

function Stats({ baseUrl }) {
  const [state, setState] = React.useState({ total: 0, blocked: 0, types: 0 });

  useEffect(() => {
    let mounted = true;
    const url = resolveUrl(baseUrl, '/api/attack/stats');
    fetch(url, { credentials: 'include' })
      .then((r) => r.json())
      .then((data) => {
        if (!mounted) return;
        setState({
          total: Number(data.total || 0),
          blocked: Number(data.blocked || 0),
          types: Number(data.types || 0),
        });
      })
      .catch(() => {
        if (!mounted) return;
      });

    return () => {
      mounted = false;
    };
  }, [baseUrl]);

  return (
    <div className="stats">
      <div className="stat">
        <div className="stat__k">Total</div>
        <div className="stat__v">{state.total}</div>
      </div>
      <div className="stat">
        <div className="stat__k">Blocked</div>
        <div className="stat__v">{state.blocked}</div>
      </div>
      <div className="stat">
        <div className="stat__k">Types</div>
        <div className="stat__v">{state.types}</div>
      </div>
    </div>
  );
}
