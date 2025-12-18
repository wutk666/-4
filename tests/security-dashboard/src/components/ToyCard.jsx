import React, { useState } from 'react';
import { useSpring, a } from '@react-spring/three';
import { Text, RoundedBox } from '@react-three/drei';

export default function ToyCard({ position, color, label, href, backendBaseUrl }) {
  const [hovered, setHover] = useState(false);
  const [pressed, setPressed] = useState(false);
  const [armed, setArmed] = useState(false);

  const resolveHref = () => {
    if (!href) return null;
    if (/^https?:\/\//i.test(href)) return href;
    const envBase = (() => {
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
      return null;
    })();

    const defaultBase = (() => {
      try {
        if (typeof window !== 'undefined' && String(window.location.port || '') === '5173') {
          const host = window.location.hostname || '127.0.0.1';
          return `http://${host}:5000`;
        }
        if (typeof window !== 'undefined') {
          return window.location.origin;
        }
      } catch (_err) {
        // ignore
      }
      return 'http://127.0.0.1:5000';
    })();

    const base = backendBaseUrl || envBase || defaultBase;
    const normalizedBase = String(base).replace(/\/$/, '');
    const normalizedPath = String(href).startsWith('/') ? String(href) : `/${href}`;
    return `${normalizedBase}${normalizedPath}`;
  };

  const go = (e) => {
    const url = resolveHref();
    if (!url) return;

    try {
      // eslint-disable-next-line no-console
      console.log('[ToyCard] navigate', url);
    } catch (_err) {
      // ignore
    }

    try {
      e.stopPropagation();
    } catch (_err) {
      // ignore
    }

    const ne = e && e.nativeEvent ? e.nativeEvent : null;
    const openNew = ne && (ne.ctrlKey || ne.metaKey);
    if (openNew) {
      window.open(url, '_blank', 'noopener,noreferrer');
      return;
    }

    const isEmbedded = (() => {
      try {
        return window.self !== window.top;
      } catch (_err) {
        return true;
      }
    })();

    if (isEmbedded) {
      try {
        try {
          window.parent.postMessage({ type: 'TOYCARD_NAVIGATE', url }, '*');
          return;
        } catch (_err) {
          // ignore
        }
        window.open(url, '_top');
        return;
      } catch (_err) {
        // fall through
      }
    }

    window.location.assign(url);
  };

  const { scale, rotation } = useSpring({
    scale: pressed ? 0.95 : hovered ? 1.08 : 1,
    rotation: hovered ? [0, 0.1, 0] : [0, 0, 0],
    config: { mass: 1, tension: 350, friction: 40 },
  });

  return (
    <a.group
      position={position}
      scale={scale}
      rotation={rotation}
      onPointerOver={() => {
        setHover(true);
        document.body.style.cursor = 'pointer';
      }}
      onPointerOut={() => {
        setHover(false);
        setPressed(false);
        setArmed(false);
        document.body.style.cursor = 'auto';
      }}
      onPointerDown={(e) => {
        try {
          e.stopPropagation();
        } catch (_err) {
          // ignore
        }
        setPressed(true);
        setArmed(true);
      }}
      onPointerUp={(e) => {
        try {
          e.stopPropagation();
        } catch (_err) {
          // ignore
        }
        setPressed(false);
        if (armed) go(e);
        setArmed(false);
      }}
      onClick={(e) => {
        try {
          e.stopPropagation();
        } catch (_err) {
          // ignore
        }
      }}
    >
      <RoundedBox args={[2.2, 2.5, 0.2]} radius={0.15} smoothness={4}>
        <meshStandardMaterial color={color} roughness={0.4} metalness={0.1} />
      </RoundedBox>

      <Text
        position={[0, -0.8, 0.11]}
        fontSize={0.25}
        color="#333"
        anchorX="center"
        anchorY="middle"
        font="https://fonts.gstatic.com/s/inter/v12/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuLyfAZ9hjp-Ek-_EeA.woff"
      >
        {label}
      </Text>

      <mesh position={[0, 0.3, 0.11]}>
        <boxGeometry args={[0.8, 0.8, 0.8]} />
        <meshStandardMaterial color="#fff" />
      </mesh>
    </a.group>
  );
}
