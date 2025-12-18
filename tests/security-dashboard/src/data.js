import {
  FaShieldAlt,
  FaBug,
  FaCode,
  FaTerminal,
  FaLock,
  FaChartLine,
  FaCogs,
} from 'react-icons/fa';
import { GiWalkieTalkie } from 'react-icons/gi';

export function getBackendBaseUrl() {
  try {
    if (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_BACKEND_BASE_URL) {
      return import.meta.env.VITE_BACKEND_BASE_URL;
    }
  } catch (_err) {
    // ignore
  }

  try {
    if (typeof process !== 'undefined' && process.env && process.env.REACT_APP_BACKEND_BASE_URL) {
      return process.env.REACT_APP_BACKEND_BASE_URL;
    }
  } catch (_err) {
    // ignore
  }

  if (typeof window === 'undefined') return 'http://127.0.0.1:5000';

  const port = String(window.location.port || '');
  if (port === '5173') {
    return 'http://127.0.0.1:5000';
  }

  return window.location.origin;
}

export const dashboardData = {
  stats: [
    { key: 'total', label: 'Total Attacks', value: 0, color: 'blue', icon: GiWalkieTalkie },
    { key: 'blocked', label: 'Blocked', value: 0, color: 'red', icon: FaShieldAlt },
    { key: 'types', label: 'Types', value: 0, color: 'blue', icon: FaBug },
    { key: 'success', label: 'Success', value: '0%', color: 'yellow', icon: FaChartLine },
  ],
  rows: [
    {
      id: 'injection',
      title: '注入类攻击',
      subTitle: 'Injection Attacks',
      color: 'red',
      mainIcon: FaCode,
      items: ['XSS', 'SQL', 'Command'],
    },
    {
      id: 'access',
      title: '访问控制',
      subTitle: 'Access Control',
      color: 'yellow',
      mainIcon: FaLock,
      items: ['Traversal', 'Privilege', 'Upload'],
    },
    {
      id: 'behavior',
      title: '行为分析',
      subTitle: 'Behavioral Analysis',
      color: 'blue',
      mainIcon: FaCogs,
      items: ['Auth', 'Brute Force', 'DoS'],
    },
  ],
};

export const musicTracks = [
  
];
