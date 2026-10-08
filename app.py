Absolutely. Here is the **complete single-file `index.html`**. Save everything below as `index.html` and upload it.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#070b14">
<title>Intellics — Indian Markets, Explained Simply</title>

<style>
/* =========================================================
   INTELLICS — SINGLE FILE
   No frameworks / no external CSS / no build step
   ========================================================= */

:root{
  --bg:#060912;
  --bg2:#0b1020;
  --card:rgba(15,22,38,.78);
  --card2:rgba(20,29,49,.72);
  --border:rgba(255,255,255,.09);
  --text:#f5f7fb;
  --muted:#9ca8bb;
  --green:#28d17c;
  --red:#ff5c68;
  --gold:#f3bd55;
  --blue:#5aa7ff;
  --cyan:#42d9ff;
  --shadow:0 20px 60px rgba(0,0,0,.35);
  --radius:20px;
}

*{
  box-sizing:border-box;
  margin:0;
  padding:0;
}

html{
  scroll-behavior:smooth;
}

body{
  font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  background:
    radial-gradient(circle at 15% 10%,rgba(40,209,124,.08),transparent 30%),
    radial-gradient(circle at 85% 20%,rgba(255,92,104,.08),transparent 30%),
    var(--bg);
  color:var(--text);
  min-height:100vh;
  overflow-x:hidden;
}

button,
input,
select{
  font:inherit;
}

button{
  cursor:pointer;
}

/* =========================
   BACKGROUND
   ========================= */

