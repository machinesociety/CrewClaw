import { useEffect, useState } from 'react';

export default function ThemeCursor() {
  const [mounted, setMounted] = useState(false);
  const [point, setPoint] = useState({ x: 0, y: 0 });
  const [down, setDown] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia('(pointer: fine)').matches) {
      return;
    }
    setMounted(true);

    const onMove = (event: MouseEvent) => setPoint({ x: event.clientX, y: event.clientY });
    const onDown = () => setDown(true);
    const onUp = () => setDown(false);

    window.addEventListener('mousemove', onMove);
    window.addEventListener('mousedown', onDown);
    window.addEventListener('mouseup', onUp);

    return () => {
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mousedown', onDown);
      window.removeEventListener('mouseup', onUp);
    };
  }, []);

  if (!mounted) return null;

  return (
    <div
      className={`theme-cursor ${down ? 'is-down' : ''}`}
      style={{ transform: `translate(${point.x - 8}px, ${point.y - 8}px)` }}
    />
  );
}
