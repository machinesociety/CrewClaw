import { useEffect, useMemo, useState } from 'react';
import type { CSSProperties } from 'react';

type LoginArtMode = 'idle' | 'email' | 'password' | 'password-visible' | 'error';

interface AnimatedLoginArtProps {
  mode: LoginArtMode;
  pointer: { x: number; y: number };
}

function Eye({
  dx,
  dy,
  closed = false,
  variant = 'default',
  style = {},
}: {
  dx: number;
  dy: number;
  closed?: boolean;
  variant?: 'default' | 'dot';
  style?: CSSProperties;
}) {
  return (
    <div className={`login-art-eye ${variant} ${closed ? 'is-closed' : ''}`} style={style}>
      {!closed && (
        <span
          className="login-art-pupil"
          style={{ transform: `translate(${dx}px, ${dy}px)` }}
        />
      )}
    </div>
  );
}

export default function AnimatedLoginArt({ mode, pointer }: AnimatedLoginArtProps) {
  const [blink, setBlink] = useState(false);
  const [peek, setPeek] = useState(false);

  useEffect(() => {
    const nextBlink = () => 1800 + Math.random() * 2600;
    const timer = window.setInterval(() => {
      setBlink(true);
      window.setTimeout(() => setBlink(false), 140);
    }, nextBlink());
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    if (mode !== 'password-visible') {
      setPeek(false);
      return;
    }
    const timer = window.setInterval(() => {
      setPeek((v: boolean) => !v);
    }, 900);
    return () => window.clearInterval(timer);
  }, [mode]);

  const eyeOffset = useMemo(() => {
    // 增加眼睛跟随的幅度
    const x = (pointer.x - 0.5) * 12;
    const y = (pointer.y - 0.5) * 10;
    return { x: Math.max(-6, Math.min(6, x)), y: Math.max(-4, Math.min(4, y)) };
  }, [pointer.x, pointer.y]);

  const isError = mode === 'error';
  const isPassword = mode === 'password';
  const isPwdVisible = mode === 'password-visible';
  const isEmail = mode === 'email';
  const isTyping = isEmail || isPassword || isPwdVisible; // 是否正在输入
  const closeEyes = blink || isPassword;

  // 计算光标距离中心的距离，用于身子拉伸 (scaleY)
  const dxFromCenter = pointer.x - 0.5;
  const dyFromCenter = pointer.y - 0.5;
  const distance = Math.sqrt(dxFromCenter * dxFromCenter + dyFromCenter * dyFromCenter);

  // 倾斜角度：使用 skewX 而非 rotate，这样底座底部会始终保持水平，不会翘起
  // 如果正在输入，重置为 0
  const skewAngle = isTyping ? 0 : Math.max(-10, Math.min(10, dxFromCenter * 35));

  // 拉伸比例：鼠标越远，拉伸越明显，最大 1.45
  // 如果正在输入，重置为 1
  const stretchFactor = isTyping ? 1 : 1 + Math.min(0.45, distance * 1.2);
  // 为了让动画更有“果冻感”，增加一个反向的 X 轴缩放 (Squash and Stretch)
  const squashFactor = 1 / (Math.sqrt(stretchFactor) || 1);

  const getCharStyle = (baseScale: number): CSSProperties => ({
    // 使用 skewX 保证底座平齐，scaleY 拉伸，scaleX 挤压
    transform: `skewX(${-skewAngle}deg) scaleY(${stretchFactor * baseScale}) scaleX(${squashFactor})`,
    transformOrigin: 'bottom center',
    transition: `transform 220ms cubic-bezier(0.175, 0.885, 0.32, 1.275)`, // 增加一点弹性
  });

  const getFaceStyle = (tiltFactor: number = 1): CSSProperties => ({
    // 脸部需要反向 skew 以抵消身体的 skew，防止五官变形
    // 使用 100% 的补偿以确保眼睛始终是正圆
    transform: `skewX(${skewAngle}deg) scaleX(${1 / squashFactor})`,
    transformOrigin: 'center center',
  });

  const getEyeCompensationStyle = (baseScale: number): CSSProperties => {
    const charScaleY = Math.max(0.1, stretchFactor * baseScale);
    return {
      // 只需要补偿 Y 轴拉伸，因为 X 轴和斜切已经在 Face 级别补偿过了
      transform: `scaleY(${1 / charScaleY})`,
      transformOrigin: 'center center',
    };
  };

  // 眼睛位置微调
  const getEyePos = (charDx: number) => {
    const dx = isPassword ? -4 : isPwdVisible ? 4 : eyeOffset.x + charDx;
    const dy = isPassword ? -1 : isPwdVisible ? -2 : eyeOffset.y;
    return { dx, dy };
  };

  return (
    <div className={`login-art-stage ${isError ? 'is-error' : ''}`}>
      {/* 紫色：最后面，最高 */}
      <div className="login-art-character purple" style={getCharStyle(1.1)}>
        <div className="login-art-face" style={getFaceStyle(1)}>
          <Eye {...getEyePos(-1)} closed={closeEyes} style={getEyeCompensationStyle(1.1)} />
          <Eye {...getEyePos(-1)} closed={closeEyes} style={getEyeCompensationStyle(1.1)} />
        </div>
      </div>

      {/* 黑色：中间 */}
      <div className="login-art-character black" style={getCharStyle(0.95)}>
        <div className="login-art-face" style={getFaceStyle(0.8)}>
          <Eye
            dx={(isPassword || isPwdVisible) ? -5 : getEyePos(1).dx}
            dy={(isPassword || isPwdVisible) ? -3 : getEyePos(1).dy}
            closed={blink} /* 黑色小人在输入密码时不闭眼，只看左上 */
            style={getEyeCompensationStyle(0.95)}
          />
          <Eye
            dx={(isPassword || isPwdVisible) ? -5 : getEyePos(1).dx}
            dy={(isPassword || isPwdVisible) ? -3 : getEyePos(1).dy}
            closed={blink}
            style={getEyeCompensationStyle(0.95)}
          />
        </div>
      </div>

      {/* 橙色：前面，最宽 */}
      <div className="login-art-character orange" style={getCharStyle(0.75)}>
        <div className="login-art-face" style={getFaceStyle(0.6)}>
          <Eye {...getEyePos(0)} closed={closeEyes} style={getEyeCompensationStyle(0.75)} />
          <Eye {...getEyePos(0)} closed={closeEyes} style={getEyeCompensationStyle(0.75)} />
        </div>
        <div className="login-art-mouth smile" />
      </div>

      {/* 黄色：最前面 */}
      <div className="login-art-character yellow" style={getCharStyle(0.85)}>
        <div className="login-art-face" style={getFaceStyle(0.5)}>
          <Eye
            dx={isPwdVisible && peek ? 3 : getEyePos(0).dx}
            dy={isPwdVisible ? 1 : getEyePos(0).dy}
            closed={closeEyes && !peek}
            variant="dot"
            style={getEyeCompensationStyle(0.85)}
          />
          <Eye
            dx={isPwdVisible && peek ? 3 : getEyePos(0).dx}
            dy={isPwdVisible ? 1 : getEyePos(0).dy}
            closed={closeEyes && !peek}
            variant="dot"
            style={getEyeCompensationStyle(0.85)}
          />
        </div>
        <div className="login-art-mouth flat" />
      </div>
    </div>
  );
}
