import React, { useEffect, useMemo, useRef, useState } from 'react';
import gsap from 'gsap';
import * as echarts from 'echarts';

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
  const trendRef = useRef(null);
  const pieRef = useRef(null);
  const trendChartRef = useRef(null);
  const pieChartRef = useRef(null);
  const baseUrl = useMemo(() => getBackendBaseUrl(), []);
  const [stats, setStats] = useState({ total: 0, blocked: 0, types: 0, success: '0%' });
  const [isRedAlert, setIsRedAlert] = useState(false);
  const [trend, setTrend] = useState({ labels: [], data: [] });
  const [typeBreakdown, setTypeBreakdown] = useState({ labels: [], data: [] });
  const [selectedType, setSelectedType] = useState('');
  const [logs, setLogs] = useState([]);
  const [logQuery, setLogQuery] = useState('');
  const [alertConfig, setAlertConfig] = useState({
    enabled: false,
    severity: 'high',
    windowMinutes: 5,
    minCount: 3,
    channel: 'ui',
  });
  const [alertMessage, setAlertMessage] = useState('');

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
    const load = () => {
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
    };

    load();
    const t = window.setInterval(load, 5000);
    return () => {
      mounted = false;
      window.clearInterval(t);
    };
  }, [baseUrl]);

  useEffect(() => {
    let mounted = true;
    const load = () => {
      fetch('/api/stats/attacks', { credentials: 'include' })
        .then((r) => r.json())
        .then((data) => {
          if (!mounted) return;
          setTrend({
            labels: Array.isArray(data.labels) ? data.labels : [],
            data: Array.isArray(data.data) ? data.data : [],
          });
        })
        .catch(() => {
          if (!mounted) return;
        });
    };
    load();
    const t = window.setInterval(load, 15000);
    return () => {
      mounted = false;
      window.clearInterval(t);
    };
  }, []);

  useEffect(() => {
    let mounted = true;
    const load = () => {
      fetch('/api/attack/type_breakdown', { credentials: 'include' })
        .then((r) => r.json())
        .then((data) => {
          if (!mounted) return;
          setTypeBreakdown({
            labels: Array.isArray(data.labels) ? data.labels : [],
            data: Array.isArray(data.data) ? data.data : [],
          });
        })
        .catch(() => {
          if (!mounted) return;
        });
    };
    load();
    const t = window.setInterval(load, 15000);
    return () => {
      mounted = false;
      window.clearInterval(t);
    };
  }, []);

  useEffect(() => {
    let mounted = true;

    const buildUrl = () => {
      const u = new URL('/api/attack/logs', window.location.origin);
      u.searchParams.set('limit', '80');
      if (selectedType) u.searchParams.set('type', selectedType);
      if (logQuery) u.searchParams.set('q', logQuery);
      return u.pathname + u.search;
    };

    const load = () => {
      fetch(buildUrl(), { credentials: 'include' })
        .then((r) => r.json())
        .then((data) => {
          if (!mounted) return;
          setLogs(Array.isArray(data.logs) ? data.logs : []);
        })
        .catch(() => {
          if (!mounted) return;
        });
    };

    load();
    const t = window.setInterval(load, 5000);
    return () => {
      mounted = false;
      window.clearInterval(t);
    };
  }, [selectedType, logQuery]);

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem('securityDashboard.alertConfig');
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (!parsed || typeof parsed !== 'object') return;
      setAlertConfig((v) => ({ ...v, ...parsed }));
    } catch (_err) {
      return;
    }
  }, []);

  useEffect(() => {
    try {
      window.localStorage.setItem('securityDashboard.alertConfig', JSON.stringify(alertConfig));
    } catch (_err) {
      return;
    }
  }, [alertConfig]);

  useEffect(() => {
    if (!alertConfig.enabled) {
      setAlertMessage('');
      return;
    }

    const order = { low: 1, medium: 2, high: 3, critical: 4 };
    const minLevel = order[String(alertConfig.severity || 'high')] || 3;
    const now = Date.now();
    const windowMs = Math.max(1, Number(alertConfig.windowMinutes || 5)) * 60 * 1000;
    const count = logs.filter((l) => {
      const ts = Date.parse(l.time);
      const sev = order[String(l.severity || 'medium')] || 2;
      return Number.isFinite(ts) && now - ts <= windowMs && sev >= minLevel;
    }).length;

    const minCount = Math.max(1, Number(alertConfig.minCount || 3));
    if (count >= minCount) {
      setAlertMessage(`ALERT: ${count} ${alertConfig.severity}+ attacks in last ${alertConfig.windowMinutes}m`);
      if (alertConfig.channel === 'ui') {
        return;
      }
      return;
    }
    setAlertMessage('');
  }, [alertConfig, logs]);

  useEffect(() => {
    if (!trendRef.current) return;
    const chart = echarts.init(trendRef.current);
    trendChartRef.current = chart;
    return () => {
      try {
        chart.dispose();
      } catch (_err) {
        return;
      }
    };
  }, []);

  useEffect(() => {
    if (!pieRef.current) return;
    const chart = echarts.init(pieRef.current);
    pieChartRef.current = chart;
    const onClick = (params) => {
      const name = params && params.name ? String(params.name) : '';
      if (!name) return;
      setSelectedType((v) => (v === name ? '' : name));
    };
    chart.on('click', onClick);
    return () => {
      try {
        chart.off('click', onClick);
        chart.dispose();
      } catch (_err) {
        return;
      }
    };
  }, []);

  useEffect(() => {
    const resize = () => {
      try {
        if (trendChartRef.current) trendChartRef.current.resize();
        if (pieChartRef.current) pieChartRef.current.resize();
      } catch (_err) {
        return;
      }
    };
    window.addEventListener('resize', resize);
    return () => window.removeEventListener('resize', resize);
  }, []);

  useEffect(() => {
    if (!trendChartRef.current) return;
    trendChartRef.current.setOption({
      grid: { left: 36, right: 18, top: 26, bottom: 30 },
      xAxis: {
        type: 'category',
        data: trend.labels,
        boundaryGap: false,
        axisLabel: { color: 'rgba(229,229,229,0.65)' },
        axisLine: { lineStyle: { color: 'rgba(255,0,0,0.18)' } },
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: 'rgba(229,229,229,0.65)' },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
      },
      tooltip: { trigger: 'axis' },
      series: [
        {
          name: 'Attacks',
          type: 'line',
          smooth: true,
          data: trend.data,
          showSymbol: false,
          lineStyle: { width: 2, color: 'rgba(255,0,0,0.85)' },
          areaStyle: { color: 'rgba(255,0,0,0.12)' },
        },
      ],
    });
  }, [trend]);

  useEffect(() => {
    if (!pieChartRef.current) return;
    const seriesData = typeBreakdown.labels.map((l, i) => ({
      name: String(l),
      value: Number(typeBreakdown.data[i] || 0),
    }));
    pieChartRef.current.setOption({
      tooltip: { trigger: 'item' },
      legend: {
        top: 8,
        textStyle: { color: 'rgba(229,229,229,0.75)' },
      },
      series: [
        {
          name: 'Types',
          type: 'pie',
          radius: ['38%', '68%'],
          center: ['50%', '58%'],
          data: seriesData,
          emphasis: {
            scale: true,
            scaleSize: 8,
          },
          itemStyle: {
            borderColor: 'rgba(0,0,0,0.6)',
            borderWidth: 2,
          },
          label: { color: 'rgba(229,229,229,0.8)' },
        },
      ],
    });
  }, [typeBreakdown]);

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

        {alertMessage ? (
          <div className="st-alert">
            <div className="st-alert__text">{alertMessage}</div>
            <button className="btn" type="button" onClick={() => setAlertMessage('')}>Dismiss</button>
          </div>
        ) : null}

        <div className="st-visual-grid">
          <DashboardCard color="red" isRedAlert={isRedAlert} className="st-panel">
            <div className="st-panel__title">Attack Trend (14d)</div>
            <div className="st-chart" ref={trendRef} />
          </DashboardCard>
          <DashboardCard color="yellow" isRedAlert={isRedAlert} className="st-panel">
            <div className="st-panel__title">Attack Types (click to drill down)</div>
            <div className="st-chart" ref={pieRef} />
            {selectedType ? (
              <button className="btn st-clear" type="button" onClick={() => setSelectedType('')}>
                Clear filter: {selectedType}
              </button>
            ) : null}
          </DashboardCard>
        </div>

        <DashboardCard color="blue" isRedAlert={isRedAlert} className="st-panel st-panel--wide">
          <div className="st-panel__header">
            <div className="st-panel__title">Attack Details</div>
            <div className="st-panel__actions">
              <input
                className="st-input"
                value={logQuery}
                onChange={(e) => setLogQuery(e.target.value)}
                placeholder="Search payload"
              />
              {selectedType ? <span className="st-pill">type={selectedType}</span> : null}
            </div>
          </div>
          <div className="st-table-wrap">
            <table className="st-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Type</th>
                  <th>Severity</th>
                  <th>IP</th>
                  <th>Blocked</th>
                  <th>Payload</th>
                </tr>
              </thead>
              <tbody>
                {logs.length ? logs.map((l) => (
                  <tr key={l.id}>
                    <td className="st-td-time">{String(l.time || '').replace('T', ' ').slice(0, 19)}</td>
                    <td>{l.attack_type}</td>
                    <td>{l.severity}</td>
                    <td>{l.ip}</td>
                    <td>{l.blocked ? 'yes' : 'no'}</td>
                    <td className="st-td-payload" title={l.payload}>{l.payload}</td>
                  </tr>
                )) : (
                  <tr>
                    <td colSpan={6} className="st-empty">No data</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </DashboardCard>

        <DashboardCard color="red" isRedAlert={isRedAlert} className="st-panel st-panel--wide">
          <div className="st-panel__header">
            <div className="st-panel__title">Alert Config</div>
            <div className="st-panel__actions">
              <label className="st-switch">
                <input
                  type="checkbox"
                  checked={alertConfig.enabled}
                  onChange={(e) => setAlertConfig((v) => ({ ...v, enabled: e.target.checked }))}
                />
                <span className="st-switch__label">Enable</span>
              </label>
            </div>
          </div>

          <div className="st-form">
            <div className="st-field">
              <div className="st-field__label">Severity</div>
              <select
                className="st-select"
                value={alertConfig.severity}
                onChange={(e) => setAlertConfig((v) => ({ ...v, severity: e.target.value }))}
              >
                <option value="low">low+</option>
                <option value="medium">medium+</option>
                <option value="high">high+</option>
                <option value="critical">critical</option>
              </select>
            </div>

            <div className="st-field">
              <div className="st-field__label">Window (minutes)</div>
              <input
                className="st-input"
                type="number"
                min={1}
                value={alertConfig.windowMinutes}
                onChange={(e) => setAlertConfig((v) => ({ ...v, windowMinutes: Number(e.target.value || 1) }))}
              />
            </div>

            <div className="st-field">
              <div className="st-field__label">Min Count</div>
              <input
                className="st-input"
                type="number"
                min={1}
                value={alertConfig.minCount}
                onChange={(e) => setAlertConfig((v) => ({ ...v, minCount: Number(e.target.value || 1) }))}
              />
            </div>

            <div className="st-field">
              <div className="st-field__label">Channel</div>
              <select
                className="st-select"
                value={alertConfig.channel}
                onChange={(e) => setAlertConfig((v) => ({ ...v, channel: e.target.value }))}
              >
                <option value="ui">UI</option>
                <option value="email">Email</option>
                <option value="slack">Slack</option>
                <option value="wecom">WeCom</option>
                <option value="sms">SMS</option>
              </select>
            </div>
          </div>
        </DashboardCard>

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
