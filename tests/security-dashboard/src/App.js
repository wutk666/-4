import React, { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Environment, ContactShadows } from '@react-three/drei';

import ToyCard from './components/ToyCard';

const THEME = {
  bg: '#FDFBF7',
  primary: '#FF6B6B',
  secondary: '#4ECDC4',
  accent: '#FFE66D',
  text: '#2D3436',
};

const DEFAULT_BACKEND_BASE_URL = (() => {
  if (typeof window === 'undefined') return 'http://127.0.0.1:5000';
  const port = String(window.location.port || '');
  if (port === '5173') return 'http://127.0.0.1:5000';
  return window.location.origin;
})();

const BACKEND_BASE_URL =
  ((typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_BACKEND_BASE_URL) ? import.meta.env.VITE_BACKEND_BASE_URL : null) ||
  ((typeof process !== 'undefined' && process.env && process.env.REACT_APP_BACKEND_BASE_URL) ? process.env.REACT_APP_BACKEND_BASE_URL : null) ||
  DEFAULT_BACKEND_BASE_URL;

export default function App() {
  return (
    <div style={{ height: '100vh', width: '100vw', background: THEME.bg }}>
      <Canvas shadows camera={{ position: [0, 0, 10], fov: 50 }} style={{ background: THEME.bg }}>
        <ambientLight intensity={0.7} />
        <spotLight
          position={[10, 10, 10]}
          angle={0.15}
          penumbra={1}
          intensity={1}
          castShadow
        />

        <Environment preset="city" />

        <Suspense fallback={null}>
          <SceneContent />
        </Suspense>
      </Canvas>
    </div>
  );
}

function SceneContent() {
  return (
    <>
      <group position={[0, 0, 0]}>
        <ToyCard
          position={[-3, 2.5, 0]}
          color={THEME.secondary}
          label="Dashboard"
          href="/dashboard"
          backendBaseUrl={BACKEND_BASE_URL}
        />
        <ToyCard
          position={[0, 2.5, 0]}
          color={THEME.primary}
          label="Attack Hub"
          href="/attack_hub_legacy"
          backendBaseUrl={BACKEND_BASE_URL}
        />
        <ToyCard
          position={[3, 2.5, 0]}
          color={THEME.accent}
          label="Auth & Session"
          href="/attack/auth_security"
          backendBaseUrl={BACKEND_BASE_URL}
        />

        <ToyCard
          position={[-3, -0.5, 0]}
          color="#87C7F3"
          label="XSS"
          href="/test_xss"
          backendBaseUrl={BACKEND_BASE_URL}
        />
        <ToyCard
          position={[0, -0.5, 0]}
          color="#FF9F43"
          label="SQL Injection"
          href="/test_sqli"
          backendBaseUrl={BACKEND_BASE_URL}
        />
        <ToyCard
          position={[3, -0.5, 0]}
          color="#FF9FF3"
          label="Command"
          href="/test_cmdi"
          backendBaseUrl={BACKEND_BASE_URL}
        />

        <ToyCard
          position={[-3, -3.5, 0]}
          color="#A29BFE"
          label="Path Traversal"
          href="/test_path_traversal"
          backendBaseUrl={BACKEND_BASE_URL}
        />
        <ToyCard
          position={[0, -3.5, 0]}
          color="#55EFC4"
          label="Console"
          href="/console"
          backendBaseUrl={BACKEND_BASE_URL}
        />
        <ToyCard
          position={[3, -3.5, 0]}
          color="#FAB1A0"
          label="Logs"
          href="/get_banned_ips"
          backendBaseUrl={BACKEND_BASE_URL}
        />
      </group>

      <ContactShadows
        position={[0, -4, 0]}
        opacity={0.6}
        scale={20}
        blur={2.5}
        far={4.5}
        color="#E8DAC5"
      />

      <OrbitControls
        enableZoom={false}
        minPolarAngle={Math.PI / 2.5}
        maxPolarAngle={Math.PI / 2}
      />
    </>
  );
}
