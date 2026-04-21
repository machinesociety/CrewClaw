type ArtMode = 'idle' | 'email' | 'password' | 'password-visible' | 'error';

function Eye({
  closed = false,
  dot = false,
  offsetX = 0,
  offsetY = 0,
}: {
  closed?: boolean;
  dot?: boolean;
  offsetX?: number;
  offsetY?: number;
}) {
  return (
    <span className={`login-art-eye ${closed ? 'is-closed' : ''} ${dot ? 'dot' : ''}`}>
      {!closed && (
        <span
          className="login-art-pupil"
          style={{ transform: `translate(${offsetX}px, ${offsetY}px)` }}
        />
      )}
    </span>
  );
}

export default function AnimatedLoginArt({
  mode,
  pointer,
}: {
  mode: ArtMode;
  pointer: { x: number; y: number };
}) {
  const eyeX = Math.max(-4, Math.min(4, (pointer.x - 0.5) * 10));
  const eyeY = Math.max(-3, Math.min(3, (pointer.y - 0.5) * 8));
  const purpleClosed = mode === 'password';
  const orangeSad = mode === 'error';

  return (
    <div
      className="login-art-stage"
      style={mode === 'error' ? { animation: 'loginArtShake 320ms ease-in-out' } : undefined}
    >
      <div className="login-art-character purple">
        <div className="login-art-face">
          <Eye closed={purpleClosed} offsetX={eyeX} offsetY={eyeY} />
          <Eye closed={purpleClosed} offsetX={eyeX} offsetY={eyeY} />
        </div>
        <div className={`login-art-mouth ${mode === 'password-visible' ? 'flat' : ''}`} />
      </div>

      <div className="login-art-character black">
        <div className="login-art-face">
          <Eye offsetX={eyeX} offsetY={eyeY} />
          <Eye offsetX={eyeX} offsetY={eyeY} />
        </div>
        <div className="login-art-mouth flat" />
      </div>

      <div className="login-art-character orange">
        <div className="login-art-face">
          <Eye offsetX={eyeX} offsetY={eyeY} />
          <Eye offsetX={eyeX} offsetY={eyeY} />
        </div>
        <div className={`login-art-mouth ${orangeSad ? 'sad' : ''}`} />
      </div>

      <div className="login-art-character yellow">
        <div className="login-art-face">
          <Eye dot offsetX={eyeX} offsetY={eyeY} />
          <Eye dot offsetX={eyeX} offsetY={eyeY} />
        </div>
        <div className="login-art-mouth flat" />
      </div>
    </div>
  );
}
