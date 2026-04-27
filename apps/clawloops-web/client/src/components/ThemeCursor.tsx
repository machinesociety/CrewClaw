import { useEffect, useState } from 'react';

export default function ThemeCursor() {
  const [point, setPoint] = useState({ x: -100, y: -100 });
  const [down, setDown] = useState(false);
  const [enabled, setEnabled] = useState(false);

  useEffect(() => {
    const media = window.matchMedia('(pointer:fine)');
    const sync = () => setEnabled(media.matches);
    sync();
    media.addEventListener('change', sync);
    return () => media.removeEventListener('change', sync);
  }, []);

  useEffect(() => {
    if (!enabled) return;
    const onMove = (e: MouseEvent) => setPoint({ x: e.clientX, y: e.clientY });
    const onDown = () => setDown(true);
    const onUp = () => setDown(false);
    window.addEventListener('mousemove', onMove, { passive: true });
    window.addEventListener('mousedown', onDown);
    window.addEventListener('mouseup', onUp);
    return () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mousedown', onDown);
      window.removeEventListener('mouseup', onUp);
    };
  }, [enabled]);

  if (!enabled) return null;

  return (
    <div
      aria-hidden="true"
      className={`theme-cursor ${down ? 'is-down' : ''}`}
      style={{
        transform: `translate(${point.x}px, ${point.y}px) translate(-50%, -50%)`,
      }}
    />
  );
}
