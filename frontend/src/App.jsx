import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence, animate } from "framer-motion";
import { Loader2, ArrowRight, AlertTriangle, Sparkle } from "lucide-react";

// ---------------------------------------------------------------------------
// Design tokens — warm cream base, layered organic blobs, soft pastel accents.
// No build step here, so custom colors are applied via inline style rather
// than a Tailwind config.
// ---------------------------------------------------------------------------
const T = {
  bg: "#F1584F",
  card: "#FFFFFF",
  panel: "#FBE8D9",
  ink: "#231F35",
  inkSoft: "#736C87",
  inkFaint: "#B3ACC4",
  navy: "#241F3D",
  lavender: "#B9B4DE",
  sage: "#A9BB99",
  blush: "#EFB8B3",
  gold: "#F2A93B",
  teal: "#2FBFA0",
  purple: "#8D7FEA",
  low: "#E2867B",
  mid: "#E6B84D",
  high: "#8CB27C",
};

const fontDisplay = "'Baloo 2', sans-serif";
const fontBody = "'DM Sans', sans-serif";

function scoreToColor(score) {
  const stops = [
    { at: 0, c: [226, 134, 123] },
    { at: 50, c: [230, 184, 77] },
    { at: 100, c: [140, 178, 124] },
  ];
  const clamped = Math.max(0, Math.min(100, score));
  let a = stops[0],
      b = stops[1];
  if (clamped > 50) {
    a = stops[1];
    b = stops[2];
  }
  const span = b.at - a.at || 1;
  const t = (clamped - a.at) / span;
  const rgb = a.c.map((v, i) => Math.round(v + (b.c[i] - v) * t));
  return `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`;
}

function scoreToLabel(score) {
  if (score < 40) return "Needs work";
  if (score < 70) return "Getting there";
  return "Great fit";
}

// Two hand-tuned organic blob paths, reused at different scales, rotations
// and colors throughout — this overlapping-blob field is the page's one
// signature, recurring motif instead of decoration bolted on once.
const BLOB_A =
    "M39.9,-65.7C52.8,-59.4,65.2,-51.1,72.7,-39.2C80.2,-27.3,82.8,-11.8,80.6,2.7C78.4,17.2,71.4,30.7,62.1,42.3C52.8,53.9,41.2,63.6,27.9,69.5C14.6,75.4,-0.4,77.5,-15.4,75.3C-30.4,73.1,-45.4,66.6,-56.9,56C-68.4,45.4,-76.4,30.7,-79.5,14.8C-82.6,-1.1,-80.8,-18.2,-73.6,-32.5C-66.4,-46.8,-53.8,-58.3,-40,-64.8C-26.2,-71.3,-13.1,-72.8,0.5,-73.6C14.1,-74.4,28.2,-74.5,39.9,-65.7Z";
const BLOB_B =
    "M42.8,-71.5C54.9,-63.6,63.6,-50.1,69.9,-35.8C76.2,-21.5,80.1,-6.4,78.4,8C76.7,22.4,69.4,36.1,59.4,47.6C49.4,59.1,36.7,68.4,22.4,73.2C8.1,78,-7.8,78.3,-22.6,74.2C-37.4,70.1,-51.1,61.6,-61.4,49.8C-71.7,38,-78.6,22.9,-80.4,7C-82.2,-8.9,-78.9,-25.6,-70.6,-39.4C-62.3,-53.2,-49,-64.1,-34.9,-71.4C-20.8,-78.7,-6,-82.4,7.7,-80.6C21.4,-78.8,30.7,-79.4,42.8,-71.5Z";

function Blob({ path = BLOB_A, color, size = 400, style = {}, opacity = 1, drift = false }) {
  return (
      <motion.svg
          viewBox="-100 -100 200 200"
          width={size}
          height={size}
          className="pointer-events-none absolute"
          style={{ opacity, ...style }}
          animate={drift ? { rotate: [0, 8, 0, -8, 0], scale: [1, 1.04, 1, 0.98, 1] } : undefined}
          transition={drift ? { duration: 22, repeat: Infinity, ease: "easeInOut" } : undefined}
      >
        <path d={path} fill={color} />
      </motion.svg>
  );
}

