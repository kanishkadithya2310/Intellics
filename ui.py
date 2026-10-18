SIDEBAR_CSS = """<style>
[data-testid="stSidebar"]{background:rgba(10,15,31,.94);border-right:1px solid rgba(255,255,255,.08)}
[data-testid="stSidebar"] [role="radiogroup"]{gap:6px}

/* each section = one row */
[data-testid="stSidebar"] [role="radiogroup"] label{
  --c:#5eead4;
  position:relative;display:flex;align-items:center;gap:12px;width:100%;
  padding:11px 14px;border-radius:12px;cursor:pointer;
  border:1px solid transparent;
  transition:background .2s ease,border-color .2s ease,transform .15s ease}
[data-testid="stSidebar"] [role="radiogroup"] label:hover{background:rgba(255,255,255,.07);transform:translateX(2px)}

/* hide the old radio circle and the native input (kept in the DOM so clicks and keyboard still work) */
[data-testid="stSidebar"] [role="radiogroup"] label > :not(:last-child){
  position:absolute!important;opacity:0!important;width:0!important;height:0!important;
  margin:0!important;padding:0!important;pointer-events:none}

/* light, OFF: a dim glass bead */
[data-testid="stSidebar"] [role="radiogroup"] label::before{
  content:"";flex:none;width:9px;height:9px;border-radius:50%;
  background:rgba(255,255,255,.14);
  box-shadow:inset 0 0 0 1px rgba(255,255,255,.22);
  transition:background .25s ease,box-shadow .25s ease}

/* light, ON: same neon glow as the header light */
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){
  background:linear-gradient(120deg,rgba(94,234,212,.14),rgba(109,74,255,.26));
  border-color:rgba(94,234,212,.28)}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked)::before{
  background:radial-gradient(circle at 50% 50%,#fff 0,var(--c) 45%,var(--c) 100%);
  box-shadow:0 0 2px #fff,0 0 5px var(--c),0 0 10px var(--c),0 0 18px var(--c),
             0 0 30px color-mix(in srgb,var(--c) 65%,transparent);
  animation:navpulse 2.4s ease-in-out infinite}
@keyframes navpulse{
  0%,100%{box-shadow:0 0 2px #fff,0 0 5px var(--c),0 0 10px var(--c),0 0 18px var(--c),0 0 30px color-mix(in srgb,var(--c) 65%,transparent)}
  50%{box-shadow:0 0 2px #fff,0 0 4px var(--c),0 0 7px var(--c),0 0 12px var(--c),0 0 18px color-mix(in srgb,var(--c) 45%,transparent)}}

/* keyboard focus */
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:focus-visible){outline:3px solid #67e8f9;outline-offset:2px}

[data-testid="stSidebar"] [role="radiogroup"] label p{font-weight:600;font-size:1rem;margin:0}
.side-brand{font-weight:800;letter-spacing:.1em;font-size:1.1rem;margin:.2rem 0 .8rem}
.side-brand small{display:block;font-weight:400;letter-spacing:.02em;opacity:.7;font-size:.75rem}

@media (prefers-reduced-motion:reduce){
  [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked)::before{animation:none}
  [data-testid="stSidebar"] [role="radiogroup"] label{transition:none}}
</style>"""
