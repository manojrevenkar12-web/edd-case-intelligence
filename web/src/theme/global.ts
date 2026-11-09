import { breakpoint, color, font, layout, radius, space, stroke } from "./tokens";

export const globalCss = `
*,*::before,*::after{box-sizing:border-box}
body{margin:0;background:${color.page};color:${color.ink};font-family:${font.body};font-size:${font.size.md}px;line-height:${font.leading.body}}
h1,h2,h3{margin:0;font-family:${font.serif};font-weight:${font.weight.semibold};line-height:${font.leading.tight}}
p{margin:0}
:focus-visible{outline:${stroke.focus}px solid ${color.focus};outline-offset:2px}
.page{max-width:${layout.maxWidth}px;margin:0 auto;padding:${space[10]}px ${space[6]}px ${space[16]}px}
.measure{max-width:${layout.measure}ch}
.ink2{color:${color.ink2}}
.muted{color:${color.muted}}
.num{font-variant-numeric:tabular-nums}
.section{margin-top:${space[12]}px}
.section h2{font-size:${font.size.xl}px;margin-bottom:${space[2]}px}
.lede{font-size:${font.size.lg}px;color:${color.ink2};margin-top:${space[3]}px}
.board{background:${color.card};border:${stroke.hair}px solid ${color.rule};border-radius:${radius.md}px;padding:${space[6]}px;margin-top:${space[4]}px}
.figures{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:${space[6]}px}
.figure strong{display:block;font-family:${font.serif};font-size:${font.size.xxxl}px;font-weight:${font.weight.semibold};line-height:${font.leading.tight};font-variant-numeric:tabular-nums}
.chips{display:flex;flex-wrap:wrap;gap:${space[2]}px;margin-bottom:${space[4]}px}
.chip{appearance:none;font:inherit;font-size:${font.size.sm}px;border:${stroke.hair}px solid ${color.rule};background:${color.card};color:${color.ink2};border-radius:${radius.md}px;padding:${space[1]}px ${space[3]}px;cursor:pointer}
.chip[aria-pressed="true"]{border-color:${color.ink};color:${color.ink}}
.btn{appearance:none;font:inherit;font-size:${font.size.sm}px;border:${stroke.hair}px solid ${color.ink};background:${color.card};border-radius:${radius.md}px;padding:${space[1]}px ${space[4]}px;cursor:pointer;align-self:flex-start}
.state{display:flex;flex-direction:column;gap:${space[2]}px;padding:${space[6]}px;border:${stroke.hair}px dashed ${color.rule};border-radius:${radius.md}px;background:${color.card}}
.skeleton{background:linear-gradient(90deg,${color.rule}55,${color.rule}aa,${color.rule}55);background-size:200% 100%;animation:shimmer 1.4s linear infinite;border-radius:${radius.sm}px}
@keyframes shimmer{to{background-position:-200% 0}}
.legend{display:flex;flex-wrap:wrap;gap:${space[4]}px;font-size:${font.size.sm}px;color:${color.ink2};margin-top:${space[3]}px}
.table{width:100%;border-collapse:collapse;font-size:${font.size.sm}px}
.table th,.table td{text-align:left;padding:${space[2]}px;border-bottom:${stroke.hair}px solid ${color.rule};vertical-align:top}
.table .r{text-align:right}
@media (max-width:${breakpoint.narrow}px){.page{padding:${space[6]}px ${space[4]}px}}
@media (prefers-reduced-motion:reduce){.skeleton{animation:none}}
`;