// A flat-vector "device showcase" — a monitor with a UI on screen, surrounded
// by tilted mockup cards, echoing the reference's isometric monitor-plus-
// scattered-template-cards composition, redrawn in this page's own palette.
function MonitorIllustration({ size = 260, style = {} }) {
  return (
      <motion.div
          className="absolute"
          style={{ width: size, ...style }}
          initial={{ opacity: 0, scale: 0.92, y: 12 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.15, ease: [0.16, 1, 0.3, 1] }}
      >
        <svg viewBox="0 0 260 210" width="100%" height="auto">
          <ellipse cx="130" cy="196" rx="76" ry="9" fill="#1A1730" opacity="0.15" />
          <rect x="20" y="8" width="220" height="150" rx="16" fill={T.navy} />
          <rect x="33" y="21" width="194" height="124" rx="8" fill="#171633" />
          <rect x="46" y="34" width="88" height="11" rx="5.5" fill={T.gold} />
          <rect x="46" y="53" width="128" height="6" rx="3" fill="#494672" />
          <rect x="46" y="65" width="98" height="6" rx="3" fill="#494672" />
          <rect x="46" y="86" width="58" height="36" rx="8" fill={T.teal} />
          <rect x="112" y="86" width="58" height="36" rx="8" fill={T.purple} />
          <rect x="46" y="128" width="124" height="9" rx="4.5" fill={T.gold} opacity="0.85" />
          <rect x="118" y="158" width="24" height="18" fill={T.navy} />
          <rect x="90" y="176" width="80" height="10" rx="5" fill={T.navy} />
        </svg>
      </motion.div>
  );
}

// A single tilted "template preview" card — a color header band over a few
// text lines, floating and drifting slowly.
function MockupCard({ color, width = 112, height = 82, rotate = 0, style = {}, delay = 0 }) {
  return (
      <motion.div
          className="absolute overflow-hidden rounded-xl"
          style={{ width, height, background: "#FFFFFF", boxShadow: "0 16px 30px -12px rgba(26, 23, 48, 0.4)", ...style }}
          initial={{ opacity: 0, y: 14, rotate: rotate - 6 }}
          animate={{ opacity: 1, y: [0, -10, 0], rotate: [rotate - 3, rotate + 3, rotate - 3] }}
          transition={{
            opacity: { duration: 0.6, delay },
            y: { duration: 5, repeat: Infinity, ease: "easeInOut", delay },
            rotate: { duration: 7, repeat: Infinity, ease: "easeInOut", delay },
          }}
      >
        <div style={{ height: "36%", background: color }} />
        <div className="flex flex-col gap-1.5 p-2.5">
          <div style={{ height: 5, width: "72%", borderRadius: 3, background: "#E7E2D6" }} />
          <div style={{ height: 5, width: "52%", borderRadius: 3, background: "#EFEAE0" }} />
          <div style={{ marginTop: 3, height: 14, width: "58%", borderRadius: 7, background: color, opacity: 0.18 }} />
        </div>
      </motion.div>
  );
}

// Composes the monitor with three orbiting mockup cards into one scene,
// with the whole group breathing gently so it never looks static.
function DeviceShowcase({ style = {} }) {
  return (
      <motion.div
          className="relative"
          style={{ width: 340, height: 300, ...style }}
          animate={{ y: [0, -8, 0] }}
          transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
      >
        <MonitorIllustration size={260} style={{ top: 30, left: 30 }} />
        <MockupCard color={T.teal} width={104} height={78} rotate={-9} style={{ top: 0, left: -14 }} delay={0.25} />
        <MockupCard color={T.purple} width={98} height={72} rotate={11} style={{ bottom: 4, left: 6 }} delay={0.55} />
        <MockupCard color={T.gold} width={100} height={74} rotate={-7} style={{ bottom: 30, right: -18 }} delay={0.4} />
      </motion.div>
  );
}