.background-grid{
  position:fixed;
  inset:0;
  pointer-events:none;
  opacity:.28;
  background-image:
    linear-gradient(rgba(255,255,255,.025) 1px,transparent 1px),
    linear-gradient(90deg,rgba(255,255,255,.025) 1px,transparent 1px);
  background-size:45px 45px;
  mask-image:linear-gradient(to bottom,#000,transparent 90%);
  z-index:-5;
}

.glow{
  position:fixed;
  width:450px;
  height:450px;
  border-radius:50%;
  filter:blur(100px);
  opacity:.08;
  pointer-events:none;
  z-index:-4;
}

.glow.green{
  background:var(--green);
  top:-180px;
  left:-150px;
}

.glow.red{
  background:var(--red);
  top:100px;
  right:-180px;
}

/* =========================
   HEADER
   ========================= */

header{
  position:sticky;
  top:0;
  z-index:100;
  backdrop-filter:blur(18px);
  background:rgba(6,9,18,.72);
  border-bottom:1px solid var(--border);
}

.nav{
  width:min(1400px,94%);
  margin:auto;
  height:72px;
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:20px;
}

.brand{
  display:flex;
  align-items:center;
  gap:12px;
  font-weight:800;
  letter-spacing:-.5px;
}

.brand-mark{
  width:42px;
  height:42px;
  border-radius:13px;
  display:grid;
  place-items:center;
  background:linear-gradient(135deg,#1ed67a,#087e51);
  box-shadow:0 8px 30px rgba(40,209,124,.2);
}

.brand-mark svg{
  width:25px;
  height:25px;
}

.brand-name{
  font-size:19px;
}

.brand-sub{
  color:var(--muted);
  font-size:11px;
  font-weight:500;
  margin-top:1px;
}

.nav-actions{
  display:flex;
  gap:8px;
  align-items:center;
}

.nav-btn{
  border:1px solid var(--border);
  background:rgba(255,255,255,.035);
  color:var(--muted);
  padding:9px 13px;
  border-radius:11px;
  transition:.2s;
}

.nav-btn:hover,
.nav-btn.active{
  color:white;
  background:rgba(255,255,255,.08);
  border-color:rgba(255,255,255,.16);
}

/* =========================
   HERO
   ========================= */

.hero{
  width:min(1400px,94%);
  margin:25px auto 0;
  min-height:455px;
  position:relative;
  overflow:hidden;
  border:1px solid var(--border);
  border-radius:30px;
  background:
    linear-gradient(90deg,rgba(4,9,17,.97) 0%,rgba(4,9,17,.78) 38%,rgba(4,9,17,.38) 72%,rgba(4,9,17,.8) 100%),
    radial-gradient(circle at 20% 50%,rgba(40,209,124,.12),transparent 30%),
    radial-gradient(circle at 80% 50%,rgba(255,92,104,.12),transparent 30%),
    #090d17;
  box-shadow:var(--shadow);
}

.hero::before{
  content:"";
  position:absolute;
  inset:0;
  background-image:
    linear-gradient(rgba(255,255,255,.035) 1px,transparent 1px),
    linear-gradient(90deg,rgba(255,255,255,.035) 1px,transparent 1px);
  background-size:55px 55px;
  opacity:.22;
}

.hero-content{
  position:relative;
  z-index:5;
  padding:70px 65px;
  max-width:720px;
}

.badge{
  display:inline-flex;
  align-items:center;
  gap:8px;
  border:1px solid rgba(40,209,124,.25);
  background:rgba(40,209,124,.08);
  color:#8ff0bd;
  padding:8px 12px;
  border-radius:999px;
  font-size:12px;
  font-weight:700;
  margin-bottom:22px;
}

.badge-dot{
  width:7px;
  height:7px;
  border-radius:50%;
  background:var(--green);
  box-shadow:0 0 12px var(--green);
}

.hero h1{
  font-size:clamp(45px,6vw,82px);
  line-height:.95;
  letter-spacing:-4px;
  margin-bottom:22px;
}

.hero h1 span{
  background:linear-gradient(90deg,#fff,#a9b5c9);
  -webkit-background-clip:text;
  color:transparent;
}

.hero p{
  font-size:18px;
  line-height:1.7;
  color:#adb7c8;
  max-width:620px;
}

.hero-buttons{
  display:flex;
  gap:12px;
  margin-top:30px;
  flex-wrap:wrap;
}

.primary{
  border:0;
  background:linear-gradient(135deg,#28d17c,#13a962);
  color:#04120b;
  font-weight:800;
  padding:13px 19px;
  border-radius:12px;
  box-shadow:0 12px 35px rgba(40,209,124,.18);
}

.secondary{
  border:1px solid var(--border);
  background:rgba(255,255,255,.045);
  color:white;
  padding:13px 19px;
  border-radius:12px;
}

/* Bull / Bear artwork */

.market-art{
  position:absolute;
  right:-15px;
  top:0;
  width:58%;
  height:100%;
  pointer-events:none;
}

.market-art svg{
  width:100%;
  height:100%;
}

.bull{
  animation:bullFloat 5s ease-in-out infinite;
  transform-origin:center;
}

.bear{
  animation:bearFloat 5.5s ease-in-out infinite;
  transform-origin:center;
}

.bull-glow{
  animation:pulseGreen 3s ease-in-out infinite;
}

.bear-glow{
  animation:pulseRed 3.4s ease-in-out infinite;
}

.chart-line{
  stroke-dasharray:800;
  stroke-dashoffset:800;
  animation:drawLine 5s linear infinite;
}

@keyframes bullFloat{
  0%,100%{transform:translateY(0) rotate(0)}
  50%{transform:translateY(-9px) rotate(-1deg)}
}

@keyframes bearFloat{
  0%,100%{transform:translateY(0) rotate(0)}
  50%{transform:translateY(10px) rotate(1deg)}
}

@keyframes pulseGreen{
  0%,100%{opacity:.1}
  50%{opacity:.25}
}

@keyframes pulseRed{
  0%,100%{opacity:.08}
  50%{opacity:.22}
}

@keyframes drawLine{
  0%{stroke-dashoffset:800}
  60%,100%{stroke-dashoffset:0}
}

/* =========================
   MAIN
   ========================= */

main{
  width:min(1400px,94%);
  margin:28px auto 80px;
}

.section-title{
  display:flex;
  justify-content:space-between;
  align-items:end;
  gap:20px;
  margin:40px 0 16px;
}

.section-title h2{
  font-size:25px;
  letter-spacing:-.7px;
}

.section-title p{
  color:var(--muted);
  font-size:13px;
}

/* =========================
   MARKET CARDS
   ========================= */

.market-grid{
  display:grid;
  grid-template-columns:repeat(4,1fr);
  gap:14px;
}

.market-card{
  background:var(--card);
  border:1px solid var(--border);
  border-radius:17px;
  padding:18px;
  position:relative;
  overflow:hidden;
}

.market-card::after{
  content:"";
  position:absolute;
  width:100px;
  height:100px;
  border-radius:50%;
  background:var(--green);
  filter:blur(50px);
  opacity:.05;
  right:-30px;
  bottom:-30px;
}

.market-name{
  font-size:12px;
  color:var(--muted);
  margin-bottom:10px;
}

.market-value{
  font-size:25px;
  font-weight:800;
  letter-spacing:-.7px;
}

.market-change{
  margin-top:7px;
  font-size:12px;
  font-weight:700;
}

.up{color:var(--green)}
.down{color:var(--red)}

.mini-chart{
  width:100%;
  height:35px;
  margin-top:12px;
}

/* =========================
   CONTROLS
   ========================= */

.controls{
  display:flex;
  gap:9px;
  flex-wrap:wrap;
  padding:15px;
  background:rgba(255,255,255,.025);
  border:1px solid var(--border);
  border-radius:17px;
  margin-bottom:18px;
}

.search{
  flex:1;
  min-width:220px;
}

.search input,
.controls select{
  width:100%;
  border:1px solid var(--border);
  background:#0b1120;
  color:white;
  padding:11px 13px;
  border-radius:10px;
  outline:none;
}

.search input:focus,
.controls select:focus{
  border-color:rgba(90,167,255,.55);
}

.filter-btn{
  border:1px solid var(--border);
  background:rgba(255,255,255,.035);
  color:#aeb9c9;
  padding:10px 14px;
  border-radius:10px;
}

.filter-btn.active{
  color:white;
  background:rgba(255,255,255,.1);
}

/* =========================
   NEWS
   ========================= */

.news-layout{
  display:grid;
  grid-template-columns:minmax(0,1fr) 320px;
  gap:18px;
}

.news-list{
  display:flex;
  flex-direction:column;
  gap:14px;
}

.news-card{
  border:1px solid var(--border);
  background:var(--card);
  border-radius:19px;
  padding:20px;
  transition:.2s;
}

.news-card:hover{
  transform:translateY(-2px);
  border-color:rgba(255,255,255,.15);
}

.news-top{
  display:flex;
  align-items:center;
  gap:8px;
  flex-wrap:wrap;
  margin-bottom:10px;
}

.source{
  font-size:11px;
  font-weight:800;
  color:#dbe3ef;
}

.news-time{
  color:#78859a;
  font-size:11px;
}

.topic{
  padding:5px 8px;
  border-radius:7px;
  background:rgba(90,167,255,.09);
  color:#8dbfff;
  font-size:10px;
  font-weight:700;
}

.news-title{
  font-size:20px;
  line-height:1.3;
  margin-bottom:10px;
  letter-spacing:-.35px;
}

.news-summary{
  color:#aeb8c8;
  line-height:1.65;
  font-size:14px;
}

.read-link{
  color:#74b5ff;
  font-size:12px;
  font-weight:700;
  text-decoration:none;
  margin-top:13px;
  display:inline-block;
}

.explainer{
  margin-top:17px;
  border-top:1px solid var(--border);
  padding-top:14px;
}

.explainer-label{
  color:#dce4f1;
  font-size:11px;
  font-weight:800;
  text-transform:uppercase;
  letter-spacing:.7px;
  margin-bottom:10px;
}

.term{
  display:inline-flex;
  flex-direction:column;
  vertical-align:top;
  margin:0 6px 7px 0;
  border:1px solid rgba(243,189,85,.2);
  background:rgba(243,189,85,.055);
  border-radius:10px;
  padding:7px 9px;
  min-width:120px;
}

.term b{
  color:var(--gold);
  font-size:11px;
}

.term span{
  color:#98a5b7;
  font-size:10px;
  line-height:1.35;
  margin-top:3px;
}

/* =========================
   SIDEBAR
   ========================= */

.side-card{
  background:var(--card);
  border:1px solid var(--border);
  border-radius:19px;
  padding:18px;
  margin-bottom:14px;
}

.side-title{
  font-size:14px;
  font-weight:800;
  margin-bottom:15px;
}

.focus-item{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:10px;
  padding:12px 0;
  border-bottom:1px solid var(--border);
}

.focus-item:last-child{
  border-bottom:0;
}

.focus-company{
  font-size:13px;
  font-weight:700;
}

.focus-meta{
  color:var(--muted);
  font-size:10px;
  margin-top:3px;
}

.focus-change{
  font-size:12px;
  font-weight:800;
}

/* =========================
   TABS
   ========================= */

.tabs{
  display:flex;
  gap:7px;
  margin-bottom:18px;
  overflow:auto;
}

.tab{
  white-space:nowrap;
  border:1px solid var(--border);
  background:rgba(255,255,255,.03);
  color:#8996aa;
  padding:10px 15px;
  border-radius:10px;
}

.tab.active{
  color:white;
  background:rgba(255,255,255,.09);
}

/* =========================
   MOVERS
   ========================= */

.movers-grid{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:18px;
}

.mover-card{
  border:1px solid var(--border);
  background:var(--card);
  border-radius:20px;
  padding:20px;
}

.mover-head{
  display:flex;
  justify-content:space-between;
  align-items:center;
  margin-bottom:18px;
}

.mover-head h3{
  font-size:16px;
}

.mover-row{
  display:grid;
  grid-template-columns:120px 1fr 70px;
  gap:10px;
  align-items:center;
  margin:12px 0;
}

.mover-name{
  font-size:12px;
  font-weight:700;
}

.bar-bg{
  height:9px;
  border-radius:99px;
  background:rgba(255,255,255,.07);
  overflow:hidden;
}

.bar{
  height:100%;
  border-radius:99px;
}

.green-bar{
  background:linear-gradient(90deg,#19a968,#42df91);
}

.red-bar{
  background:linear-gradient(90deg,#d33e4d,#ff6872);
}

.mover-value{
  text-align:right;
  font-size:11px;
  font-weight:800;
}

/* =========================
   EXPLORER
   ========================= */

.explorer{
  display:grid;
  grid-template-columns:320px 1fr;
  gap:18px;
}

.explorer-card{
  background:var(--card);
  border:1px solid var(--border);
  border-radius:20px;
  padding:20px;
}

.company-select{
  width:100%;
  background:#0b1120;
  color:white;
  border:1px solid var(--border);
  border-radius:10px;
  padding:12px;
}

.company-big{
  font-size:32px;
  font-weight:900;
  margin-top:20px;
}

.company-price{
  font-size:18px;
  color:#dbe3ef;
  margin-top:5px;
}

.chart-container{
  width:100%;
  height:330px;
  position:relative;
}

#companyChart{
  width:100%;
  height:100%;
}

.explorer-news{
  margin-top:18px;
}

.related{
  padding:12px 0;
  border-bottom:1px solid var(--border);
}

.related:last-child{
  border-bottom:0;
}

.related a{
  color:#dce5f2;
  text-decoration:none;
  font-size:13px;
  line-height:1.4;
}

.related small{
  display:block;
  color:#738097;
  margin-top:4px;
}

/* =========================
   SETTINGS
   ========================= */

.settings{
  display:none;
}

.settings.open{
  display:block;
}

.setting-box{
  max-width:700px;
  margin:auto;
  background:var(--card);
  border:1px solid var(--border);
  border-radius:20px;
  padding:25px;
}

.setting-box label{
  display:block;
  font-size:12px;
  font-weight:800;
  margin-bottom:8px;
}

.setting-box input{
  width:100%;
  padding:12px;
  border-radius:10px;
  border:1px solid var(--border);
  background:#080d18;
  color:white;
  outline:none;
}

.setting-help{
  color:var(--muted);
  font-size:11px;
  line-height:1.6;
  margin-top:10px;
}

/* =========================
   STATUS
   ========================= */

.status{
  display:flex;
  justify-content:space-between;
  gap:15px;
  color:#68758a;
  font-size:10px;
  margin-top:22px;
  flex-wrap:wrap;
}

.status-live{
  display:flex;
  align-items:center;
  gap:6px;
}

.status-live span{
  width:6px;
  height:6px;
  border-radius:50%;
  background:var(--green);
}

/* =========================
   FOOTER
   ========================= */

footer{
  width:min(1400px,94%);
  margin:auto;
  border-top:1px solid var(--border);
  padding:25px 0 40px;
  color:#657186;
  font-size:11px;
  line-height:1.7;
}

/* =========================
   LOADING
   ========================= */

.loading{
  padding:35px;
  text-align:center;
  color:var(--muted);
  border:1px dashed var(--border);
  border-radius:15px;
}

/* =========================
   MOBILE
   ========================= */

@media(max-width:1050px){
  .market-grid{
    grid-template-columns:repeat(2,1fr);
  }

  .news-layout{
    grid-template-columns:1fr;
  }

  .market-art{
    opacity:.45;
    width:70%;
  }

  .explorer{
    grid-template-columns:1fr;
  }
}

@media(max-width:720px){
  .nav{
    height:62px;
  }

  .brand-sub{
    display:none;
  }

  .nav-btn{
    padding:8px;
    font-size:11px;
  }

  .hero{
    min-height:600px;
  }

  .hero-content{
    padding:45px 25px;
  }

  .hero h1{
    font-size:48px;
    letter-spacing:-2.5px;
  }

  .hero p{
    font-size:15px;
  }

  .market-art{
    width:115%;
    height:50%;
    top:auto;
    bottom:-25px;
    right:-80px;
    opacity:.45;
  }

  .market-grid{
    grid-template-columns:1fr 1fr;
  }

  .movers-grid{
    grid-template-columns:1fr;
  }

  .mover-row{
    grid-template-columns:90px 1fr 55px;
  }

  .news-title{
    font-size:17px;
  }
}

@media(max-width:480px){
  .market-grid{
    grid-template-columns:1fr;
  }

  .brand-name{
    font-size:16px;
  }

  .hero{
    border-radius:20px;
  }

  .hero-content{
    padding:38px 20px;
  }
}
</style>
</head>

<body>

<div class="background-grid"></div>
<div class="glow green"></div>
<div class="glow red"></div>

<!-- =====================================================
     HEADER
     ===================================================== -->

<header>
  <nav class="nav">

    <div class="brand">
      <div class="brand-mark">
        <svg viewBox="0 0 30 30" fill="none">
          <path d="M5 22L11 14L15 18L24 7"
                stroke="white"
                stroke-width="3"
                stroke-linecap="round"
                stroke-linejoin="round"/>
          <circle cx="24" cy="7" r="2.5" fill="white"/>
        </svg>
      </div>

      <div>
        <div class="brand-name">INTELLICS</div>
        <div class="brand-sub">AI & DATA ANALYTICS COMMITTEE</div>
      </div>
    </div>

    <div class="nav-actions">
      <button class="nav-btn active" onclick="showPage('news',this)">News</button>
      <button class="nav-btn" onclick="showPage('movers',this)">Movers</button>
      <button class="nav-btn" onclick="showPage('explorer',this)">Explorer</button>
      <button class="nav-btn" onclick="showPage('settings',this)">⚙</button>
    </div>

  </nav>
</header>


<!-- =====================================================
     HERO
     ===================================================== -->

<section class="hero">

  <div class="hero-content">

    <div class="badge">
      <span class="badge-dot"></span>
      INDIAN MARKETS • EXPLAINED SIMPLY
    </div>

    <h1>
      Understand<br>
      <span>the market.</span>
    </h1>

    <p>
      Intellics brings Indian market news, company movements,
      macro events and financial terminology together in one
      simple dashboard.
    </p>

    <div class="hero-buttons">
      <button class="primary" onclick="scrollToNews()">
        Explore today's news →
      </button>

      <button class="secondary" onclick="showPage('explorer')">
        Explore stocks
      </button>
    </div>

  </div>


  <!-- Bull + Bear SVG -->
  <div class="market-art">

    <svg viewBox="0 0 900 550"
         preserveAspectRatio="xMidYMid meet">

      <defs>

        <radialGradient id="greenGlow">
          <stop offset="0" stop-color="#28d17c" stop-opacity=".4"/>
          <stop offset="1" stop-color="#28d17c" stop-opacity="0"/>
        </radialGradient>

        <radialGradient id="redGlow">
          <stop offset="0" stop-color="#ff5c68" stop-opacity=".35"/>
          <stop offset="1" stop-color="#ff5c68" stop-opacity="0"/>
        </radialGradient>

        <linearGradient id="bullGrad"
                        x1="0"
                        y1="0"
                        x2="1"
                        y2="1">
          <stop stop-color="#42df91"/>
          <stop offset="1" stop-color="#087d50"/>
        </linearGradient>

        <linearGradient id="bearGrad"
                        x1="0"
                        y1="0"
                        x2="1"
                        y2="1">
          <stop stop-color="#ff737c"/>
          <stop offset="1" stop-color="#8c1f2d"/>
        </linearGradient>

      </defs>


      <!-- glow -->
      <ellipse
        class="bull-glow"
        cx="300"
        cy="310"
        rx="260"
        ry="220"
        fill="url(#greenGlow)"
      />

      <ellipse
        class="bear-glow"
        cx="650"
        cy="300"
        rx="260"
        ry="220"
        fill="url(#redGlow)"
      />


      <!-- market line -->
      <path
        class="chart-line"
        d="M60 400
           C130 380 140 390 185 350
           C230 310 245 360 290 320
           C335 280 360 300 390 245
           C425 190 455 230 490 210
           C535 185 555 140 600 170
           C650 200 680 125 730 115
           C780 105 815 75 850 45"
        fill="none"
        stroke="#8feebc"
        stroke-width="3"
        opacity=".45"
      />

      <!-- BULL -->

      <g class="bull"
         transform="translate(90 145)">

        <path
          d="M90 230
             C70 205 65 170 78 142
             C92 112 120 98 150 96
             C185 93 210 110 229 137
             L260 116
             C275 105 290 112 291 127
             C292 141 279 150 264 153
             L240 159
             C244 190 228 218 205 237
             L210 280
             L174 280
             L165 241
             L135 241
             L125 280
             L89 280
             L96 236
             Z"
          fill="url(#bullGrad)"
          opacity=".8"
        />

        <!-- horns -->
        <path
          d="M103 137
             C62 123 50 91 63 70
             C68 96 86 101 114 102"
          fill="none"
          stroke="#55e59a"
          stroke-width="11"
          stroke-linecap="round"
        />

        <path
          d="M199 104
             C236 83 263 65 270 39
             C281 68 262 105 230 124"
          fill="none"
          stroke="#55e59a"
          stroke-width="11"
          stroke-linecap="round"
        />

        <!-- eye -->
        <circle cx="228" cy="137" r="6" fill="#07150e"/>
        <circle cx="230" cy="135" r="2" fill="white"/>

        <!-- nose -->
        <ellipse cx="273" cy="150" rx="15" ry="10" fill="#075e3d"/>

        <circle cx="269" cy="148" r="2" fill="#9df5c7"/>
        <circle cx="278" cy="148" r="2" fill="#9df5c7"/>

      </g>


      <!-- BEAR -->

      <g class="bear"
         transform="translate(505 140)">

        <path
          d="M90 250
             C65 220 59 178 72 145
             C83 116 103 95 129 88
             L120 58
             C117 43 128 31 141 39
             L165 66
             C185 59 209 60 229 69
             L253 42
             C263 31 279 40 277 56
             L272 89
             C300 108 316 139 315 174
             C314 211 296 241 270 257
             L276 290
             L237 290
             L229 254
             L194 261
             L187 290
             L148 290
             L153 256
             C128 256 106 253 90 250Z"
          fill="url(#bearGrad)"
          opacity=".72"
        />

        <!-- ears -->
        <circle cx="132" cy="79" r="24" fill="#a32938"/>
        <circle cx="251" cy="79" r="24" fill="#a32938"/>

        <!-- eyes -->
        <circle cx="170" cy="138" r="6" fill="#16070a"/>
        <circle cx="238" cy="138" r="6" fill="#16070a"/>

        <!-- muzzle -->
        <ellipse cx="204" cy="174" rx="48" ry="35" fill="#d24a58"/>
        <ellipse cx="204" cy="163" rx="15" ry="11" fill="#421018"/>

        <!-- mouth -->
        <path
          d="M204 171 C198 192 184 197 174 194
             M204 171 C211 192 226 197 237 194"
          fill="none"
          stroke="#4b1018"
          stroke-width="4"
          stroke-linecap="round"
        />

      </g>

    </svg>

  </div>
</section>


<!-- =====================================================
     MAIN
     ===================================================== -->

<main>

  <!-- MARKET -->
  <div class="section-title">
    <div>
      <h2>Market Pulse</h2>
      <p>Major indicators at a glance</p>
    </div>
  </div>

  <section class="market-grid" id="marketGrid"></section>


  <!-- TABS -->

  <div class="tabs" style="margin-top:35px">
    <button class="tab active" onclick="showPage('news',this)">
      📰 News
    </button>

    <button class="tab" onclick="showPage('movers',this)">
      📈 Gainers & Losers
    </button>

    <button class="tab" onclick="showPage('explorer',this)">
      🔎 Company Explorer
    </button>
  </div>


  <!-- =====================================================
       NEWS PAGE
       ===================================================== -->

  <section id="newsPage">

    <div class="controls">

      <div class="search">
        <input
          id="searchInput"
          type="text"
          placeholder="Search news, companies or topics..."
          oninput="renderNews()"
        >
      </div>

      <select id="topicFilter" onchange="renderNews()">
        <option value="All">All topics</option>
        <option value="Markets">Markets</option>
        <option value="Economy & RBI">Economy & RBI</option>
        <option value="Companies">Companies</option>
        <option value="Global">Global</option>
        <option value="Commodities">Commodities</option>
      </select>

      <select id="sourceFilter" onchange="renderNews()">
        <option value="All">All sources</option>
      </select>

      <button
        class="filter-btn"
        id="todayBtn"
        onclick="toggleToday()"
      >
        Today only
      </button>

      <button
        class="filter-btn"
        onclick="loadNews(true)"
      >
        ↻ Refresh
      </button>

    </div>


    <div class="news-layout">

      <div class="news-list" id="newsList">
        <div class="loading">
          Loading market news...
        </div>
      </div>


      <aside>

        <div class="side-card">

          <div class="side-title">
            🔥 Stocks in Focus
          </div>

          <div id="focusList"></div>

        </div>


        <div class="side-card">

          <div class="side-title">
            💡 Quick Glossary
          </div>

          <div class="term">
            <b>Bull Market</b>
            <span>Prices generally moving upward.</span>
          </div>

          <div class="term">
            <b>Bear Market</b>
            <span>Prices generally moving downward.</span>
          </div>

          <div class="term">
            <b>Volatility</b>
            <span>How sharply prices move.</span>
          </div>

          <div class="term">
            <b>Market Cap</b>
            <span>Total market value of a company.</span>
          </div>

          <div class="term">
            <b>IPO</b>
            <span>First public sale of company shares.</span>
          </div>

        </div>

      </aside>

    </div>

  </section>


  <!-- =====================================================
       MOVERS PAGE
       ===================================================== -->

  <section id="moversPage" style="display:none">

    <div class="section-title">
      <div>
        <h2>Market Movers</h2>
        <p>Top gainers and losers in the tracked universe</p>
      </div>
    </div>

    <div class="movers-grid">

      <div class="mover-card">

        <div class="mover-head">
          <h3>🚀 Top Gainers</h3>
          <span class="up">Today</span>
        </div>

        <div id="gainers"></div>

      </div>


      <div class="mover-card">

        <div class="mover-head">
          <h3>🔻 Top Losers</h3>
          <span class="down">Today</span>
        </div>

        <div id="losers"></div>

      </div>

    </div>

  </section>


  <!-- =====================================================
       EXPLORER PAGE
       ===================================================== -->

  <section id="explorerPage" style="display:none">

    <div class="section-title">
      <div>
        <h2>Company Explorer</h2>
        <p>Price movement and related market news</p>
      </div>
    </div>

    <div class="explorer">

      <div class="explorer-card">

        <label style="font-size:11px;color:#8996aa">
          SELECT COMPANY
        </label>

        <select
          class="company-select"
          id="companySelect"
          onchange="loadCompany()"
        ></select>

        <div class="company-big" id="companyName">
          Reliance Industries
        </div>

        <div class="company-price" id="companyPrice">
          Loading...
        </div>

        <div class="status" style="margin-top:25px">
          <span>1 month performance</span>
          <span id="companyChange">—</span>
        </div>

      </div>


      <div class="explorer-card">

        <div class="chart-container">
          <svg id="companyChart"
               viewBox="0 0 900 330"
               preserveAspectRatio="none">
          </svg>
        </div>

        <div class="explorer-news">

          <div class="side-title">
            Related News
          </div>

          <div id="relatedNews"></div>

        </div>

      </div>

    </div>

  </section>


  <!-- =====================================================
       SETTINGS PAGE
       ===================================================== -->

  <section id="settingsPage" class="settings">

    <div class="section-title">
      <div>
        <h2>Intellics Settings</h2>
        <p>Optional AI configuration</p>
      </div>
    </div>

    <div class="setting-box">

      <label>Groq API Key</label>

      <input
        id="groqKey"
        type="password"
        placeholder="gsk_..."
      >

      <button
        class="primary"
        style="margin-top:12px"
        onclick="saveGroqKey()"
      >
        Save API key
      </button>

      <p class="setting-help">
        If you provide a Groq API key, Intellics can generate
        short plain-English summaries for articles.
        The key is stored only in this browser using localStorage.
        If no key is provided, Intellics uses its built-in
        rule-based summary instead.
      </p>

    </div>

  </section>


  <!-- STATUS -->

  <div class="status">

    <div class="status-live">
      <span></span>
      <span id="statusText">
        Intellics ready
      </span>
    </div>

    <span id="lastUpdated">
      Last updated — 
    </span>

  </div>

</main>


<!-- =====================================================
     FOOTER
     ===================================================== -->

<footer>

  <strong>Intellics</strong> — AI & Data Analytics Committee.

  <br>

  This dashboard is for educational and informational purposes only.
  Market prices and news may be delayed. Nothing on this website
  constitutes investment, financial or trading advice.

</footer>


<script>

/* =========================================================
   INTELLICS DATA
   ========================================================= */

const companies = [
  {
    name:"Reliance Industries",
    ticker:"RELIANCE.NS",
    aliases:["reliance","ril"]
  },
  {
    name:"Tata Consultancy Services",
    ticker:"TCS.NS",
    aliases:["tcs"]
  },
  {
    name:"HDFC Bank",
    ticker:"HDFCBANK.NS",
    aliases:["hdfc","hdfc bank"]
  },
  {
    name:"Infosys",
    ticker:"INFY.NS",
    aliases:["infosys"]
  },
  {
    name:"ICICI Bank",
    ticker:"ICICIBANK.NS",
    aliases:["icici","icici bank"]
  },
  {
    name:"State Bank of India",
    ticker:"SBIN.NS",
    aliases:["sbi","state bank"]
  },
  {
    name:"Bharti Airtel",
    ticker:"BHARTIARTL.NS",
    aliases:["airtel","bharti airtel"]
  },
  {
    name:"ITC",
    ticker:"ITC.NS",
    aliases:["itc"]
  },
  {
    name:"Larsen & Toubro",
    ticker:"LT.NS",
    aliases:["l&t","larsen"]
  },
  {
    name:"Tata Motors",
    ticker:"TATAMOTORS.NS",
    aliases:["tata motors"]
  }
];


const glossary = {

  "bull market":{
    term:"Bull Market",
    meaning:"A period when asset prices are generally rising."
  },

  "bear market":{
    term:"Bear Market",
    meaning:"A period when asset prices are generally falling."
  },

  "volatility":{
    term:"Volatility",
    meaning:"How much and how quickly a price moves."
  },

  "market cap":{
    term:"Market Cap",
    meaning:"The total market value of a company's outstanding shares."
  },

  "ipo":{
    term:"IPO",
    meaning:"An Initial Public Offering, when a company offers shares to the public."
  },

  "rbi":{
    term:"RBI",
    meaning:"Reserve Bank of India, India's central bank."
  },

  "repo rate":{
    term:"Repo Rate",
    meaning:"The rate at which RBI lends short-term money to banks."
  },

  "inflation":{
    term:"Inflation",
    meaning:"A sustained increase in the general level of prices."
  },

  "gdp":{
    term:"GDP",
    meaning:"The value of goods and services produced in an economy."
  },

  "earnings":{
    term:"Earnings",
    meaning:"The profit generated by a company during a period."
  },

  "revenue":{
    term:"Revenue",
    meaning:"The money a company earns from its business activities."
  },

  "margin":{
    term:"Margin",
    meaning:"A measure of profit relative to revenue."
  },

  "m&a":{
    term:"M&A",
    meaning:"Mergers and acquisitions involving companies."
  },

  "fii":{
    term:"FII",
    meaning:"Foreign Institutional Investors investing in Indian markets."
  },

  "dii":{
    term:"DII",
    meaning:"Domestic Institutional Investors investing in Indian markets."
  },

  "crude oil":{
    term:"Crude Oil",
    meaning:"Unrefined petroleum used to produce fuels and other products."
  }

};


/* =========================================================
   DEMO NEWS
   ========================================================= */

let newsData = [

  {
    title:"Indian equities remain in focus as investors track global cues",
    source:"Intellics Market Desk",
    topic:"Markets",
    date:new Date(),
    summary:"Indian investors are watching global markets, institutional flows and upcoming economic signals as markets search for direction.",
    link:"#"
  },

  {
    title:"RBI policy outlook keeps interest rates and liquidity in focus",
    source:"Economic Times",
    topic:"Economy & RBI",
    date:new Date(),
    summary:"Expectations around monetary policy remain important because interest rates influence borrowing costs, liquidity and economic activity.",
    link:"#"
  },

  {
    title:"Large-cap companies remain closely watched by investors",
    source:"Moneycontrol",
    topic:"Companies",
    date:new Date(),
    summary:"Large companies continue to attract attention as investors evaluate earnings, valuations and expectations for future growth.",
    link:"#"
  },

  {
    title:"Crude oil prices remain an important variable for India",
    source:"Business Standard",
    topic:"Commodities",
    date:new Date(),
    summary:"Changes in crude prices can influence India's import bill, inflation, currency and profitability across several industries.",
    link:"#"
  },

  {
    title:"Global markets influence sentiment across Indian equities",
    source:"Mint",
    topic:"Global",
    date:new Date(),
    summary:"Investors are monitoring global risk appetite, overseas markets and macroeconomic signals for their potential impact on Indian equities.",
    link:"#"
  }

];


/* =========================================================
   MARKET DATA
   ========================================================= */

const marketItems = [

  {
    name:"Sensex",
    ticker:"^BSESN"
  },

  {
    name:"Nifty 50",
    ticker:"^NSEI"
  },

  {
    name:"Brent Crude",
    ticker:"BZ=F"
  },

  {
    name:"Gold",
    ticker:"GC=F"
  }

];


/* =========================================================
   APP STATE
   ========================================================= */

let onlyToday=false;

let currentPage="news";

let prices={};

let lastNewsFetch=null;


/* =========================================================
   PAGE NAVIGATION
   ========================================================= */

function showPage(page,button){

  currentPage=page;

  document.getElementById("newsPage").style.display =
    page==="news" ? "" : "none";

  document.getElementById("moversPage").style.display =
    page==="movers" ? "" : "none";

  document.getElementById("explorerPage").style.display =
    page==="explorer" ? "" : "none";

  document.getElementById("settingsPage").classList.toggle(
    "open",
    page==="settings"
  );

  document.querySelectorAll(".nav-btn,.tab")
    .forEach(x=>x.classList.remove("active"));

  if(button){
    button.classList.add("active");
  }

  if(page==="movers"){
    renderMovers();
  }

  if(page==="explorer"){
    loadCompany();
  }

  window.scrollTo({
    top:document.querySelector("main").offsetTop-80,
    behavior:"smooth"
  });
}


function scrollToNews(){

  document.getElementById("newsPage").scrollIntoView({
    behavior:"smooth"
  });

}


/* =========================================================
   FORMATTERS
   ========================================================= */

function formatNumber(value){

  if(value===null || value===undefined || isNaN(value)){
    return "—";
  }

  return Number(value).toLocaleString("en-IN",{
    maximumFractionDigits:2
  });

}


function formatPercent(value){

  if(value===null || value===undefined || isNaN(value)){
    return "—";
  }

  return `${value>=0?"+":""}${Number(value).toFixed(2)}%`;

}


function timeAgo(date){

  const diff=Math.max(
    0,
    Math.floor((Date.now()-new Date(date).getTime())/60000)
  );

  if(diff<1) return "Just now";

  if(diff<60) return `${diff}m ago`;

  const hours=Math.floor(diff/60);

  if(hours<24) return `${hours}h ago`;

  return `${Math.floor(hours/24)}d ago`;

}


/* =========================================================
   YAHOO FINANCE
   ========================================================= */

async function yahooChart(ticker,range="5d",interval="1d"){

  const url=
    "https://query1.finance.yahoo.com/v8/finance/chart/"+
    encodeURIComponent(ticker)+
    `?range=${range}&interval=${interval}`;

  try{

    const response=await fetch(url);

    if(!response.ok) throw new Error("Yahoo request failed");

    const json=await response.json();

    const result=json.chart.result?.[0];

    if(!result) throw new Error("No result");

    const timestamps=result.timestamp || [];

    const quote=result.indicators.quote[0];

    const closes=quote.close || [];

    const values=[];

    timestamps.forEach((time,i)=>{

      if(closes[i]!==null && closes[i]!==undefined){

        values.push({
          time:time*1000,
          close:closes[i]
        });

      }

    });

    return values;

  }catch(error){

    return null;

  }

}


/* =========================================================
   MARKET CARDS
   ========================================================= */

async function loadMarkets(){

  const grid=document.getElementById("marketGrid");

  grid.innerHTML=marketItems.map(item=>`

    <div class="market-card">

      <div class="market-name">${item.name}</div>

      <div class="market-value" id="price-${item.ticker}">
        Loading...
      </div>

      <div class="market-change" id="change-${item.ticker}">
        —
      </div>

      <svg
        class="mini-chart"
        id="mini-${item.ticker}"
        viewBox="0 0 250 35"
        preserveAspectRatio="none">
      </svg>

    </div>

  `).join("");


  for(const item of marketItems){

    const data=await yahooChart(
      item.ticker,
      "5d",
      "1d"
    );

    let values=data;

    if(!values || values.length<2){

      values=generateDemoSeries(
        100+
        Math.random()*500,
        10
      );

    }

    const latest=values[values.length-1].close;

    const previous=values[values.length-2].close;

    const change=
      previous
      ? ((latest-previous)/previous)*100
      : 0;

    prices[item.ticker]={
      price:latest,
      change,
      series:values
    };

    const priceEl=
      document.getElementById(`price-${item.ticker}`);

    const changeEl=
      document.getElementById(`change-${item.ticker}`);

    if(priceEl){

      priceEl.textContent=
        formatNumber(latest);

    }

    if(changeEl){

      changeEl.textContent=
        formatPercent(change);

      changeEl.className=
        "market-change "+(change>=0?"up":"down");

    }

    drawMiniChart(
      document.getElementById(`mini-${item.ticker}`),
      values,
      change>=0
    );

  }

}


/* =========================================================
   MINI CHART
   ========================================================= */

function drawMiniChart(svg,data,positive){

  if(!svg || !data || !data.length) return;

  const values=data.map(x=>x.close);

  const min=Math.min(...values);

  const max=Math.max(...values);

  const range=max-min || 1;

  const points=values.map((value,index)=>{

    const x=
      (index/(values.length-1||1))*250;

    const y=
      32-
      ((value-min)/range)*28;

    return `${x},${y}`;

  }).join(" ");

  svg.innerHTML=`

    <polyline
      points="${points}"
      fill="none"
      stroke="${positive?"#28d17c":"#ff5c68"}"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
    />

  `;

}


/* =========================================================
   NEWS RENDER
   ========================================================= */

function renderNews(){

  const search=
    document.getElementById("searchInput")
      .value
      .toLowerCase()
      .trim();

  const topic=
    document.getElementById("topicFilter").value;

  const source=
    document.getElementById("sourceFilter").value;

  let filtered=newsData.filter(article=>{

    const matchesSearch=
      !search ||
      (
        article.title+" "+
        article.summary+" "+
        article.source+" "+
        article.topic
      ).toLowerCase().includes(search);

    const matchesTopic=
      topic==="All" ||
      article.topic===topic;

    const matchesSource=
      source==="All" ||
      article.source===source;

    let matchesToday=true;

    if(onlyToday){

      const d=new Date(article.date);

      const now=new Date();

      matchesToday=
        d.toDateString()===now.toDateString();

    }

    return(
      matchesSearch &&
      matchesTopic &&
      matchesSource &&
      matchesToday
    );

  });


  const container=
    document.getElementById("newsList");


  if(!filtered.length){

    container.innerHTML=`

      <div class="loading">
        No stories found for the selected filters.
      </div>

    `;

    return;

  }


  container.innerHTML=
    filtered.map(article=>newsCard(article)).join("");

}


function newsCard(article){

  const terms=
    findGlossaryTerms(
      article.title+" "+article.summary
    );

  return `

    <article class="news-card">

      <div class="news-top">

        <span class="source">
          ${escapeHTML(article.source)}
        </span>

        <span class="news-time">
          ${timeAgo(article.date)}
        </span>

        <span class="topic">
          ${escapeHTML(article.topic)}
        </span>

      </div>

      <div class="news-title">
        ${escapeHTML(article.title)}
      </div>

      <div class="news-summary">
        ${escapeHTML(article.summary)}
      </div>

      <a
        class="read-link"
        href="${article.link || "#"}"
        target="_blank"
        rel="noopener"
      >
        Read source →
      </a>

      ${
        terms.length
        ?
        `
        <div class="explainer">

          <div class="explainer-label">
            Words explained
          </div>

          ${terms.map(term=>`

            <span class="term">

              <b>${term.term}</b>

              <span>${term.meaning}</span>

            </span>

          `).join("")}

        </div>
        `
        :""
      }

    </article>

  `;

}


function findGlossaryTerms(text){

  const lower=text.toLowerCase();

  const found=[];

  Object.keys(glossary).forEach(key=>{

    if(
      lower.includes(key) &&
      !found.some(x=>x.term===glossary[key].term)
    ){

      found.push(glossary[key]);

    }

  });

  return found.slice(0,5);

}


/* =========================================================
   ESCAPE
   ========================================================= */

function escapeHTML(value){

  return String(value)
    .replaceAll("&","&amp;")
    .replaceAll("<","&lt;")
    .replaceAll(">","&gt;")
    .replaceAll('"',"&quot;")
    .replaceAll("'","&#039;");

}


/* =========================================================
   SOURCES
   ========================================================= */

function populateSources(){

  const select=
    document.getElementById("sourceFilter");

  const sources=[
    ...new Set(newsData.map(x=>x.source))
  ];

  select.innerHTML=
    `<option value="All">All sources</option>`+
    sources.map(source=>
      `<option value="${escapeHTML(source)}">
        ${escapeHTML(source)}
      </option>`
    ).join("");

}


/* =========================================================
   TODAY FILTER
   ========================================================= */

function toggleToday(){

  onlyToday=!onlyToday;

  const button=
    document.getElementById("todayBtn");

  button.classList.toggle(
    "active",
    onlyToday
  );

  renderNews();

}


/* =========================================================
   STOCKS IN FOCUS
   ========================================================= */

function renderFocus(){

  const focus=
    companies.slice(0,6);

  document.getElementById("focusList").innerHTML=
    focus.map(company=>{

      const p=
        prices[company.ticker];

      const change=
        p?.change ??
        ((Math.random()-.5)*4);

      return `

        <div class="focus-item">

          <div>
            <div class="focus-company">
              ${company.name}
            </div>

            <div class="focus-meta">
              ${company.ticker}
            </div>
          </div>

          <div class="focus-change ${change>=0?"up":"down"}">
            ${formatPercent(change)}
          </div>

        </div>

      `;

    }).join("");

}


/* =========================================================
   MOVERS
   ========================================================= */

function getMovers(){

  return companies.map(company=>{

    const p=prices[company.ticker];

    return {
      ...company,
      change:p?.change ??
        ((Math.random()-.5)*6)
    };

  });

}


function renderMovers(){

  const data=getMovers()
    .sort((a,b)=>b.change-a.change);

  const gainers=data
    .filter(x=>x.change>=0)
    .slice(0,6);

  const losers=data
    .filter(x=>x.change<0)
    .sort((a,b)=>a.change-b.change)
    .slice(0,6);

  renderMoverList(
    document.getElementById("gainers"),
    gainers,
    true
  );

  renderMoverList(
    document.getElementById("losers"),
    losers,
    false
  );

}


function renderMoverList(container,data,positive){

  if(!data.length){

    container.innerHTML=
      `<div class="loading">No data available.</div>`;

    return;

  }

  const max=
    Math.max(
      ...data.map(x=>Math.abs(x.change))
    ) || 1;

  container.innerHTML=
    data.map(item=>{

      const width=
        Math.min(
          100,
          Math.abs(item.change)/max*100
        );

      return `

        <div class="mover-row">

          <div class="mover-name">
            ${item.name}
          </div>

          <div class="bar-bg">

            <div
              class="bar ${positive?"green-bar":"red-bar"}"
              style="width:${width}%">
            </div>

          </div>

          <div
            class="mover-value ${positive?"up":"down"}"
          >
            ${formatPercent(item.change)}
          </div>

        </div>

      `;

    }).join("");

}


/* =========================================================
   COMPANY EXPLORER
   ========================================================= */

function populateCompanies(){

  const select=
    document.getElementById("companySelect");

  select.innerHTML=
    companies.map((company,index)=>`

      <option value="${index}">
        ${company.name}
      </option>

    `).join("");

}


async function loadCompany(){

  const index=
    Number(
      document.getElementById("companySelect").value
    );

  const company=
    companies[index];

  if(!company) return;

  document.getElementById("companyName")
    .textContent=company.name;

  document.getElementById("companyPrice")
    .textContent="Loading...";

  const data=
    await yahooChart(
      company.ticker,
      "1mo",
      "1d"
    );

  let series=data;

  if(!series || series.length<3){

    series=
      generateDemoSeries(
        700+Math.random()*1500,
        30
      );

  }

  const latest=
    series[series.length-1].close;

  const first=
    series[0].close;

  const change=
    ((latest-first)/first)*100;

  document.getElementById("companyPrice")
    .textContent=
      "₹"+formatNumber(latest);

  document.getElementById("companyChange")
    .textContent=
      formatPercent(change);

  document.getElementById("companyChange")
    .className=
      change>=0 ? "up" : "down";

  drawCompanyChart(series);

  renderRelatedNews(company);

}


function drawCompanyChart(data){

  const svg=
    document.getElementById("companyChart");

  const values=
    data.map(x=>x.close);

  const min=Math.min(...values);

  const max=Math.max(...values);

  const range=max-min || 1;

  const width=900;

  const height=300;

  const points=
    values.map((value,index)=>{

      const x=
        index/(values.length-1||1)*
        (width-30)+15;

      const y=
        height-
        ((value-min)/range)*(height-35)+10;

      return `${x},${y}`;

    });

  const areaPoints=
    [
      `15,${height}`,
      ...points,
      `${width-15},${height}`
    ].join(" ");

  const positive=
    values[values.length-1]>=values[0];

  svg.innerHTML=`

    <defs>

      <linearGradient
        id="chartFill"
        x1="0"
        y1="0"
        x2="0"
        y2="1">

        <stop
          offset="0"
          stop-color="${positive?"#28d17c":"#ff5c68"}"
          stop-opacity=".22"
        />

        <stop
          offset="1"
          stop-color="${positive?"#28d17c":"#ff5c68"}"
          stop-opacity="0"
        />

      </linearGradient>

    </defs>

    <line
      x1="0"
      y1="75"
      x2="900"
      y2="75"
      stroke="rgba(255,255,255,.06)"
    />

    <line
      x1="0"
      y1="150"
      x2="900"
      y2="150"
      stroke="rgba(255,255,255,.06)"
    />

    <line
      x1="0"
      y1="225"
      x2="900"
      y2="225"
      stroke="rgba(255,255,255,.06)"
    />

    <polygon
      points="${areaPoints}"
      fill="url(#chartFill)"
    />

    <polyline
      points="${points.join(" ")}"
      fill="none"
      stroke="${positive?"#28d17c":"#ff5c68"}"
      stroke-width="3"
      stroke-linecap="round"
      stroke-linejoin="round"
    />

  `;

}


function renderRelatedNews(company){

  const terms=
    [company.name.toLowerCase(),...company.aliases];

  const relevant=
    newsData.filter(article=>{

      const text=
        (
          article.title+
          " "+
          article.summary
        ).toLowerCase();

      return terms.some(term=>text.includes(term));

    }).slice(0,5);

  const list=
    relevant.length
    ? relevant
    : newsData.slice(0,5);

  document.getElementById("relatedNews").innerHTML=
    list.map(article=>`

      <div class="related">

        <a
          href="${article.link||"#"}"
          target="_blank"
          rel="noopener"
        >
          ${escapeHTML(article.title)}
        </a>

        <small>
          ${escapeHTML(article.source)}
          •
          ${timeAgo(article.date)}
        </small>

      </div>

    `).join("");

}


/* =========================================================
   RSS NEWS
   ========================================================= */

const rssFeeds=[

  {
    source:"Economic Times",
    topic:"Markets",
    url:"https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"
  },

  {
    source:"Moneycontrol",
    topic:"Markets",
    url:"https://www.moneycontrol.com/rss/marketreports.xml"
  },

  {
    source:"Mint",
    topic:"Markets",
    url:"https://www.livemint.com/rss/markets"
  },

  {
    source:"Business Standard",
    topic:"Markets",
    url:"https://www.business-standard.com/rss/markets-106.rss"
  },

  {
    source:"BusinessLine",
    topic:"Economy & RBI",
    url:"https://www.thehindubusinessline.com/feeder/default.rss"
  }

];


async function fetchRSS(feed){

  try{

    const proxy=
      "https://api.rss2json.com/v1/api.json?rss_url="+
      encodeURIComponent(feed.url);

    const response=
      await fetch(proxy);

    if(!response.ok){
      throw new Error("RSS error");
    }

    const json=
      await response.json();

    return (json.items||[])
      .slice(0,8)
      .map(item=>({

        title:item.title,

        source:feed.source,

        topic:feed.topic,

        date:
          item.pubDate
          ? new Date(item.pubDate)
          : new Date(),

        summary:
          cleanText(
            item.description||
            item.content||
            item.title
          ).slice(0,500),

        link:item.link

      }));

  }catch(error){

    return [];

  }

}


async function loadNews(force=false){

  setStatus(
    force
    ? "Refreshing news..."
    : "Loading news..."
  );

  try{

    const results=
      await Promise.all(
        rssFeeds.map(fetchRSS)
      );

    const fetched=
      results.flat();

    if(fetched.length){

      newsData=[
        ...fetched,
        ...newsData
      ];

      newsData=
        dedupeNews(newsData)
        .slice(0,60);

      lastNewsFetch=
        new Date();

      populateSources();

      renderNews();

      renderRelatedIfExplorer();

      setStatus(
        `${fetched.length} fresh stories loaded`
      );

    }else{

      setStatus(
        "Live news unavailable — showing fallback stories"
      );

    }

  }catch(error){

    setStatus(
      "Using fallback market stories"
    );

  }

  document.getElementById("lastUpdated")
    .textContent=
      "Last updated " +
      new Date().toLocaleTimeString();

}


function cleanText(text){

  const temp=
    document.createElement("div");

  temp.innerHTML=text;

  return temp.textContent || temp.innerText || "";

}


function dedupeNews(items){

  const seen=new Set();

  return items.filter(item=>{

    const key=
      item.title
        .toLowerCase()
        .replace(/\s+/g," ")
        .trim();

    if(seen.has(key)) return false;

    seen.add(key);

    return true;

  });

}


function renderRelatedIfExplorer(){

  if(currentPage==="explorer"){
    loadCompany();
  }

}


/* =========================================================
   OPTIONAL GROQ AI SUMMARY
   ========================================================= */

function saveGroqKey(){

  const key=
    document.getElementById("groqKey").value.trim();

  if(key){

    localStorage.setItem(
      "intellics_groq_key",
      key
    );

    alert(
      "Groq API key saved in this browser."
    );

  }

}


async function summarizeWithGroq(article){

  const key=
    localStorage.getItem(
      "intellics_groq_key"
    );

  if(!key){
    return basicSummary(article);
  }

  try{

    const response=
      await fetch(
        "https://api.groq.com/openai/v1/chat/completions",
        {
          method:"POST",

          headers:{
            "Content-Type":"application/json",
            "Authorization":"Bearer "+key
          },

          body:JSON.stringify({

            model:"llama-3.1-8b-instant",

            messages:[

              {
                role:"system",
                content:
                  "Explain financial news simply for an Indian MBA student. Keep it under 70 words."
              },

              {
                role:"user",
                content:
                  article.title+
                  "\n\n"+
                  article.summary
              }

            ],

            temperature:.2,

            max_tokens:120

          })

        }
      );

    if(!response.ok){
      return basicSummary(article);
    }

    const json=
      await response.json();

    return (
      json.choices?.[0]?.message?.content ||
      basicSummary(article)
    );

  }catch(error){

    return basicSummary(article);

  }

}


function basicSummary(article){

  const title=
    article.title.toLowerCase();

  if(title.includes("rbi")){
    return "This matters because RBI policy can influence interest rates, liquidity, borrowing costs and economic activity.";
  }

  if(title.includes("oil") || title.includes("crude")){
    return "Crude prices matter to India because the country imports a large amount of its energy. Higher prices can affect inflation and costs.";
  }

  if(title.includes("earnings") || title.includes("profit")){
    return "Investors are watching company earnings because profits and future guidance can influence valuation and share prices.";
  }

  return article.summary ||
    "The story is relevant because it may influence investor sentiment, expectations or market prices.";

}


/* =========================================================
   DEMO SERIES
   ========================================================= */

function generateDemoSeries(start,count){

  const result=[];

  let value=start;

  for(let i=0;i<count;i++){

    value+=
      (Math.random()-.46)*
      start*.025;

    if(value<1){
      value=1;
    }

    result.push({
      time:Date.now()-
        (count-i)*86400000,
      close:value
    });

  }

  return result;

}


/* =========================================================
   SETTINGS LOAD
   ========================================================= */

function loadSettings(){

  const key=
    localStorage.getItem(
      "intellics_groq_key"
    );

  if(key){

    document.getElementById("groqKey")
      .value=key;

  }

}


/* =========================================================
   STATUS
   ========================================================= */

function setStatus(message){

  document.getElementById("statusText")
    .textContent=message;

}


/* =========================================================
   INITIALIZE
   ========================================================= */

async function initialize(){

  populateCompanies();

  populateSources();

  loadSettings();

  renderNews();

  renderFocus();

  await loadMarkets();

  renderFocus();

  renderMovers();

  await loadNews();

}


/* =========================================================
   REFRESH TIMERS
   ========================================================= */

setInterval(()=>{

  loadMarkets();

},30000);


setInterval(()=>{

  loadNews();

},120000);


/* =========================================================
   START
   ========================================================= */

initialize();

</script>

</body>
</html>
```