// ---------------------------------------------------------------------------
// Input card
// ---------------------------------------------------------------------------
function Channel({ tag, tagColor, placeholder, value, onChange }) {
  return (
      <div
          className="group relative flex-1 rounded-[28px] p-6 transition-all duration-300 ease-out focus-within:-translate-y-1 hover:-translate-y-0.5"
          style={{
            background: T.panel,
            boxShadow: "0 18px 40px -20px rgba(35, 31, 53, 0.25)",
          }}
      >
        <div
            className="pointer-events-none absolute inset-0 rounded-[28px] opacity-0 transition-opacity duration-300 group-focus-within:opacity-100"
            style={{ boxShadow: `0 0 0 2.5px ${tagColor}55, 0 22px 46px -20px rgba(35, 31, 53, 0.35)` }}
        />
        <div className="relative mb-3 flex items-center justify-between">
        <span
            className="rounded-full px-3 py-1 text-[12px] font-semibold"
            style={{ fontFamily: fontBody, background: `${tagColor}22`, color: tagColor }}
        >
          {tag}
        </span>
          <span className="text-[12px]" style={{ fontFamily: fontBody, color: T.inkFaint }}>
          {value.length} chars
        </span>
        </div>
        <textarea
            value={value}
            onChange={onChange}
            placeholder={placeholder}
            spellCheck={false}
            className="relative min-h-[300px] w-full resize-none bg-transparent outline-none placeholder:opacity-50 focus-visible:outline-none"
            style={{ fontFamily: fontBody, fontSize: "14px", lineHeight: 1.65, color: T.ink }}
        />
      </div>
  );
}

// ---------------------------------------------------------------------------
// Radial gauge
// ---------------------------------------------------------------------------
function ScoreGauge({ score }) {
  const [display, setDisplay] = useState(0);
  const size = 176;
  const stroke = 14;
  const r = (size - stroke) / 2;
  const circumference = 2 * Math.PI * r;

  useEffect(() => {
    const controls = animate(0, score, {
      duration: 1.5,
      ease: [0.16, 1, 0.3, 1],
      onUpdate: (v) => setDisplay(v),
    });
    return () => controls.stop();
  }, [score]);

  const color = scoreToColor(display);
  const offset = circumference * (1 - display / 100);

  return (
      <div className="relative flex-shrink-0" style={{ width: size, height: size }}>
        <motion.div
            className="absolute inset-0 rounded-full"
            style={{ background: color, filter: "blur(22px)" }}
            animate={{ opacity: [0.15, 0.35, 0.15] }}
            transition={{ duration: 2.6, repeat: Infinity, ease: "easeInOut" }}
        />
        <svg width={size} height={size} className="relative -rotate-90">
          <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#F0D4B8" strokeWidth={stroke} />
          <circle
              cx={size / 2}
              cy={size / 2}
              r={r}
              fill="none"
              stroke={color}
              strokeWidth={stroke}
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={offset}
              style={{ transition: "stroke 0.3s linear" }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span style={{ fontFamily: fontDisplay, fontSize: "36px", fontWeight: 700, color }}>
          {display.toFixed(0)}
        </span>
          <span className="text-[11px] font-medium" style={{ fontFamily: fontBody, color: T.inkSoft }}>
          match score
        </span>
        </div>
      </div>
  );
}

function KeywordPill({ label, index }) {
  const palette = [T.low, T.gold, T.navy, T.sage];
  const color = palette[index % palette.length];
  return (
      <motion.span
          initial={{ opacity: 0, y: 10, scale: 0.9 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          whileHover={{ scale: 1.08, y: -2 }}
          transition={{ delay: 0.5 + index * 0.06, duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
          className="cursor-default rounded-full px-3.5 py-1.5 text-[13px] font-medium"
          style={{ fontFamily: fontBody, color, background: `${color}1A` }}
      >
        {label}
      </motion.span>
  );
}

// ---------------------------------------------------------------------------
// Root
// ---------------------------------------------------------------------------
export default function SkillSync() {
  const [resumeText, setResumeText] = useState("");
  const [jdText, setJdText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const resultsRef = useRef(null);

  const canAnalyze = resumeText.trim().length > 0 && jdText.trim().length > 0 && !isLoading;

  async function handleAnalyze() {
    if (!canAnalyze) return;
    setIsLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch("http://127.0.0.1:5000/match", {
        method: "POST",
        mode: "cors",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resume_text: resumeText, jd_text: jdText }),
      });
      if (!res.ok) throw new Error(`Server responded with ${res.status}`);
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(
          err instanceof TypeError
              ? "Can't reach the backend. Make sure it's running on http://127.0.0.1:5000 and has CORS enabled."
              : err.message || "Something went wrong while analyzing."
      );
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    if (result && resultsRef.current) {
      resultsRef.current.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, [result]);

  return (
      <div className="relative min-h-screen w-full overflow-hidden px-4 py-16 sm:px-8" style={{ background: T.bg, fontFamily: fontBody }}>
        <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;700;800&family=DM+Sans:wght@400;500;600;700&display=swap');
        textarea::-webkit-scrollbar { width: 6px; }
        textarea::-webkit-scrollbar-thumb { background: #E6E0D2; border-radius: 4px; }
      `}</style>

        {/* Subtle depth blob, kept low-key so the flat coral reads clean like the reference */}
        <div className="absolute inset-x-0 top-0 h-[560px] overflow-hidden" style={{ zIndex: 0 }}>
          <Blob path={BLOB_B} color="#DD4E46" size={520} opacity={0.5} style={{ top: -220, left: "-8%" }} drift />
        </div>

        <div className="relative mx-auto max-w-5xl" style={{ zIndex: 1 }}>
          {/* Header */}
          <motion.header
              initial={{ opacity: 0, y: -12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
              className="mb-14 flex flex-col items-center gap-10 pt-6 text-center md:flex-row md:items-center md:justify-between md:text-left"
          >
            <div className="flex flex-col items-center md:items-start">
              <div className="mb-5 flex items-center gap-2">
              <span
                  className="flex h-9 w-9 items-center justify-center rounded-full"
                  style={{ background: T.navy }}
              >
                <Sparkle size={16} color={T.gold} strokeWidth={2.5} />
              </span>
                <span style={{ fontFamily: fontDisplay, fontSize: "20px", fontWeight: 700, color: T.card }}>
                SkillSync
              </span>
              </div>
              <h1
                  className="max-w-lg text-4xl leading-tight sm:text-5xl"
                  style={{ fontFamily: fontDisplay, fontWeight: 800, color: T.card, letterSpacing: "-0.01em" }}
              >
                It's so simple.
              </h1>
              <p className="mt-3 max-w-sm text-[15px]" style={{ color: "rgba(255,255,255,0.85)" }}>
                Paste a resume and a job description below, and see how well they line up.
              </p>
            </div>

            <div className="-mb-24 flex w-full shrink-0 justify-center sm:-mb-8 md:mb-0 md:w-auto md:justify-start">
              <div className="scale-[0.68] origin-top sm:scale-90 md:scale-100">
                <DeviceShowcase />
              </div>
            </div>
          </motion.header>

          {/* Input channels */}
          <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
              className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full"
          >
            <Channel
                tag="Resume"
                tagColor={T.navy}
                placeholder="Paste the candidate's resume text here…"
                value={resumeText}
                onChange={(e) => setResumeText(e.target.value)}
            />
            <Channel
                tag="Job description"
                tagColor={T.gold}
                placeholder="Paste the target job description here…"
                value={jdText}
                onChange={(e) => setJdText(e.target.value)}
            />
          </motion.div>

          {/* Action */}
          <div className="mt-9 flex flex-col items-center">
            <motion.button
                onClick={handleAnalyze}
                disabled={!canAnalyze}
                whileHover={canAnalyze ? { scale: 1.04 } : {}}
                whileTap={canAnalyze ? { scale: 0.96 } : {}}
                animate={
                  canAnalyze
                      ? { boxShadow: ["0 14px 30px -12px rgba(43,42,76,0.55)", "0 14px 34px -8px rgba(43,42,76,0.75)", "0 14px 30px -12px rgba(43,42,76,0.55)"] }
                      : {}
                }
                transition={canAnalyze ? { boxShadow: { duration: 2.4, repeat: Infinity, ease: "easeInOut" } } : {}}
                className="group relative flex items-center gap-2 overflow-hidden rounded-full px-7 py-3.5 text-[15px] font-semibold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2"
                style={{
                  fontFamily: fontBody,
                  background: canAnalyze ? T.navy : "#E4DFD2",
                  color: canAnalyze ? T.card : T.inkFaint,
                  cursor: canAnalyze ? "pointer" : "not-allowed",
                  outlineColor: T.navy,
                }}
            >
              {canAnalyze && (
                  <span
                      className="pointer-events-none absolute inset-y-0 -left-1/2 w-1/2 -skew-x-12 bg-white/25 opacity-0 transition-all duration-700 ease-out group-hover:left-full group-hover:opacity-100"
                  />
              )}
              {isLoading ? (
                  <>
                    <Loader2 size={17} className="animate-spin" />
                    Analyzing…
                  </>
              ) : (
                  <>
                    Analyze compatibility
                    <motion.span className="flex" whileHover={{ x: 3 }} transition={{ duration: 0.2 }}>
                      <ArrowRight size={17} />
                    </motion.span>
                  </>
              )}
            </motion.button>

            <AnimatePresence>
              {error && (
                  <motion.div
                      initial={{ opacity: 0, y: -6 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -6 }}
                      className="mt-5 flex max-w-md items-start gap-2.5 rounded-2xl px-4 py-3 text-sm"
                      style={{ background: `${T.low}18`, color: "#B24A3E" }}
                  >
                    <AlertTriangle size={16} className="mt-0.5 flex-shrink-0" />
                    <span>{error}</span>
                  </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Results */}
          <AnimatePresence>
            {result && (
                <motion.div
                    ref={resultsRef}
                    initial={{ opacity: 0, y: 24 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 24 }}
                    transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
                    className="relative mt-12 overflow-hidden rounded-[32px] p-8"
                    style={{ background: T.panel, boxShadow: "0 24px 60px -24px rgba(35, 31, 53, 0.3)" }}
                >
                  <Blob path={BLOB_A} color={T.blush} size={180} opacity={0.35} style={{ bottom: -70, right: -50, mixBlendMode: "multiply" }} />

                  <div className="relative flex flex-col items-center gap-8 sm:flex-row sm:items-start sm:justify-between">
                    <div className="flex flex-col items-center">
                      <ScoreGauge score={result.match_score} />
                      <span
                          className="mt-3 rounded-full px-3 py-1 text-[12px] font-semibold"
                          style={{
                            fontFamily: fontBody,
                            color: scoreToColor(result.match_score),
                            background: `${scoreToColor(result.match_score)}18`,
                          }}
                      >
                    {scoreToLabel(result.match_score)}
                  </span>
                    </div>

                    <div className="w-full flex-1">
                  <span className="text-[13px] font-semibold" style={{ fontFamily: fontBody, color: T.ink }}>
                    Missing keywords
                  </span>
                      {result.missing_keywords && result.missing_keywords.length > 0 ? (
                          <div className="mt-4 flex flex-wrap gap-2">
                            {result.missing_keywords.map((kw, i) => (
                                <KeywordPill key={kw + i} label={kw} index={i} />
                            ))}
                          </div>
                      ) : (
                          <p className="mt-4 text-sm" style={{ color: T.inkSoft }}>
                            No gaps detected — full coverage.
                          </p>
                      )}
                    </div>
                  </div>
                </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
  );
}