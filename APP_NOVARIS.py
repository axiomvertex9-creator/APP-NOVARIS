import json
import os
import random
import re
import html
from datetime import datetime
from pathlib import Path
from orion_widget import orion_widget
from planet_codex import render_planet_codex 

import streamlit as st
import streamlit.components.v1 as components

ETUDE_HTML = Path(__file__).with_name("etude.html")
SIM_HTML = Path(__file__).with_name("astronaut sim.html")
ORBITAL_HTML = Path(__file__).with_name("Orbital Foundry.html")
FLIGHT_HTML = Path(__file__).with_name("orion-flight-sim.html")
SPACE_HTML = Path(__file__).with_name("flight sim.html")
MISSION_HTML = Path(__file__).with_name("mission.html")
EXPOLIS_HTML = Path(__file__).with_name("expolis.html")
ACADEMY_HTML = Path(__file__).with_name("academy.html")

st.set_page_config(page_title="NOVARIS", page_icon="🚀", layout="wide", initial_sidebar_state="collapsed")

USERS_FILE = Path(__file__).with_name("users.json")   # sign-up data is stored here
EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")

# ---------------- SESSION STATE ----------------

defaults = {
    "bg_color": "#1E0A3C",
    "text_color": "#00D2FF",
    "accent_color": "#7C4DFF",
    "dashboard_title": "WELCOME TO NOVARIS (ensure Internet is present)",
    "launch_name": None,   # name currently being launched (None = show form)
    "launch_id": 0,        # changes on every launch/replay so the animation restarts
    "launch_user": None,   # record saved for the current launch (for the download button)
    "travel_to": None,     # destination chosen on the SPACE TRAVEL page
    "travel_id": 0         # changes on every trip so the scene restarts
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ---------------- INTRO ----------------
if "intro_done" not in st.session_state:
    st.session_state.intro_done = False

if not st.session_state.intro_done:
    st.markdown("""<style>
    header, footer, [data-testid="stToolbar"], [data-testid="stSidebar"],
    [data-testid="stSidebarCollapsedControl"] {display:none}
    .block-container {padding:0 !important; max-width:100% !important}
    iframe[title$="novaris_intro"] {position:fixed; inset:0; width:100vw; height:100vh; border:0; z-index:9999}
    </style>""", unsafe_allow_html=True)
    intro = components.declare_component("novaris_intro", path=str(Path(__file__).with_name("novaris_intro")))
    if intro(key="intro", default=None) == "done":
        st.session_state.intro_done = True
        st.rerun()
    st.stop()

if not st.session_state.get("faded"):
    st.session_state.faded = True
    st.markdown(
        "<style>"
        "body::after{content:'';position:fixed;inset:0;background:#000;"
        "z-index:999999;pointer-events:none;animation:novout 2s ease-out forwards}"
        "@keyframes novout{from{opacity:1} to{opacity:0}}"
        "</style>",
        unsafe_allow_html=True
    )

# ---------------- FILE HANDLING ----------------

def load_users():
    try:
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_user(user):
    users = load_users()          # re-read so parallel sessions don't overwrite each other
    users.append(user)
    tmp = USERS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(users, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, USERS_FILE)   # atomic swap: the file is never half-written


def mask_email(email):
    local, _, domain = email.partition("@")
    return f"{local[:1]}***@{domain}"


# ---------------- GOOGLE (GMAIL) SIGN-IN ----------------

def google_login_ready():
    try:
        return hasattr(st, "login") and "auth" in st.secrets
    except Exception:
        return False


def google_account():
    try:
        if getattr(st.user, "is_logged_in", False):
            return {"name": st.user.get("name", ""), "email": st.user.get("email", "")}
    except Exception:
        pass
    return None

# ---------------- USER PREFERENCES (mini local backend: prefs.json) ----------------
# prefs.json = a tiny "cookie jar" on disk. users.json (login/sign-up data) is NOT touched.
# Layout: {"_last_user": "...", "profiles": {"<email or guest>": {"preferences": {}, "clicks": {}, "events": []}}}

PREFS_FILE = Path(__file__).with_name("prefs.json")
PREF_KEYS = ("bg_color", "text_color", "accent_color", "dashboard_title")
MAX_EVENTS = 200                                   # keep the click log from growing forever
HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def _read_prefs():
    try:
        data = json.loads(PREFS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _write_prefs(data):
    tmp = PREFS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, PREFS_FILE)                    # atomic swap, same trick as save_user()


def _profile(data, key):
    profiles = data.setdefault("profiles", {})
    prof = profiles.setdefault(key, {})
    prof.setdefault("preferences", {})
    prof.setdefault("clicks", {})
    prof.setdefault("events", [])
    return prof


def current_profile():
    g = google_account()
    if g and g.get("email"):
        return g["email"].lower()
    rec = st.session_state.get("launch_user")
    if rec and rec.get("email"):
        return rec["email"].lower()
    return st.session_state.get("profile") or "guest"


def save_prefs():
    """Write the current look (colors + title) to prefs.json for the active profile."""
    data = _read_prefs()
    key = current_profile()
    _profile(data, key)["preferences"] = {k: st.session_state[k] for k in PREF_KEYS}
    data["_last_user"] = key
    _write_prefs(data)


def track(name, kind="click"):
    """Count a click / page visit and add it to the event log."""
    data = _read_prefs()
    key = current_profile()
    prof = _profile(data, key)
    prof["clicks"][name] = prof["clicks"].get(name, 0) + 1
    prof["events"].append({
        "time": datetime.now().isoformat(timespec="seconds"),
        "type": kind,
        "name": name
    })
    prof["events"] = prof["events"][-MAX_EVENTS:]
    data["_last_user"] = key
    _write_prefs(data)


# Once per browser session: bring back the saved look.
if "prefs_loaded" not in st.session_state:
    st.session_state.prefs_loaded = True
    _data = _read_prefs()
    _g = google_account()
    st.session_state.profile = (
        _g["email"].lower() if _g and _g.get("email") else _data.get("_last_user", "guest")
    )
    _saved = _data.get("profiles", {}).get(st.session_state.profile, {}).get("preferences", {})
    for _k in PREF_KEYS:
        _v = _saved.get(_k)
        if _k.endswith("_color"):
            if isinstance(_v, str) and HEX_RE.match(_v):
                st.session_state[_k] = _v
        elif isinstance(_v, str) and _v.strip():
            st.session_state[_k] = _v.strip()[:100]
    st.session_state.prefs_snapshot = {k: st.session_state[k] for k in PREF_KEYS}

# ---------------- LAUNCH ANIMATION ----------------
# Plain string with __TOKENS__ so CSS/JS braces need no escaping.

LAUNCH_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Unbounded:wght@800&display=swap" rel="stylesheet">
<style>
:root{--flare:#ff7a3d;--ion:#4de8ff;--font:'Unbounded',system-ui,sans-serif;--mono:ui-monospace,Menlo,Consolas,monospace}
html,body{height:100%;margin:0;overflow:hidden;background:transparent;font-family:var(--font);color:#f3f1ea}
canvas{position:fixed;inset:0;width:100%;height:100%}
#title,#count{position:fixed;left:50%;transform:translate(-50%,-50%);text-align:center;width:92vw;
font-weight:800;word-break:break-word}
#title{top:50%;font-size:clamp(1.6rem,8vw,4.2rem);text-shadow:0 0 24px var(--ion);transition:top 1.4s ease}
#title.up{top:15%}
#title.flash{animation:fl .36s steps(1) infinite}
@keyframes fl{0%{color:#fff;text-shadow:0 0 30px var(--ion),0 0 60px var(--ion)}
50%{color:var(--flare);text-shadow:0 0 30px var(--flare),0 0 60px var(--flare)}}
#count{top:42%;font-size:clamp(4rem,20vw,8rem);color:var(--ion);opacity:0}
#count.pop{animation:pop .9s ease-out}
@keyframes pop{0%{opacity:1;transform:translate(-50%,-50%) scale(1.5)}100%{opacity:0;transform:translate(-50%,-50%) scale(.8)}}
#hud{position:fixed;left:10px;top:10px;width:min(48vw,270px);padding:8px 10px;border:1px solid var(--ion);
border-radius:10px;background:rgba(7,10,36,.6);font:11px/1.55 var(--mono);opacity:0;transition:opacity .8s}
#hud.on{opacity:1}#hud h4{margin:0 0 4px;font:800 10px var(--font);color:var(--ion);letter-spacing:.08em}
#hud div{display:flex;justify-content:space-between;gap:8px}#hud span{opacity:.7}#hud b{text-align:right}
#toasts{position:fixed;right:10px;top:10px;width:min(46vw,300px);font:11px/1.4 var(--mono)}
.t{margin-bottom:6px;padding:6px 10px;border-left:3px solid var(--ion);border-radius:6px;background:rgba(7,10,36,.75);animation:in .4s ease-out}
.t.big{border-color:#3ddc84;color:#b6ffd6;font-size:13px;font-weight:700}
@keyframes in{from{opacity:0;transform:translateX(30px)}to{opacity:1;transform:none}}
#snd{position:fixed;right:10px;bottom:10px;z-index:5;padding:6px 12px;border:1px solid var(--ion);border-radius:999px;background:rgba(7,10,36,.7);color:#f3f1ea;font:700 11px var(--mono);cursor:pointer}
</style></head>
<body>
<!-- launch __NONCE__ -->
<canvas id="c"></canvas>
<div id="title"></div>
<div id="count"></div>
<div id="hud"></div>
<div id="toasts"></div>
<button id="snd" type="button"></button>
<script>
const NAME=__NAME__, ACCENT=__ACCENT__, BG=__BG__;
document.documentElement.style.setProperty('--flare',ACCENT);
const cv=document.getElementById('c'),ctx=cv.getContext('2d');
const titleEl=document.getElementById('title'),countEl=document.getElementById('count');
const hud=document.getElementById('hud'),box=document.getElementById('toasts');
let W,H;
function size(){const d=Math.min(devicePixelRatio||1,2);W=innerWidth;H=innerHeight;
cv.width=W*d;cv.height=H*d;ctx.setTransform(d,0,0,d,0,0)}
addEventListener('resize',size);size();

const stars=Array.from({length:150},()=>({x:Math.random(),y:Math.random(),r:Math.random()*1.6+.3,tw:Math.random()*6}));
let parts=[],phase='morph',t0=null,vis=0,vel=0,lastCount=-1,last=0;
const clamp=(v,a=0,b=1)=>Math.min(b,Math.max(a,v));
const ease=t=>t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2;
const mix=(a,b,t)=>a.map((v,i)=>Math.round(v+(b[i]-v)*t));
const rgb=c=>'rgb('+c.join(',')+')';

// ---- sound (Web Audio, no files needed) ----
let AC=null,master=null,rum=null,muted=false;
const snd=document.getElementById('snd');
try{AC=new(window.AudioContext||window.webkitAudioContext)();master=AC.createGain();master.gain.value=.5;master.connect(AC.destination)}catch(e){}
function beep(f,d,type,vol){
  if(!AC||AC.state!=='running')return;
  const o=AC.createOscillator(),g=AC.createGain(),t=AC.currentTime;
  o.type=type||'sine';o.frequency.value=f;
  g.gain.setValueAtTime(vol||.2,t);g.gain.exponentialRampToValueAtTime(.001,t+d);
  o.connect(g);g.connect(master);o.start(t);o.stop(t+d);
}
function noise(){
  const n=AC.sampleRate*2,b=AC.createBuffer(1,n,AC.sampleRate),d=b.getChannelData(0);
  for(let i=0;i<n;i++)d[i]=Math.random()*2-1;
  const s=AC.createBufferSource();s.buffer=b;s.loop=true;return s;
}
function startRumble(){
  if(!AC||rum)return;
  const s=noise(),f=AC.createBiquadFilter();f.type='lowpass';f.frequency.value=240;
  rum=AC.createGain();rum.gain.value=0;s.connect(f);f.connect(rum);rum.connect(master);s.start();
}
function rumbleUpdate(ph){
  if(!AC||AC.state!=='running')return;
  if(ph==='count'||ph==='launch')startRumble();
  if(!rum)return;
  const g=ph==='launch'?.6*(1-clamp(altKm/110))+.03:ph==='count'?.12:0;   // thinner air = quieter
  rum.gain.setTargetAtTime(g,AC.currentTime,.15);
}
function boom(){
  if(!AC||AC.state!=='running')return;
  const s=noise(),f=AC.createBiquadFilter(),g=AC.createGain(),t=AC.currentTime;
  f.type='lowpass';f.frequency.value=500;g.gain.setValueAtTime(.9,t);g.gain.exponentialRampToValueAtTime(.001,t+1.4);
  s.connect(f);f.connect(g);g.connect(master);s.start(t);s.stop(t+1.5);
}
function sfx(big){
  if(big)[523,659,784,1047].forEach((f,i)=>setTimeout(()=>beep(f,.5,'sine',.22),i*130));
  else beep(880,.12,'triangle',.1);
}
function refresh(){snd.textContent=!AC?'NO AUDIO':AC.state!=='running'?'🔇 TAP FOR SOUND':muted?'🔇 SOUND OFF':'🔊 SOUND ON'}
snd.onclick=()=>{
  if(!AC)return;
  if(AC.state!=='running'){muted=false;master.gain.value=.5;AC.resume().then(refresh);return}
  muted=!muted;master.gain.setTargetAtTime(muted?0:.5,AC.currentTime,.02);refresh();
};
addEventListener('pointerdown',e=>{if(e.target!==snd&&AC&&AC.state==='suspended'&&!muted)AC.resume().then(refresh)});
setInterval(refresh,400);refresh();

// ---- flight physics (stylised, time-lapsed) ----
const C=299792458,SITE=[13.72,80.23];            // launch site: Sriharikota
let lt=0,T=0,ts=6,v=0,a=0,altKm=0,s=0,lat=SITE[0],lon=SITE[1],warp=null,hudOn=false;

const BODIES=[
 {n:'ISS',km:408,k:'station',x:.76,s:.05},
 {n:'THE MOON',km:384400,k:'moon',x:.22,s:.09},
 {n:'MARS',km:1e8,k:'mars',x:.78,s:.08},
 {n:'ASTEROID FIELD',km:3.5e8,k:'rocks',x:.3,s:.06},
 {n:'JUPITER',km:6.3e8,k:'gas',x:.74,s:.16},
 {n:'ALPHA CENTAURI',km:4.1e13,k:'star',x:.25,s:.06},
 {n:'SIRIUS',km:8.1e13,k:'star',x:.8,s:.07},
 {n:'BLACK HOLE',km:5e14,k:'bh',x:.3,s:.2}
];
function fd(km){
  if(km<1)return (km*1000).toFixed(0)+' m';
  if(km<10)return km.toFixed(2)+' km';
  if(km<1e6)return Math.round(km).toLocaleString('en-US')+' km';
  if(km<9.461e11)return (km/1.496e8).toFixed(2)+' AU';
  return (km/9.461e12).toFixed(2)+' ly';
}
function fv(x){return x<1000?x.toFixed(0)+' m/s':x<1e6?(x/1000).toFixed(2)+' km/s':(x/C*100).toFixed(1)+'% c'}
function ft(t){
  if(t>3.15e7)return (t/3.156e7).toFixed(1)+' yr';
  if(t>86400)return (t/86400).toFixed(1)+' d';
  const p=n=>String(Math.floor(n)).padStart(2,'0');
  return 'T+'+p(t/3600)+':'+p(t%3600/60)+':'+p(t%60);
}
const MS=[
 [()=>v>=343,'Mach 1: supersonic'],
 [()=>T>=60,'Max-Q: peak aerodynamic pressure, throttling down'],
 [()=>altKm>=12,'Troposphere cleared (12 km)'],
 [()=>altKm>=50,'Stratosphere cleared (50 km)'],
 [()=>altKm>=85,'Mesosphere cleared (85 km)'],
 [()=>altKm>=100,'SUCCESS: Passed the Kármán line (100 km). You are in space!',1],
 [()=>v>=7800,'Orbital velocity reached: 7.8 km/s'],
 [()=>altKm>=150,'Time-warp engaged: mission clock accelerating'],
 [()=>v>=11200,'Escape velocity reached: leaving Earth behind'],
 [()=>v>=.01*C,'Relativistic cruise: 1% the speed of light']
].concat(BODIES.map(b=>[()=>altKm>=b.km,'Passing '+b.n+' ('+fd(b.km)+')'])).map(m=>({t:m[0],m:m[1],big:m[2],done:false}));
function toast(msg,big){
  sfx(big);
  const d=document.createElement('div');d.className='t'+(big?' big':'');d.textContent=msg;box.appendChild(d);
  while(box.children.length>4)box.firstChild.remove();
  setTimeout(()=>d.remove(),big?7000:4500);
}
function step(dt){
  lt+=dt;
  if(warp===null&&altKm>=150)warp=lt;
  ts=warp===null?6:6*Math.exp((lt-warp)/2.4);
  const dts=dt*ts;T+=dts;
  a=Math.min(11/(1-Math.min(T,330)/420),40)*((T>60&&T<85)?.82:1);
  const vmax=.99*C;
  if(v>=vmax)a=0;
  v=Math.min(v+a*dts,vmax);
  altKm+=v*dts/1000;
  if(altKm<2000){
    s+=v*Math.sin(clamp(T/300)*1.47)*dts/1000;
    const d=s/6371,h=1.745,p1=SITE[0]*Math.PI/180;
    const p2=Math.asin(Math.sin(p1)*Math.cos(d)+Math.cos(p1)*Math.sin(d)*Math.cos(h));
    lat=p2*180/Math.PI;
    lon=SITE[1]+Math.atan2(Math.sin(h)*Math.sin(d)*Math.cos(p1),Math.cos(d)-Math.sin(p1)*Math.sin(p2))*180/Math.PI;
  }
  for(const m of MS)if(!m.done&&m.t()){m.done=true;toast(m.m,m.big)}
}
function drawHud(){
  const deep=altKm>=2000,row=(k,x)=>'<div><span>'+k+'</span><b>'+x+'</b></div>';
  hud.innerHTML='<h4>FLIGHT DATA · SRIHARIKOTA</h4>'+
   row('MISSION',ft(T))+row('TIME-LAPSE','×'+(ts>1e4?ts.toExponential(1):ts.toFixed(0)))+
   row('ALTITUDE',fd(altKm))+row('VELOCITY',fv(v))+
   row('ACCEL',a.toFixed(1)+' m/s² · '+(a/9.81).toFixed(1)+' g')+
   row('LATITUDE',deep?'deep space':Math.abs(lat).toFixed(3)+'° '+(lat>=0?'N':'S'))+
   row('LONGITUDE',deep?'deep space':Math.abs(lon).toFixed(3)+'° '+(lon>=0?'E':'W'))+
   row('FROM SPACE CTR',fd(Math.hypot(altKm,s)));
}

// ---- bodies ----
function circ(x,y,r,f){ctx.fillStyle=f;ctx.beginPath();ctx.arc(x,y,r,0,7);ctx.fill()}
function drawBody(b,u){
  const x=W*b.x,y=H*(-.25+1.5*u),r=b.s*H*(.5+.9*Math.sin(Math.PI*u));
  ctx.save();
  if(b.k==='station'){
    ctx.fillStyle='#d9d9e3';ctx.fillRect(x-r*.5,y-r*.12,r,r*.24);
    ctx.fillStyle='#4de8ff';ctx.fillRect(x-r*1.4,y-r*.4,r*.8,r*.8);ctx.fillRect(x+r*.6,y-r*.4,r*.8,r*.8);
  }else if(b.k==='moon'){
    circ(x,y,r,'#b9b7bd');circ(x-r*.3,y-r*.2,r*.18,'#8e8c94');circ(x+r*.25,y+r*.3,r*.25,'#9a98a0');circ(x+r*.4,y-r*.35,r*.12,'#8e8c94');
  }else if(b.k==='mars'){
    const g=ctx.createRadialGradient(x-r*.3,y-r*.3,r*.1,x,y,r);g.addColorStop(0,'#ff9a6a');g.addColorStop(1,'#8f3418');
    circ(x,y,r,g);circ(x+r*.2,y+r*.3,r*.2,'rgba(60,15,5,.35)');
  }else if(b.k==='rocks'){
    for(let i=0;i<10;i++)circ(x+Math.sin(i*12.9)*r*2,y+Math.cos(i*7.3)*r*1.3,r*(.14+.08*(i%3)),'#8b8794');
  }else if(b.k==='gas'){
    ctx.beginPath();ctx.arc(x,y,r,0,7);ctx.clip();
    ctx.fillStyle='#d9a877';ctx.fillRect(x-r,y-r,2*r,2*r);
    ['#b9714a','#efd3a8','#a65f3a','#e6c08e','#b9714a'].forEach((c,i)=>{ctx.fillStyle=c;ctx.fillRect(x-r,y-r+i*r*.4+r*.1,2*r,r*.2)});
  }else if(b.k==='star'){
    const g=ctx.createRadialGradient(x,y,0,x,y,r*2.4);g.addColorStop(0,'#fff');g.addColorStop(.25,'#ffe9a6');g.addColorStop(1,'rgba(255,200,80,0)');
    circ(x,y,r*2.4,g);
  }else{
    ctx.translate(x,y);ctx.rotate(-.35);ctx.scale(1,.28);
    ctx.strokeStyle='rgba(255,150,60,.95)';ctx.lineWidth=r*.2;ctx.shadowColor='#ff9a3d';ctx.shadowBlur=30;
    ctx.beginPath();ctx.arc(0,0,r*.95,0,7);ctx.stroke();
    ctx.setTransform(dpr(),0,0,dpr(),0,0);circ(x,y,r*.55,'#000');
    ctx.strokeStyle='rgba(255,200,120,.8)';ctx.lineWidth=2;ctx.beginPath();ctx.arc(x,y,r*.62,Math.PI*1.1,Math.PI*1.9);ctx.stroke();
  }
  ctx.restore();
  ctx.fillStyle='#fff';ctx.font='700 11px ui-monospace,monospace';ctx.textAlign='center';
  ctx.fillText(b.n+' · '+fd(b.km),x,y+Math.max(r*1.7,28));
}
function dpr(){return Math.min(devicePixelRatio||1,2)}

titleEl.textContent=NAME;
setTimeout(()=>titleEl.classList.add('up'),900);

function puff(x,y,big){
  for(let i=0;i<(big?5:2);i++)parts.push({x:x+(Math.random()-.5)*20,y,vx:(Math.random()-.5)*(big?160:50),
    vy:(big?120:30)+Math.random()*120,life:0,max:.8+Math.random()*(big?1.4:.7),r:(big?10:6)+Math.random()*10});
}

function rocket(x,y,rh,flame,now){
  const w=rh*.28;
  ctx.save();ctx.translate(x,y);
  if(flame>0){
    const len=rh*(.45+Math.random()*.2)*flame;
    const g=ctx.createLinearGradient(0,0,0,len);
    g.addColorStop(0,'#fff6c8');g.addColorStop(.35,'#ff9a3d');g.addColorStop(1,'rgba(255,60,20,0)');
    ctx.fillStyle=g;ctx.beginPath();ctx.moveTo(-w*.38,0);ctx.lineTo(w*.38,0);ctx.lineTo(0,len);ctx.fill();
  }
  ctx.fillStyle=ACCENT;
  for(const s of[-1,1]){ctx.beginPath();ctx.moveTo(s*w/2,-rh*.05);ctx.lineTo(s*w*1.05,rh*.02);ctx.lineTo(s*w/2,-rh*.42);ctx.fill()}
  const hg=ctx.createLinearGradient(-w/2,0,w/2,0);
  hg.addColorStop(0,'#b9b7c4');hg.addColorStop(.4,'#f3f1ea');hg.addColorStop(1,'#a3a1b4');
  ctx.fillStyle=hg;ctx.beginPath();
  ctx.moveTo(-w/2,0);ctx.lineTo(-w/2,-rh*.6);ctx.quadraticCurveTo(-w*.45,-rh*.9,0,-rh);
  ctx.quadraticCurveTo(w*.45,-rh*.9,w/2,-rh*.6);ctx.lineTo(w/2,0);ctx.closePath();ctx.fill();
  ctx.fillStyle=ACCENT;ctx.fillRect(-w/2,-rh*.08,w,rh*.05);
  ctx.fillStyle='#0d1238';ctx.strokeStyle='#4de8ff';ctx.lineWidth=2;
  ctx.beginPath();ctx.arc(0,-rh*.7,w*.17,0,7);ctx.fill();ctx.stroke();
  const on=Math.floor(now/180)%2===0;
  ctx.save();ctx.translate(0,-rh*.14);ctx.rotate(-Math.PI/2);
  ctx.font='800 '+(w*.26)+'px Unbounded,sans-serif';ctx.textAlign='left';ctx.textBaseline='middle';
  ctx.fillStyle=on?ACCENT:'#0d1238';ctx.shadowColor=on?ACCENT:'transparent';ctx.shadowBlur=on?12:0;
  ctx.fillText(NAME,0,0,rh*.4);ctx.restore();
  ctx.restore();
}

function frame(now){
  if(t0===null)t0=now;
  const dt=Math.min((now-last)/1000||0,.05);last=now;
  const el=(now-t0)/1000;
  const p=ease(clamp(el/2.2));
  let flame=0,shake=0;
  if(phase==='morph'&&el>2.2)phase='count';
  if(phase==='count'){
    if(!hudOn){hudOn=true;hud.classList.add('on')}
    const n=3-Math.floor(el-2.2);
    if(n>0){
      if(n!==lastCount){lastCount=n;beep(660,.18);countEl.textContent=n;countEl.classList.remove('pop');void countEl.offsetWidth;countEl.classList.add('pop')}
      flame=.25;shake=1.5;
    }else{phase='launch';titleEl.classList.add('flash');countEl.textContent='';beep(1040,.6,'square',.12);boom();toast('LIFTOFF!')}
  }
  if(phase==='launch'){vel=Math.min(vel+380*dt,1900);vis+=vel*dt;flame=1;shake=3;step(dt)}
  if(hudOn)drawHud();rumbleUpdate(phase);

  const k=clamp(altKm/110);
  const top=mix(mix(BG,[27,42,107],p),[2,3,14],k);
  const bot=mix(mix(BG,[255,138,92],p),[8,10,40],k);
  const g=ctx.createLinearGradient(0,0,0,H);g.addColorStop(0,rgb(top));g.addColorStop(1,rgb(bot));
  ctx.fillStyle=g;ctx.fillRect(0,0,W,H);

  const rise=Math.min(vis,H*.42),scroll=vis-rise;
  for(const s of stars){
    ctx.globalAlpha=(.4+.6*Math.abs(Math.sin(now/700+s.tw)))*(.4+.6*Math.max(k,.4));
    ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(s.x*W,(s.y*H+scroll*(.15+s.r*.2))%H,s.r,0,7);ctx.fill();
  }
  ctx.globalAlpha=1;

  if(phase==='launch')for(const b of BODIES){
    const u=Math.log10(Math.max(altKm,1e-9)/b.km)+.52;
    if(u>0&&u<1)drawBody(b,u);
  }

  const padY=H*.82+(1-p)*H*.25,gy=padY+scroll,ry=padY-rise,rh=Math.min(H*.3,230);
  ctx.fillStyle='#1a1d44';ctx.fillRect(0,gy,W,H*2);
  ctx.fillStyle='#2b2f6b';ctx.fillRect(W/2-70,gy,140,10);
  if(phase==='launch'&&Math.abs(altKm-100)<40){
    const ly=ry-(100-altKm)*9;
    ctx.save();ctx.setLineDash([10,8]);ctx.strokeStyle='#3ddc84';ctx.lineWidth=2;
    ctx.beginPath();ctx.moveTo(0,ly);ctx.lineTo(W,ly);ctx.stroke();
    ctx.fillStyle='#3ddc84';ctx.font='11px ui-monospace,monospace';ctx.textAlign='left';
    ctx.fillText('KÁRMÁN LINE · 100 km',12,ly-6);ctx.restore();
  }
  if(flame>0)puff(W/2,ry,phase==='launch');
  ctx.save();ctx.translate((Math.random()-.5)*shake,(Math.random()-.5)*shake);
  ctx.globalAlpha=clamp(p*1.5);
  rocket(W/2,ry,rh*(.6+.4*p),flame,now);
  ctx.restore();ctx.globalAlpha=1;

  for(let i=parts.length-1;i>=0;i--){
    const q=parts[i];q.life+=dt;q.x+=q.vx*dt;q.y+=q.vy*dt;
    const a2=1-q.life/q.max;if(a2<=0){parts.splice(i,1);continue}
    ctx.globalAlpha=a2*.7;ctx.fillStyle=a2>.6?'#ffb04d':'#c9c7d8';
    ctx.beginPath();ctx.arc(q.x,q.y,q.r*(1.6-a2),0,7);ctx.fill();
  }
  ctx.globalAlpha=1;
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);
</script></body></html>
"""


def hex_to_rgb(hex_color):
    h = hex_color.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def build_launch_html(name, accent, bg, nonce):
    # json.dumps makes the values safe to embed as JS literals
    safe = lambda v: json.dumps(v).replace("</", "<\\/")
    return (
        LAUNCH_HTML
        .replace("__NAME__", safe(name.upper()))
        .replace("__ACCENT__", safe(accent))
        .replace("__BG__", safe(hex_to_rgb(bg)))
        .replace("__NONCE__", str(nonce))
    )


def star_shadows(n, seed):
    """Random star positions as a CSS box-shadow list (used for the twinkling background)."""
    r = random.Random(seed)
    return ",".join(
        f"{r.randint(0, 100)}vw {r.randint(0, 100)}vh 0 {r.choice([0, 0, 1])}px "
        f"rgba(255,255,255,{r.choice([.5, .8, 1])})"
        for _ in range(n)
    )


def registration_text(u):
    return "\n".join([
        "NOVARIS - REGISTRATION FORM",
        "===========================",
        f"Name        : {u['name']}",
        f"Email       : {u['email']}",
        f"Age         : {u['age']}",
        f"Description : {u['description'] or '-'}",
        f"Registered  : {u['registered_at']} (via {u['method']})",
        "",
        "Welcome aboard, astronaut!",
    ])


EXPLORER_NAMES = ['SUN', 'MERCURY', 'VENUS', 'EARTH', 'MARS', 'JUPITER', 'SATURN', 'URANUS', 'NEPTUNE', 'PROXIMA CENTAURI', 'SIRIUS', 'BETELGEUSE', 'CRAB PULSAR', 'SAGITTARIUS A*', 'CYGNUS X-1', 'M87*', 'TON 618']

EXPLORER_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Unbounded:wght@800&display=swap" rel="stylesheet">
<style>
:root{--font:'Unbounded',system-ui,sans-serif;--mono:ui-monospace,Menlo,Consolas,monospace;--accent:__ACCENT__;--ion:#4de8ff}
html,body{margin:0;height:100%;background:transparent;color:#f3f1ea;font-family:var(--mono);overflow:hidden}
.screen{position:absolute;inset:0}.hidden{display:none!important}
.wrap{display:flex;flex-wrap:wrap;gap:16px;align-items:center;justify-content:center;height:100%;padding:48px 8px 8px;box-sizing:border-box;overflow:auto}
.tabs{position:absolute;top:8px;left:50%;transform:translateX(-50%);display:flex;gap:6px;z-index:3}
.tab{padding:7px 14px;border:1px solid var(--accent);border-radius:999px;background:rgba(7,10,36,.6);color:#f3f1ea;font:800 10px var(--font);cursor:pointer}
.tab.on{background:var(--accent)}
svg{flex:1 1 380px;max-width:560px;max-height:100%;aspect-ratio:1}
.o{transform-origin:400px 400px;animation:spin linear infinite}
svg:hover .o{animation-play-state:paused}
@keyframes spin{to{transform:rotate(360deg)}}
.orbit{fill:none;stroke:rgba(255,255,255,.14);stroke-width:1}
.p{transition:filter .2s}.p.sel{filter:drop-shadow(0 0 10px #fff)}
.hit{fill:transparent;cursor:pointer}
#panel{flex:1 1 260px;max-width:340px;padding:16px;border:1px solid var(--accent);border-radius:14px;background:rgba(7,10,36,.65);font-size:13px;line-height:1.6}
#panel h2{margin:0 0 8px;font:800 1.1rem var(--font);color:var(--accent)}
#panel div{display:flex;justify-content:space-between;gap:10px;border-bottom:1px solid rgba(255,255,255,.08)}
#panel span{opacity:.65}#panel b{text-align:right}#panel p{margin:10px 0 0;opacity:.9}
.btn{padding:10px 14px;border:0;border-radius:10px;background:var(--accent);color:#fff;font:800 11px var(--font);cursor:pointer}
.btn.alt{background:rgba(7,10,36,.75);border:1px solid var(--ion)}
#panel .btn{margin-top:12px;width:100%}
canvas{position:absolute;inset:0;width:100%;height:100%;touch-action:none}
#shud{position:absolute;left:10px;top:10px;width:min(52vw,280px);padding:8px 10px;border:1px solid var(--ion);border-radius:10px;background:rgba(7,10,36,.62);font:11px/1.55 var(--mono)}
#shud h4{margin:0 0 4px;font:800 10px var(--font);color:var(--ion);letter-spacing:.08em}
#shud div{display:flex;justify-content:space-between;gap:8px}#shud span{opacity:.7}
#bar{height:5px;border-radius:5px;background:rgba(255,255,255,.15);margin-top:6px}
#bar i{display:block;height:100%;width:0;border-radius:5px;background:var(--ion)}
#cnt{position:absolute;left:50%;top:40%;transform:translate(-50%,-50%);font:800 clamp(4rem,18vw,8rem) var(--font);color:var(--ion)}
#msg{position:absolute;left:50%;top:14%;transform:translateX(-50%);width:90%;text-align:center;font:800 clamp(1rem,4vw,1.8rem) var(--font);text-shadow:0 0 20px var(--ion)}
#ctl{position:absolute;left:50%;bottom:12px;transform:translateX(-50%);display:flex;gap:8px;flex-wrap:wrap;justify-content:center;width:96%}
#snd{position:absolute;right:10px;top:10px;z-index:4}
@media (prefers-reduced-motion:reduce){.o{animation:none}}
</style></head>
<body>
<!-- explorer __NONCE__ -->
<div id="map" class="screen">
  <div class="tabs"><button class="tab on" data-t="S">SOLAR SYSTEM</button><button class="tab" data-t="D">DEEP SPACE</button></div>
  <div class="wrap"><svg id="sys" viewBox="0 0 800 800" role="img" aria-label="Space map"></svg><div id="panel"></div></div>
</div>
<div id="stage" class="screen hidden">
  <canvas id="cv"></canvas><button class="btn alt" id="snd" type="button"></button><div id="shud"></div><div id="cnt"></div><div id="msg"></div>
  <div id="ctl">
    <button class="btn alt" id="fwd">⬆ WALK</button><button class="btn alt" id="bwd">⬇ BACK</button>
    <button class="btn" id="step">🧑‍🚀 STEP OUT</button><button class="btn alt" id="skip">SKIP ▶</button>
    <button class="btn alt" id="back">↩ BACK TO MAP</button>
  </div>
</div>
<script>
const $=id=>document.getElementById(id);
const ACCENT='__ACCENT__',START=__START__;
const clamp=(v,a=0,b=1)=>Math.min(b,Math.max(a,v));
const mix=(a,b,t)=>a.map((v,i)=>Math.round(v+(b[i]-v)*t));
const rgb=c=>'rgb('+c.join(',')+')';
function sh(h,f){const n=parseInt(h.slice(1),16);return rgb([(n>>16&255)*f,(n>>8&255)*f,(n&255)*f].map(Math.round))}
function fd(km){
  if(km<1e4)return Math.round(km).toLocaleString('en-US')+' km';
  if(km<1e8)return Math.round(km/1e6).toLocaleString('en-US')+' M km';
  if(km<9.461e11)return (km/1.496e8).toFixed(2)+' AU';
  const ly=km/9.461e12;
  return ly>=1e9?(ly/1e9).toFixed(1)+' B ly':ly>=1e6?(ly/1e6).toFixed(1)+' M ly':ly>=100?Math.round(ly).toLocaleString('en-US')+' ly':ly.toFixed(2)+' ly';
}

// ---------- DATA ----------
const LB={
 P:['Diameter','Distance from Sun','Day length','Year length','Moons','Avg. temperature'],
 S:['Diameter','Distance from Earth','Surface temp','Mass','Type'],
 B:['Mass','Distance from Earth','Event horizon','Type','Famous for']};
function mk(n,k,g,c,r,orb,per,km,st,f,hud,v,x,y,d){return{n,k,g,c,r,orb,per,km,st,f,hud,v,x,y,d}}
const ALL=[
mk('SUN','star','P','#ffb830',34,0,0,1.496e8,['1,391,000 km','—','~25 days (equator)','—','—','5,500 °C (surface)'],'Holds 99.8% of the solar system’s mass.',['Shielded orbit at 0.1 AU','Surface 5,500 °C','Solar filter: ON'],{col:'#ffe08a',glow:'#ff9a30',rad:.5}),
mk('MERCURY','rock','P','#b1a99f',4,60,9,9.17e7,['4,879 km','57.9 M km','59 Earth days','88 days','0','167 °C'],'Swings from −180 °C at night to 430 °C by day.',['Gravity 3.7 m/s²','No atmosphere','Sun looks 3× bigger'],{sky:['#000','#07070b'],gnd:'#7a746e',ridge:'#5d5853',sun:.03,stars:1}),
mk('VENUS','rock','P','#e8c07a',7,100,15,4.14e7,['12,104 km','108.2 M km','243 Earth days (backwards)','225 days','0','464 °C'],'Hotter than Mercury thanks to a runaway greenhouse effect.',['Gravity 8.9 m/s²','464 °C · 92 bar','Sulfuric acid clouds'],{sky:['#7a4d12','#e6aa55'],gnd:'#6b4a2e',ridge:'#8c6334',sun:0,stars:0,atm:'rgba(230,170,80,.5)'}),
mk('EARTH','rock','P','#4d9de0',7.5,140,21,400,['12,742 km','149.6 M km','24 hours','365.25 days','1','15 °C'],'The only world known to host life.',['Gravity 9.8 m/s²','15 °C · 1 bar','Air: 21% oxygen'],{sky:['#2d74d6','#cfe8ff'],gnd:'#4d7a3a',ridge:'#5d7fa0',sun:.014,stars:0,atm:'rgba(110,170,255,.55)',spots:[[-.3,-.1,.3,'#3f8f4f'],[.35,.25,.22,'#3f8f4f'],[.05,-.78,.2,'#ffffff']]}),
mk('MARS','rock','P','#d1553a',5,180,29,7.8e7,['6,779 km','227.9 M km','24 h 37 min','687 days','2','−65 °C'],'Home to Olympus Mons, a volcano about 22 km high.',['Gravity 3.7 m/s²','−65 °C','Air: CO₂, very thin'],{sky:['#b9805a','#f0cba6'],gnd:'#a4512d',ridge:'#85452a',sun:.009,stars:0,atm:'rgba(240,160,110,.35)',spots:[[.1,-.8,.18,'#f2e6e0'],[-.25,.2,.25,'#9c4527']]}),
mk('JUPITER','gas','P','#d9a877',18,228,46,6.29e8,['139,820 km','778.5 M km','9 h 56 min','11.9 years','95+','−110 °C'],'Its Great Red Spot is a storm wider than Earth.',['Orbiting above the clouds','Cloud-top gravity 24.8 m/s²','Radiation: severe'],{bands:['#d9a877','#b9714a','#efd3a8','#a65f3a'],rad:.55}),
mk('SATURN','gas','P','#e6d0a0',14,285,66,1.28e9,['116,460 km','1.43 B km','10 h 42 min','29.4 years','274+','−140 °C'],'Less dense than water. It would float in a big enough bath.',['Orbiting above the clouds','Ring system: 282,000 km wide','Density: 0.69 g/cm³'],{bands:['#e6d0a0','#cdb78a','#f0e2bb'],rad:.5,ring:1}),
mk('URANUS','gas','P','#8fe0e6',10,335,90,2.72e9,['50,724 km','2.87 B km','17 h (backwards)','84 years','28+','−195 °C'],'Spins on its side, tilted about 98°.',['Orbiting an ice giant','Axial tilt 98°','Coldest planet atmosphere'],{bands:['#8fe0e6','#7fd2da','#a0eef2'],rad:.5}),
mk('NEPTUNE','gas','P','#4c6fe0',10,378,120,4.35e9,['49,244 km','4.50 B km','16 h','164.8 years','16','−200 °C'],'Winds near 2,000 km/h, the fastest in the solar system.',['Orbiting an ice giant','Winds ~2,000 km/h','Sunlight: 900× dimmer'],{bands:['#4c6fe0','#3f5fc7','#6584ee'],rad:.5}),
mk('PROXIMA CENTAURI','star','S','#ff6a4d',8,0,0,4.02e13,['~200,000 km','4.24 ly','3,042 °C','0.12 Suns','Red dwarf'],'The nearest star to the Sun. Its planet Proxima b sits in the habitable zone.',['Red dwarf · flares often','Planet Proxima b nearby','Flare shield: ON'],{col:'#ff8a6a',glow:'#ff3b1d',rad:.12},330,470,'4.24 ly'),
mk('SIRIUS','star','S','#cfe3ff',10,0,0,8.14e13,['~2.4 M km','8.6 ly','9,940 °C','2.06 Suns','Blue-white star'],'The brightest star in our night sky. It has a faint white dwarf companion.',['Blue-white main sequence','25× brighter than the Sun','Visor dimmed 99.9%'],{col:'#dcebff',glow:'#6fa8ff',rad:.2},455,535,'8.6 ly'),
mk('BETELGEUSE','star','S','#ff8a3d',14,0,0,5.2e15,['~1 billion km','~550 ly','3,600 °C','~16–19 Suns','Red supergiant'],'It could explode as a supernova any time in the next 100,000 years.',['Red supergiant','Would swallow Jupiter’s orbit','Visor dimmed 99%'],{col:'#ff9a55',glow:'#ff4d1a',rad:.8},245,300,'~550 ly'),
mk('CRAB PULSAR','star','S','#bfe9ff',7,0,0,6.15e16,['~20 km','~6,500 ly','~1.6 million K','1.4 Suns','Neutron star'],'A city-sized star spinning 30 times a second, born in the supernova of 1054 CE.',['Spins 30× per second','Radiation: extreme','Beam shield: ON'],{col:'#bfe9ff',glow:'#6ab8ff',rad:.05,pulsar:1},610,190,'~6,500 ly'),
mk('SAGITTARIUS A*','bh','B','#ff9a3d',9,0,0,2.52e17,['4.3 million Suns','~26,700 ly','~25 million km across','Supermassive black hole','The heart of our Milky Way, imaged in 2022'],'Stars orbit it at thousands of km/s. Its first image arrived in 2022.',['Safe orbit: 50× the horizon','Time runs ~3% slower','Tides: survivable'],{disc:'#ffb36b',rad:.35},400,400,'26,700 ly'),
mk('CYGNUS X-1','bh','B','#9fd0ff',7,0,0,6.8e16,['21 Suns','~7,200 ly','~120 km across','Stellar-mass black hole','One of the first black holes ever confirmed'],'It is stripping gas from a blue supergiant star. Hawking famously bet against it being a black hole.',['Safe orbit: 100× the horizon','Gas stream from companion','Tides: lethal inside 1,000 km'],{disc:'#9fd0ff',rad:.22},560,320,'7,200 ly'),
mk('M87*','bh','B','#ff7a3d',10,0,0,5.06e20,['6.5 billion Suns','~53.5 million ly','~38 billion km across','Supermassive black hole','The first black hole ever photographed (2019)'],'Its shadow is bigger than our whole solar system, and it fires a jet 5,000 light-years long.',['Safe orbit: 20× the horizon','Relativistic jet nearby','Tides: gentle'],{disc:'#ff9a3d',rad:.45},650,620,'53.5 M ly'),
mk('TON 618','bh','B','#ffd9a8',11,0,0,9.8e22,['40–66 billion Suns','~10.4 billion ly','~250–400 billion km across','Ultramassive black hole','Powers one of the brightest quasars known'],'One of the most massive black holes ever found, so far away its light left before Earth existed.',['Safe orbit: 10× the horizon','Quasar glare: blinding','Tides: gentle'],{disc:'#ffe3b8',rad:.6},130,120,'10.4 B ly')
];
const NAMES=ALL.map(b=>b.n);

// ---------- MAP ----------
const NS='http://www.w3.org/2000/svg',svg=$('sys'),panel=$('panel');
let tab='S',sel=-1,dots={},wasSel=false,ptype='mouse';
const el=(t,a,p)=>{const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);(p||svg).appendChild(e);return e};
function select(i){
  sel=i;for(const k in dots)dots[k].classList.toggle('sel',+k===i);
  const b=ALL[i];
  panel.innerHTML='<h2>'+b.n+'</h2>'+LB[b.g].map((l,k)=>'<div><span>'+l+'</span><b>'+b.st[k]+'</b></div>').join('')+'<p>'+b.f+'</p><button class="btn" id="go">🚀 TRAVEL TO '+b.n+'</button>';
  $('go').onclick=()=>go(i);
}
function buildMap(){
  svg.innerHTML='';dots={};sel=-1;
  if(tab==='D'){
    [[340,110,-25,.10],[300,90,35,.08],[240,70,-70,.07]].forEach(a=>el('ellipse',{cx:400,cy:400,rx:a[0],ry:a[1],transform:'rotate('+a[2]+' 400 400)',fill:'rgba(124,77,255,'+a[3]+')'}));
    for(let k=0;k<110;k++)el('circle',{cx:Math.random()*800,cy:Math.random()*800,r:Math.random()*1.3+.3,fill:'#fff',opacity:Math.random()*.7+.2});
  }
  ALL.forEach((b,i)=>{
    if((tab==='S')!==(b.g==='P'))return;
    let host=svg,x=b.x,y=b.y;
    if(tab==='S'){
      x=400+b.orb;y=400;
      if(b.orb){
        el('circle',{class:'orbit',cx:400,cy:400,r:b.orb});
        host=el('g',{class:'o',style:'animation-duration:'+b.per+'s;animation-delay:-'+(i*7.3%b.per).toFixed(1)+'s'});
      }
      if(b.n==='SATURN')el('circle',{cx:x,cy:y,r:b.r*1.7,fill:'none',stroke:'#cdb78a','stroke-width':2,opacity:.8},host);
    }else if(b.k==='bh'){
      el('circle',{cx:x,cy:y,r:b.r*2,fill:'none',stroke:b.c,'stroke-width':2,opacity:.7});
    }else{
      el('circle',{cx:x,cy:y,r:b.r*2.6,fill:b.c,opacity:.22});
    }
    const dot=el('circle',{class:'p',cx:x,cy:y,r:b.r,fill:b.k==='bh'?'#000':b.c,stroke:b.k==='bh'?b.c:'none','stroke-width':2},host);
    if(b.n==='SUN')dot.style.filter='drop-shadow(0 0 18px #ffb830)';
    dots[i]=dot;
    if(tab==='D'){const tx=el('text',{x:x,y:y+b.r*2.6+13,'text-anchor':'middle',fill:'#fff','font-size':11,opacity:.85});tx.textContent=b.n+' · '+b.d}
    const hit=el('circle',{class:'hit',cx:x,cy:y,r:Math.max(b.r+7,16)},host);
    hit.addEventListener('pointerenter',e=>{ptype=e.pointerType;wasSel=sel===i;select(i)});
    hit.addEventListener('click',()=>{if(ptype==='touch'&&!wasSel)return;go(i)});
  });
  panel.innerHTML='<h2>EXPLORE</h2><p>Hover over a world, star or black hole for its stats, then click it to fly there. On touch screens, tap once for stats and again to travel.</p>';
}
document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{
  document.querySelectorAll('.tab').forEach(o=>o.classList.toggle('on',o===t));tab=t.dataset.t;buildMap();
});
buildMap();

// ---------- STAGE ----------
const cv=$('cv'),cx=cv.getContext('2d'),shud=$('shud'),cnt=$('cnt'),msg=$('msg');
let W,H,F,view='map',B=null,t0=0,last=0,arrived=false;
function size(){const d=Math.min(devicePixelRatio||1,2);W=innerWidth;H=innerHeight;cv.width=W*d;cv.height=H*d;cx.setTransform(d,0,0,d,0,0);F=W*.62}
addEventListener('resize',size);size();
const SK=Array.from({length:260},()=>{const az=Math.random()*6.283,e=Math.asin(Math.random()*2-1);
  return{a:Math.random()*6.283,r:Math.random(),dx:Math.cos(e)*Math.sin(az),dy:Math.sin(e),dz:Math.cos(e)*Math.cos(az),tw:Math.random()*6}});
function ui(a){['fwd','bwd','step','skip','back'].forEach(k=>$(k).classList.toggle('hidden',!a.includes(k)))}
function row(k,v){return '<div><span>'+k+'</span><b>'+v+'</b></div>'}
function disc(x,y,r,f){cx.fillStyle=f;cx.beginPath();cx.arc(x,y,r,0,7);cx.fill()}

function go(i){
  B=ALL[i];view='travel';arrived=false;t0=performance.now();last=t0;ac();stopAll();sf={};
  $('map').classList.add('hidden');$('stage').classList.remove('hidden');size();
  cnt.textContent='';msg.textContent='';$('step').textContent=B.k==='rock'?'🧑‍🚀 STEP OUT':'🧑‍🚀 SPACEWALK';
  ui(['skip','back']);requestAnimationFrame(loop);
}
$('skip').onclick=()=>{t0=performance.now()-20500};
$('back').onclick=()=>{stopAll();view='map';$('stage').classList.add('hidden');$('map').classList.remove('hidden')};
$('step').onclick=()=>stepOut();
function loop(now){
  if(view==='map')return;
  const dt=Math.min((now-last)/1000||0,.05);last=now;
  if(view==='travel')travel(now);else fp(now,dt);
  requestAnimationFrame(loop);
}

// ---------- SOUND (Web Audio, no files needed) ----------
let AC=null,M=null,NB=null,S={},sf={},muted=false;
const sb=$('snd');
function ac(){
  if(!AC){try{AC=new(window.AudioContext||window.webkitAudioContext)();M=AC.createGain();M.gain.value=.5;M.connect(AC.destination)}catch(e){}}
  if(AC&&AC.state==='suspended'&&!muted)AC.resume();
  return !!AC&&AC.state==='running';
}
const on=()=>!!AC&&AC.state==='running';
function nbuf(){
  if(!NB){const n=AC.sampleRate*2;NB=AC.createBuffer(1,n,AC.sampleRate);const d=NB.getChannelData(0);for(let i=0;i<n;i++)d[i]=Math.random()*2-1}
  return NB;
}
function beep(f,d,type,vol){
  if(!on())return;
  const o=AC.createOscillator(),g=AC.createGain(),t=AC.currentTime;
  o.type=type||'sine';o.frequency.value=f;g.gain.setValueAtTime(vol||.2,t);g.gain.exponentialRampToValueAtTime(.001,t+d);
  o.connect(g);g.connect(M);o.start(t);o.stop(t+d);
}
function burst(freq,d,vol,type){
  if(!on())return;
  const s=AC.createBufferSource(),f=AC.createBiquadFilter(),g=AC.createGain(),t=AC.currentTime;
  s.buffer=nbuf();f.type=type||'lowpass';f.frequency.value=freq;
  g.gain.setValueAtTime(vol,t);g.gain.exponentialRampToValueAtTime(.001,t+d);
  s.connect(f);f.connect(g);g.connect(M);s.start(t);s.stop(t+d+.05);
}
function sweep(a,b,d){
  if(!on())return;
  const o=AC.createOscillator(),g=AC.createGain(),t=AC.currentTime;
  o.type='sawtooth';o.frequency.setValueAtTime(a,t);o.frequency.exponentialRampToValueAtTime(b,t+d);
  g.gain.setValueAtTime(.001,t);g.gain.exponentialRampToValueAtTime(.15,t+d*.6);g.gain.exponentialRampToValueAtTime(.001,t+d);
  o.connect(g);g.connect(M);o.start(t);o.stop(t+d);
}
function chime(){[523,659,784,1047].forEach((f,i)=>setTimeout(()=>beep(f,.6,'sine',.22),i*140))}
function cont(k,type,freq,q){
  if(S[k])return S[k];
  const s=AC.createBufferSource(),f=AC.createBiquadFilter(),g=AC.createGain();
  s.buffer=nbuf();s.loop=true;f.type=type;f.frequency.value=freq;f.Q.value=q||1;g.gain.value=0;
  s.connect(f);f.connect(g);g.connect(M);s.start();
  return S[k]={s:s,f:f,g:g};
}
function drone(freqs,type,vol){
  const os=freqs.map(f=>{const o=AC.createOscillator();o.type=type;o.frequency.value=f;return o}),g=AC.createGain();
  g.gain.value=0;os.forEach(o=>{o.connect(g);o.start()});g.connect(M);g.gain.setTargetAtTime(vol,AC.currentTime,1);
  S.dr={s:{stop(){os.forEach(o=>o.stop())}},g:g};
}
function stopAll(){
  if(!AC)return;
  for(const k in S){try{S[k].g.gain.setTargetAtTime(0,AC.currentTime,.05);const s=S[k].s;setTimeout(()=>{try{s.stop()}catch(e){}},300)}catch(e){}}
  S={};
}
function sndTravel(T,asc,cru,dec,w){
  if(!on())return;
  const t=AC.currentTime,n=T<3?3-Math.floor(T):0;
  if(n&&sf.n!==n){sf.n=n;beep(660,.18,'sine',.25)}
  if(T>=3&&!sf.go){sf.go=1;burst(500,1.4,.9);beep(1040,.5,'square',.1)}
  if(T>=6.8&&!sf.warp){sf.warp=1;sweep(200,1400,1.1)}
  if(T>=20&&!sf.arr){sf.arr=1;chime()}
  cont('rum','lowpass',220).g.gain.setTargetAtTime(T<3?.1:T<7?.55*(1-asc*.7):.12*(1-dec),t,.15);
  const wp=cont('warp','bandpass',600,.7);
  wp.f.frequency.setTargetAtTime(300+w*1800,t,.2);wp.g.gain.setTargetAtTime(w*.4,t,.2);
}
function sndFp(now,mv,ground){
  if(!on())return;
  const t=AC.currentTime,v=B.v;
  cont('br','bandpass',900,.8).g.gain.setTargetAtTime(Math.max(0,Math.sin(now/3200*6.283))*.07,t,.1);   // helmet breathing
  if(ground){
    const wd={EARTH:[500,.12],MARS:[260,.1],VENUS:[110,.3]}[B.n];                                      // Mercury: airless, silent
    if(wd)cont('wind','lowpass',wd[0]).g.gain.setTargetAtTime(wd[1]*(.6+.4*Math.sin(now/2300)),t,.3);
    if(mv&&(!sf.st||now-sf.st>480)){sf.st=now;burst(180,.12,.45)}                                       // footsteps
  }else{
    if(!S.dr){
      if(B.k==='bh')drone([32,33,64],'sine',.16);else if(B.k==='star')drone([110,164,220],'sine',.05);else drone([55,82.5],'sine',.1);
    }
    if(v.pulsar&&(!sf.tk||now-sf.tk>262)){sf.tk=now;beep(1800,.03,'square',.05)}                       // pulsar ticks
  }
}
function sref(){sb.textContent=!AC?'🔊 SOUND':AC.state!=='running'?'🔇 TAP FOR SOUND':muted?'🔇 SOUND OFF':'🔊 SOUND ON'}
sb.onclick=()=>{
  ac();if(!AC)return;
  if(AC.state!=='running'){muted=false;M.gain.value=.5;AC.resume().then(sref);return}
  muted=!muted;M.gain.setTargetAtTime(muted?0:.5,AC.currentTime,.03);sref();
};
addEventListener('pointerdown',e=>{if(e.target!==sb)ac()});
setInterval(sref,500);sref();

// ---------- drawing helpers ----------
function rocketDraw(x,y,rh,flame,now){
  const w=rh*.28;cx.save();cx.translate(x,y);
  if(flame>0){
    const len=rh*(.45+Math.random()*.2)*flame,g=cx.createLinearGradient(0,0,0,len);
    g.addColorStop(0,'#fff6c8');g.addColorStop(.35,'#ff9a3d');g.addColorStop(1,'rgba(255,60,20,0)');
    cx.fillStyle=g;cx.beginPath();cx.moveTo(-w*.38,0);cx.lineTo(w*.38,0);cx.lineTo(0,len);cx.fill();
  }
  cx.fillStyle=ACCENT;
  for(const s of[-1,1]){cx.beginPath();cx.moveTo(s*w/2,-rh*.05);cx.lineTo(s*w*1.05,rh*.02);cx.lineTo(s*w/2,-rh*.42);cx.fill()}
  const hg=cx.createLinearGradient(-w/2,0,w/2,0);
  hg.addColorStop(0,'#b9b7c4');hg.addColorStop(.4,'#f3f1ea');hg.addColorStop(1,'#a3a1b4');
  cx.fillStyle=hg;cx.beginPath();cx.moveTo(-w/2,0);cx.lineTo(-w/2,-rh*.6);cx.quadraticCurveTo(-w*.45,-rh*.9,0,-rh);
  cx.quadraticCurveTo(w*.45,-rh*.9,w/2,-rh*.6);cx.lineTo(w/2,0);cx.closePath();cx.fill();
  cx.fillStyle=ACCENT;cx.fillRect(-w/2,-rh*.08,w,rh*.05);
  cx.fillStyle='#0d1238';cx.strokeStyle='#4de8ff';cx.lineWidth=2;cx.beginPath();cx.arc(0,-rh*.7,w*.17,0,7);cx.fill();cx.stroke();
  cx.save();cx.translate(0,-rh*.14);cx.rotate(-Math.PI/2);cx.font='800 '+(w*.22)+'px ui-monospace,monospace';
  cx.textBaseline='middle';cx.fillStyle=ACCENT;cx.fillText('NOVARIS',0,0,rh*.4);cx.restore();
  cx.restore();
}
function drawBody(x,y,r,b,now){
  const v=b.v;cx.save();
  if(b.k==='bh'){
    cx.save();cx.translate(x,y);cx.rotate(-.3);cx.scale(1,.3);
    cx.shadowColor=v.disc;cx.shadowBlur=r*.3;cx.strokeStyle=v.disc;cx.lineWidth=r*.3;
    cx.beginPath();cx.arc(0,0,r*1.15,Math.PI,2*Math.PI);cx.stroke();cx.restore();
    disc(x,y,r*.62,'#000');
    cx.strokeStyle='rgba(255,230,190,.9)';cx.lineWidth=Math.max(1.5,r*.03);cx.beginPath();cx.arc(x,y,r*.64,0,7);cx.stroke();
    cx.save();cx.translate(x,y);cx.rotate(-.3);cx.scale(1,.3);cx.shadowColor=v.disc;cx.shadowBlur=r*.3;
    cx.strokeStyle=v.disc;cx.lineWidth=r*.3;cx.beginPath();cx.arc(0,0,r*1.15,0,Math.PI);cx.stroke();cx.restore();
    cx.strokeStyle=v.disc;cx.globalAlpha=.75;cx.lineWidth=r*.09;cx.beginPath();cx.arc(x,y,r*.82,Math.PI*1.08,Math.PI*1.92);cx.stroke();
  }else if(b.k==='star'){
    const g=cx.createRadialGradient(x,y,0,x,y,r*3);
    g.addColorStop(0,'#fff');g.addColorStop(.22,v.col);g.addColorStop(.4,v.glow+'99');g.addColorStop(1,v.glow+'00');
    disc(x,y,r*3,g);
    if(v.pulsar){
      const a=now*.012;cx.strokeStyle='rgba(191,233,255,.85)';cx.lineWidth=Math.max(2,r*.08);
      for(const s of[0,Math.PI]){cx.beginPath();cx.moveTo(x+Math.cos(a+s)*r*.2,y+Math.sin(a+s)*r*.2);cx.lineTo(x+Math.cos(a+s)*r*6,y+Math.sin(a+s)*r*6);cx.stroke()}
    }
  }else{
    if(v.ring){cx.save();cx.translate(x,y);cx.rotate(-.35);cx.scale(1,.28);cx.strokeStyle='rgba(205,183,138,.85)';cx.lineWidth=r*.22;
      cx.beginPath();cx.arc(0,0,r*1.7,Math.PI,2*Math.PI);cx.stroke();cx.restore()}
    cx.save();cx.beginPath();cx.arc(x,y,r,0,7);cx.clip();
    if(b.k==='gas'){
      cx.fillStyle=v.bands[0];cx.fillRect(x-r,y-r,2*r,2*r);
      for(let i=0;i<9;i++){cx.fillStyle=v.bands[i%(v.bands.length-1)+1];cx.fillRect(x-r,y-r+i*r*.24+Math.sin(now/3000+i)*r*.02,2*r,r*.13)}
    }else{
      cx.fillStyle=b.c;cx.fillRect(x-r,y-r,2*r,2*r);
      (v.spots||[]).forEach(s=>disc(x+s[0]*r,y+s[1]*r,s[2]*r,s[3]));
    }
    const sg=cx.createRadialGradient(x-r*.4,y-r*.4,r*.1,x,y,r*1.05);
    sg.addColorStop(0,'rgba(255,255,255,.18)');sg.addColorStop(1,'rgba(0,0,0,.7)');
    cx.fillStyle=sg;cx.fillRect(x-r,y-r,2*r,2*r);cx.restore();
    if(v.atm){cx.strokeStyle=v.atm;cx.lineWidth=r*.05;cx.beginPath();cx.arc(x,y,r*1.02,0,7);cx.stroke()}
    if(v.ring){cx.save();cx.translate(x,y);cx.rotate(-.35);cx.scale(1,.28);cx.strokeStyle='rgba(205,183,138,.85)';cx.lineWidth=r*.22;
      cx.beginPath();cx.arc(0,0,r*1.7,0,Math.PI);cx.stroke();cx.restore()}
  }
  cx.restore();
}

// ---------- TRAVEL ----------
function travel(now){
  const T=(now-t0)/1000,asc=clamp((T-3)/4),cru=clamp((T-7)/10),dec=clamp((T-17)/3);
  const top=mix([27,42,107],[2,3,14],asc),bot=mix([255,138,92],[3,4,18],asc);
  const g=cx.createLinearGradient(0,0,0,H);g.addColorStop(0,rgb(top));g.addColorStop(1,rgb(bot));
  cx.fillStyle=g;cx.fillRect(0,0,W,H);
  const w=clamp((T-6.5)/1.5)*(1-dec),R=Math.hypot(W,H)/2;
  sndTravel(T,asc,cru,dec,w);
  cx.strokeStyle='#fff';cx.fillStyle='#fff';
  for(const s of SK){
    const rr=(s.r+T*(.04+w*.8))%1,x=W/2+Math.cos(s.a)*rr*R,y=H/2+Math.sin(s.a)*rr*R;
    cx.globalAlpha=(.25+rr*.75)*(asc*.8+.2);
    if(w>.05){const l=w*rr*R*.12;cx.lineWidth=1+rr*1.5;cx.beginPath();cx.moveTo(x,y);cx.lineTo(x-Math.cos(s.a)*l,y-Math.sin(s.a)*l);cx.stroke()}
    else cx.fillRect(x,y,1.5,1.5);
  }
  cx.globalAlpha=1;
  if(cru>0){const Rm=Math.min(W,H)*.34;drawBody(W/2,H*.3,2+(Rm-2)*Math.pow(cru,3.5)*(1+.2*dec),B,now)}
  const gy=H*.84+asc*H*.45;
  if(gy<H){cx.fillStyle='#1a1d44';cx.fillRect(0,gy,W,H);cx.fillStyle='#2b2f6b';cx.fillRect(W/2-70,gy,140,8)}
  const rh=Math.min(H*.26,200),flame=T<3?.25:T>20?.1:1-dec*.8,sk=T<7?(T<3?1.5:3):1;
  cx.save();cx.translate((Math.random()-.5)*sk,(Math.random()-.5)*sk);
  rocketDraw(W/2,H*.84-asc*H*.1,rh,flame,now);cx.restore();
  cnt.textContent=T<3?String(3-Math.floor(T)):'';
  const rem=T<7?B.km:B.km*Math.pow(1-cru,2.2),rate=(T>=7&&cru<1)?B.km*2.2*Math.pow(1-cru,1.2)/10:0,wp=rate/299792;
  const st=T<3?'COUNTDOWN':T<7?'ASCENT':T<17?'WARP CRUISE':T<20?'DECELERATING':'ARRIVED';
  shud.innerHTML='<h4>NOVARIS · FLIGHT</h4>'+row('DESTINATION',B.n)+row('STATUS',st)+row('DISTANCE',T>=20?'0':fd(rem))+
    row('WARP',wp?'×'+(wp<10?wp.toFixed(1):wp.toExponential(1))+' c':'—')+row('ETA',T<17?Math.max(0,Math.ceil(17-T))+' s':'0 s')+
    '<div id="bar"><i style="width:'+Math.round((T<7?0:cru)*100)+'%"></i></div>';
  if(T>=20&&!arrived){arrived=true;msg.textContent='ARRIVED AT '+B.n;ui(['step','back'])}
}

// ---------- FIRST PERSON ----------
let yaw=0,pitch=0,pit=0,px=0,pz=0,fpT=0,drag=null,hold=0;const keys={};
const ROCKS=Array.from({length:80},()=>({x:Math.random()*120-60,z:Math.random()*120-60,s:.3+Math.random()*1.2}));
const DUST=Array.from({length:60},()=>[Math.random()*30,Math.random()*20,Math.random()*30]);
function cam(x,y,z){
  const cy=Math.cos(yaw),sy=Math.sin(yaw),cp=Math.cos(pit),sp=Math.sin(pit);
  const X=x*cy-z*sy;let Z=x*sy+z*cy;const Y=y*cp-Z*sp;Z=y*sp+Z*cp;
  return Z>.05?[W/2+X/Z*F,H/2-Y/Z*F,Z]:null;
}
function stepOut(){
  view='fp';fpT=performance.now();yaw=0;pitch=0;px=0;pz=0;msg.textContent='';stopAll();sf={};burst(3000,1.6,.25,'highpass');burst(120,.5,.6);
  ui(B.k==='rock'?['fwd','bwd','back']:['back']);
}
function ridge(col,amp,fr,off,yh){
  cx.fillStyle=col;cx.beginPath();cx.moveTo(0,H);
  for(let x=0;x<=W;x+=6){const az=yaw+Math.atan((x-W/2)/F);
    const h=(Math.sin(az*fr+off)*.5+Math.sin(az*fr*2.3+off*2)*.3+Math.sin(az*fr*5.1)*.12+.9)*amp;cx.lineTo(x,yh-h*F)}
  cx.lineTo(W,H);cx.fill();
}
function fp(now,dt){
  const v=B.v,ground=B.k==='rock';
  let mv=0;
  if(ground){
    mv=(keys.w||keys.arrowup||hold>0?1:0)-(keys.s||keys.arrowdown||hold<0?1:0);
    yaw+=((keys.d||keys.arrowright?1:0)-(keys.a||keys.arrowleft?1:0))*1.2*dt;
    px+=Math.sin(yaw)*mv*4*dt;pz+=Math.cos(yaw)*mv*4*dt;
  }
  pit=pitch+(mv?Math.sin(now/130)*.004:Math.sin(now/1500)*.004);
  const yh=H/2+F*Math.tan(pit);
  sndFp(now,mv,ground);
  // sky
  if(ground){const g=cx.createLinearGradient(0,0,0,Math.max(yh,1));g.addColorStop(0,v.sky[0]);g.addColorStop(1,v.sky[1]);cx.fillStyle=g}
  else cx.fillStyle='#02030a';
  cx.fillRect(0,0,W,H);
  if(!ground||v.stars)for(const s of SK){
    const p=cam(s.dx,s.dy,s.dz);if(!p||(ground&&p[1]>yh))continue;
    cx.globalAlpha=.4+.6*Math.abs(Math.sin(now/800+s.tw));cx.fillStyle='#fff';cx.fillRect(p[0],p[1],1.6,1.6);
  }
  cx.globalAlpha=1;
  if(ground){
    if(v.sun){
      const p=cam(Math.cos(.42)*Math.sin(.7),Math.sin(.42),Math.cos(.42)*Math.cos(.7));
      if(p){const r=F*v.sun,g=cx.createRadialGradient(p[0],p[1],0,p[0],p[1],r*6);
        g.addColorStop(0,'rgba(255,245,210,.9)');g.addColorStop(.2,'rgba(255,225,160,.35)');g.addColorStop(1,'rgba(255,225,160,0)');
        disc(p[0],p[1],r*6,g);disc(p[0],p[1],r,'#fffbe8')}
    }
    ridge(sh(v.ridge,.8),.06,2.1,1,yh);ridge(sh(v.ridge,.55),.035,3.3,4,yh);
    const g=cx.createLinearGradient(0,yh,0,H);g.addColorStop(0,sh(v.gnd,1.25));g.addColorStop(1,sh(v.gnd,.5));
    cx.fillStyle=g;cx.fillRect(0,Math.max(yh,0),W,H);
    const L=[];
    for(const r of ROCKS){
      const rx=(((r.x-px+60)%120)+120)%120-60,rz=(((r.z-pz+60)%120)+120)%120-60,p=cam(rx,-1.7,rz);
      if(p&&p[2]<70)L.push([p,r.s]);
    }
    L.sort((a,b)=>b[0][2]-a[0][2]);
    for(const q of L){const p=q[0],w=F*q[1]/p[2];
      cx.fillStyle=sh(v.gnd,.4);cx.beginPath();cx.ellipse(p[0],p[1]-w*.2,w,w*.55,0,0,7);cx.fill();
      cx.fillStyle=sh(v.gnd,.75);cx.beginPath();cx.ellipse(p[0]-w*.25,p[1]-w*.35,w*.5,w*.25,0,0,7);cx.fill()}
    const rp=cam(6-px,-1.7,16-pz);
    if(rp&&rp[2]>1.5)rocketDraw(rp[0],rp[1],F*9/rp[2],0,now);
  }else{
    const p=cam(Math.cos(-.08)*Math.sin(.45),Math.sin(-.08),Math.cos(-.08)*Math.cos(.45));
    if(p)drawBody(p[0],p[1],Math.min(F*v.rad,2500),B,now);
    const rp=cam(-10+Math.sin(now/4000)*1.5,2+Math.sin(now/3100),28);
    if(rp){cx.save();cx.translate(rp[0],rp[1]);cx.rotate(.5+Math.sin(now/3000)*.1);rocketDraw(0,0,F*9/rp[2],0,now);cx.restore()}
    cx.fillStyle='#fff';
    for(const d of DUST){
      const p=cam(((d[0]+now*.0008)%30)-15,d[1]-10,((d[2]+now*.0005)%30)-15+15);
      if(p&&p[2]<30){cx.globalAlpha=.6;cx.fillRect(p[0],p[1],Math.max(1,F*.015/p[2]),Math.max(1,F*.015/p[2]))}
    }
    cx.globalAlpha=1;
  }
  // visor
  const vg=cx.createRadialGradient(W/2,H/2,Math.min(W,H)*.35,W/2,H/2,Math.hypot(W,H)/2);
  vg.addColorStop(0,'rgba(0,0,0,0)');vg.addColorStop(1,'rgba(0,0,0,.78)');cx.fillStyle=vg;cx.fillRect(0,0,W,H);
  cx.strokeStyle='rgba(77,232,255,.3)';cx.lineWidth=3;cx.strokeRect(8,8,W-16,H-16);
  cx.fillStyle='rgba(255,255,255,.05)';cx.beginPath();cx.moveTo(0,0);cx.lineTo(W*.35,0);cx.lineTo(0,H*.4);cx.fill();
  const fa=1-clamp((now-fpT)/1800);
  if(fa>0){cx.fillStyle='rgba(0,0,0,'+fa+')';cx.fillRect(0,0,W,H);
    if(fa>.3){cx.fillStyle='#fff';cx.font='800 14px ui-monospace,monospace';cx.textAlign='center';cx.fillText('AIRLOCK OPENING…',W/2,H/2)}}
  const hd=Math.round(((yaw*180/Math.PI)%360+360)%360);
  shud.innerHTML='<h4>EVA · '+B.n+'</h4>'+B.hud.map(t=>'<div>'+t+'</div>').join('')+row('HEADING',hd+'°')+
    '<div><span>'+(ground?'Drag to look · W/S walk · A/D turn':'Floating: drag to look around')+'</span></div>';
}
cv.addEventListener('pointerdown',e=>{drag=[e.clientX,e.clientY];cv.setPointerCapture(e.pointerId)});
cv.addEventListener('pointermove',e=>{
  if(!drag||view!=='fp')return;
  yaw-=(e.clientX-drag[0])*.005;pitch=clamp(pitch+(e.clientY-drag[1])*.005,-1.2,1.2);drag=[e.clientX,e.clientY];
});
['pointerup','pointercancel'].forEach(t=>cv.addEventListener(t,()=>{drag=null}));
addEventListener('keydown',e=>{const k=e.key.length>1?e.key.toLowerCase():e.key.toLowerCase();keys[k]=1;if(view==='fp'&&k.startsWith('arrow'))e.preventDefault()});
addEventListener('keyup',e=>{delete keys[e.key.toLowerCase()]});
[['fwd',1],['bwd',-1]].forEach(a=>{
  const b=$(a[0]);b.addEventListener('pointerdown',()=>{hold=a[1]});
  ['pointerup','pointerleave','pointercancel'].forEach(t=>b.addEventListener(t,()=>{hold=0}));
});
if(START){const i=NAMES.indexOf(START);if(i>=0)go(i)}
</script></body></html>
"""


def build_explorer(accent, start=None, nonce=0):
    return (
        EXPLORER_HTML
        .replace("__ACCENT__", accent)
        .replace("__START__", json.dumps(start).replace("</", "<\\/"))
        .replace("__NONCE__", str(nonce))
    )


# ---------------- CUSTOM CSS ----------------

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {st.session_state.bg_color};
        background-image:
            radial-gradient(ellipse at 15% 0%, {st.session_state.accent_color}59, transparent 55%),
            radial-gradient(ellipse at 85% 8%, rgba(0, 255, 170, .16), transparent 50%);
        background-size: 160% 160%;
        animation: aurora 22s ease-in-out infinite alternate;
        isolation: isolate;
    }}
    .stApp::before, .stApp::after {{
        content: ""; position: fixed; top: 0; left: 0; width: 2px; height: 2px;
        z-index: -1; pointer-events: none; background: transparent;
    }}
    .stApp::before {{ box-shadow: {star_shadows(70, 1)}; animation: twinkle 3.4s ease-in-out infinite alternate; }}
    .stApp::after  {{ box-shadow: {star_shadows(50, 2)}; animation: twinkle 5.2s ease-in-out infinite alternate-reverse; }}
    @keyframes twinkle {{ from {{ opacity: .2; }} to {{ opacity: 1; }} }}
    @keyframes aurora {{ from {{ background-position: 0% 0%; }} to {{ background-position: 100% 60%; }} }}
    @media (prefers-reduced-motion: reduce) {{
        .stApp, .stApp::before, .stApp::after {{ animation: none; }}
    }}
    div.stDownloadButton > button {{
        background-color: {st.session_state.accent_color};
        color: white; border: none; border-radius: 8px;
    }}

    h1, h2, h3, p, label,
    [data-testid="stMarkdownContainer"] {{
        color: {st.session_state.text_color};
    }}

    div.stButton > button,
    div.stFormSubmitButton > button {{
        background-color: {st.session_state.accent_color};
        color: white;
        border: none;
        border-radius: 8px;
    }}

    div.stButton > button:hover,
    div.stFormSubmitButton > button:hover {{
        border: 1px solid white;
        color: white;
    }}
    </style>
    """,
    unsafe_allow_html=True
)


# ---------------- SIDEBAR NAVIGATION ----------------

# While a launch is playing, hide the sidebar so the scene feels full-page.
if st.session_state.launch_name:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"],
        [data-testid="stSidebarCollapsedControl"] { display: none; }
        iframe { border-radius: 16px; }
        </style>
        """,
        unsafe_allow_html=True
    )

with st.sidebar:
    st.title("⚙️ SETTINGS")

    page = st.radio(
        "Choose a dashboard view:",
        options=[
            "SIGN UP",
            "PLANET EXPLORER",
            "SPACE TRAVEL",
            "SPACE CRAFTS",
            "CUSTOMIZATION",
            "EXPERIMENTAL ETUDES",
            "ASTRONAUT SIMULATION",
            "ORBITAL FOUNDRY",
            "MINI FLIGHT SIMULATOR",
            "SPACE ENGINEERING AND FLIGHT",
            "RADIO CONTROL AND PLANNING",
            "INITIATE EXOPOLIS",
            "ACADEMY LITE"
        ],
        index=None
    )

# Leaving the sign-up page ends the launch scene.
if page != "SIGN UP":
    st.session_state.launch_name = None
if page != "SPACE TRAVEL":
    st.session_state.travel_to = None

if page and st.session_state.get("last_page") != page:
    st.session_state.last_page = page
    track(f"page:{page}", "page")

orion_widget()
render_planet_codex()

# ---------------- HOME / MAIN TITLE ----------------

if page is None:
    # Centered welcome text + a spacecraft crossing the background (bottom-left -> top-right)
    st.markdown(
        f"""
        <style>
        [data-testid="stMain"], section.main {{ position: relative; z-index: 0; }}
        .home {{ text-align: center; margin-top: 22vh; }}
        .home h1 {{ font-size: clamp(2rem, 6vw, 4rem); letter-spacing: .06em; }}
        .craft {{
            position: fixed; left: var(--x, 0); bottom: 0; z-index: -1; pointer-events: none;
            font-size: var(--s, 2.8rem); line-height: 1;
            animation: fly var(--d, 12s) linear var(--delay, 0s) infinite;
        }}
        .craft::before {{
            content: ""; position: absolute; right: 50%; top: 50%;
            width: calc(var(--s, 2.8rem) * 5); height: 4px; border-radius: 5px;
            transform-origin: right center; transform: rotate(-45deg);
            background: linear-gradient(to left, {st.session_state.accent_color}, transparent);
        }}
        @keyframes fly {{
            0%   {{ transform: translate(-15vmax, 15vmax); }}
            70%  {{ transform: translate(115vmax, -115vmax); }}
            100% {{ transform: translate(115vmax, -115vmax); }}
        }}
        .ufo, .sat {{ position: fixed; left: 0; z-index: -1; pointer-events: none; }}
        .ufo {{ top: 18vh; font-size: 2.2rem; animation: drift 26s linear infinite; }}
        .sat {{ top: 62vh; font-size: 1.6rem; animation: driftl 42s linear infinite; }}
        @keyframes drift {{
            0%   {{ transform: translate(-10vw, 0); }}
            25%  {{ transform: translate(25vw, -18px); }}
            50%  {{ transform: translate(55vw, 12px); }}
            75%  {{ transform: translate(85vw, -14px); }}
            100% {{ transform: translate(115vw, 0); }}
        }}
        @keyframes driftl {{
            from {{ transform: translateX(110vw) rotate(0deg); }}
            to   {{ transform: translateX(-15vw) rotate(360deg); }}
        }}
        .meteor {{
            position: fixed; top: var(--t); right: var(--r); width: 130px; height: 2px;
            z-index: -1; pointer-events: none; opacity: 0;
            background: linear-gradient(to right, #fff, transparent);
            animation: shoot var(--d) linear var(--delay) infinite;
        }}
        @keyframes shoot {{
            0%   {{ opacity: 0; transform: translate(0, 0) rotate(-30deg); }}
            2%   {{ opacity: 1; }}
            12%  {{ opacity: 0; transform: translate(-60vw, 35vh) rotate(-30deg); }}
            100% {{ opacity: 0; transform: translate(-60vw, 35vh) rotate(-30deg); }}
        }}
        @media (prefers-reduced-motion: reduce) {{ .craft, .ufo, .sat, .meteor {{ display: none; }} }}
        </style>
        <div class="craft">🚀</div>
        <div class="craft" style="--s:1.7rem;--d:17s;--delay:5s;--x:28vw">🚀</div>
        <div class="craft" style="--s:2.1rem;--d:21s;--delay:11s;--x:55vw">🚀</div>
        <div class="ufo">🛸</div><div class="sat">🛰️</div>
        <div class="meteor" style="--t:8vh;--r:10vw;--d:9s;--delay:2s"></div>
        <div class="meteor" style="--t:22vh;--r:30vw;--d:13s;--delay:6s"></div>
        <div class="meteor" style="--t:4vh;--r:50vw;--d:17s;--delay:10s"></div>
        <div class="home">
            <h1>{html.escape(st.session_state.dashboard_title)}</h1>
            <p>Explore the universe with NOVARIS</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.info("👈 Click the arrow at the top-left to open the sidebar and explore NOVARIS.", icon="🚀")
    if st.button("🎮 START NOVARIS GAME"):
        import subprocess, sys, socket, time
        if sys.platform != "win32":
            st.warning("The game runs only on the local PC version for now.")
        else:
            g = next((Path(__file__).parent / "game files").rglob("Game_NOVARIS.html")).parent
            if socket.socket().connect_ex(("127.0.0.1", 18767)):
                subprocess.Popen([sys.executable, "-m", "http.server", "18767", "--bind", "127.0.0.1", "--directory", str(g)], creationflags=0x08000000)
                time.sleep(1.5)
            components.html('<iframe src="http://127.0.0.1:18767/Game_NOVARIS.html" allow="fullscreen; pointer-lock; autoplay" style="width:100%;height:800px;border:0"></iframe>', height=800)
else:
    st.title(st.session_state.dashboard_title)
    st.caption("Explore the universe with NOVARIS")


# ---------------- SIGN UP ----------------

if page == "SIGN UP":
    st.header("SIGN UP")

    if st.session_state.launch_name:
        # ----- Launch scene replaces the form -----
        launch_name = st.session_state.launch_name

        components.html(
            build_launch_html(
                launch_name,
                st.session_state.accent_color,
                st.session_state.bg_color,
                st.session_state.launch_id
            ),
            height=640
        )

        st.success(
            f"Thank you, {launch_name}! "
            "Your data has been recorded."
        )

        col_a, col_dl, col_b = st.columns(3)
        with col_a:
            if st.button("↺ REPLAY LAUNCH", use_container_width=True):
                st.session_state.launch_id += 1
                st.rerun()
        with col_dl:
            rec = st.session_state.launch_user
            if rec:
                slug = re.sub(r"\W+", "_", rec["name"])
                st.download_button(
                    "⬇ DOWNLOAD MY FORM",
                    data=registration_text(rec),
                    file_name=f"novaris_registration_{slug}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
        with col_b:
            if st.button("NEW SIGN UP", use_container_width=True):
                st.session_state.launch_name = None
                st.rerun()

    else:
        st.subheader("Fill in the following form to proceed.")

        # ----- Register with Gmail -----
        g = google_account()
        if g:
            st.success(f"Signed in with Google as {g['email']}. Finish the form below.")
            if st.button("Use a different account"):
                st.logout()
        elif st.button("📧 Register with Gmail", use_container_width=True):
            if google_login_ready():
                st.login("google" if "google" in st.secrets["auth"] else None)
            else:
                st.info(
                    "UNDER DEVELOPMENT. PATH TO BE SPECIFIED YET"
                )
        st.caption("Or register with your email address:")

        # ----- Email form -----
        with st.form("NEW_USER_FORM", clear_on_submit=False):
            name = st.text_input(
                "ENTER YOUR NAME",
                value=g["name"][:14] if g else "",
                max_chars=14
            )
            email = st.text_input(
                "EMAIL ADDRESS",
                value=g["email"] if g else "",
                placeholder="you@example.com"
            )
            age = st.slider("SELECT AGE", 1, 100, 14)
            descp = st.text_area("YOUR DESCRIPTION")

            submit = st.form_submit_button("SUBMIT FORM")

        if submit:
            email_clean = email.strip().lower()
            if not name.strip():
                st.warning("Please enter your name.")
            elif not EMAIL_RE.match(email_clean):
                st.warning("Please enter a valid email address.")
            elif any(u.get("email", "").lower() == email_clean for u in load_users()):
                st.warning("This email is already registered.")
            else:
                via_google = bool(g) and g["email"].lower() == email_clean
                record = {
                    "name": name.strip(),
                    "email": email_clean,
                    "age": age,
                    "description": descp,
                    "method": "gmail" if via_google else "email",
                    "registered_at": datetime.now().isoformat(timespec="seconds")
                }
                save_user(record)
                st.session_state.launch_user = record
                track("SUBMIT FORM")
                save_prefs()
                st.session_state.launch_name = name.strip()
                st.session_state.launch_id += 1
                st.rerun()

    users = load_users()
    if users:
        with st.expander("VIEW REGISTERED USERS"):
            for i, user in enumerate(users, start=1):
                st.markdown(f"**User {i}: {user['name']}**")
                st.write(f"Email: {mask_email(user.get('email', ''))}")
                st.write(f"Age: {user['age']}")
                st.write(f"Description: {user['description']}")
                st.write(f"Registered via: {user.get('method', 'email')}")
                st.divider()


# ---------------- PLANET EXPLORER ----------------

elif page == "PLANET EXPLORER":
    st.header("🪐 PLANET EXPLORER")
    st.write(
        "Hover over a planet, star or black hole for its stats, then click it to "
        "fly there in the NOVARIS rocket and step out. On touch screens, tap once "
        "for stats and again to travel. Sizes and distances are not to scale."
    )
    components.html(build_explorer(st.session_state.accent_color), height=700)
    st.caption("Moon counts change as new moons are discovered. Figures are approximate.")


# ---------------- SPACE TRAVEL ----------------

elif page == "SPACE TRAVEL":
    st.header("🛰️ SPACE TRAVEL")
    dest = st.selectbox("Choose your destination", EXPLORER_NAMES)
    if st.button("🚀 TAKE ME THERE"):
        st.session_state.travel_to = dest
        st.session_state.travel_id += 1
        track(f"travel:{dest}")
    if st.session_state.travel_to:
        components.html(
            build_explorer(
                st.session_state.accent_color,
                st.session_state.travel_to,
                st.session_state.travel_id
            ),
            height=700
        )


# ---------------- SPACE CRAFTS ----------------

elif page == "SPACE CRAFTS":
    st.header("🚀 SPACE CRAFTS")
    st.write(
        "Discover the spacecraft and observatories "
        "that have expanded our understanding of space."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Voyager 1")
        st.image(
            "https://science.nasa.gov/wp-content/uploads/2023/09/"
            "voyager1.png",
            use_container_width=True
        )
        st.write(
            "Launched in 1977, Voyager 1 explored Jupiter "
            "and Saturn and later entered interstellar space."
        )
        st.link_button(
            "Explore Voyager 1",
            "https://science.nasa.gov/mission/voyager/voyager-1/",
            use_container_width=True
        )

    with col2:
        st.subheader("James Webb Space Telescope")
        st.image(
            "https://science.nasa.gov/wp-content/uploads/2023/06/"
            "webb-telescope.jpg",
            use_container_width=True
        )
        st.write(
            "This infrared space telescope studies distant "
            "galaxies, stars, and planetary systems."
        )
        st.link_button(
            "Explore JWST",
            "https://science.nasa.gov/mission/webb/",
            use_container_width=True
        )

    with col3:
        st.subheader("Chandrayaan-3")
        st.image(
            "https://www.isro.gov.in/media_isro/image/index/"
            "Chandrayaan3/Chandrayaan3_Lander.jpg",
            use_container_width=True
        )
        st.write(
            "India's lunar mission achieved a successful "
            "soft landing on the Moon on 23 August 2023."
        )
        st.link_button(
            "Explore Chandrayaan-3",
            "https://www.isro.gov.in/Chandrayaan3.html",
            use_container_width=True
        )

    st.divider()
    st.caption(
        "Images are loaded from external websites. "
        "An image may not appear if its URL changes or "
        "the hosting website blocks access."
    )


# ---------------- CUSTOMIZATION ----------------

elif page == "CUSTOMIZATION":
    st.header("🎨 CUSTOMIZATION")
    st.write("Personalize your ASTRA NOVA dashboard.")

    st.subheader("Appearance")

    bg_color = st.color_picker(
        "Choose Background Color",
        value=st.session_state.bg_color
    )

    text_color = st.color_picker(
        "Choose Text Color",
        value=st.session_state.text_color
    )

    accent_color = st.color_picker(
        "Choose Button Color",
        value=st.session_state.accent_color
    )

    st.session_state.bg_color = bg_color
    st.session_state.text_color = text_color
    st.session_state.accent_color = accent_color
    
    snapshot = {k: st.session_state[k] for k in PREF_KEYS}
    if st.session_state.get("prefs_snapshot") != snapshot:
        st.session_state.prefs_snapshot = snapshot
        save_prefs()

    st.divider()
    st.subheader("Dashboard Title")

    dashboard_title = st.text_input(
        "Enter a new title",
        value=st.session_state.dashboard_title
    )

    if st.button("APPLY TITLE"):
        track("APPLY TITLE")
        if dashboard_title.strip():
            st.session_state.dashboard_title = dashboard_title.strip()
            st.rerun()
        else:
            st.warning("The title cannot be empty.")

    st.divider()
    st.subheader("Preview")

    st.markdown(
        f"""
        <div style="
            background-color: {bg_color};
            color: {text_color};
            padding: 20px;
            border: 1px solid {accent_color};
            border-radius: 12px;
        ">
            <h3 style="color: {text_color};">
                {html.escape(dashboard_title)}
            </h3>
            <p style="color: {text_color};">
                Your personalized ASTRA NOVA dashboard.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button("RESET CUSTOMIZATION"):
        track("RESET CUSTOMIZATION")
        st.session_state.bg_color = defaults["bg_color"]
        st.session_state.text_color = defaults["text_color"]
        st.session_state.accent_color = defaults["accent_color"]
        st.session_state.dashboard_title = defaults["dashboard_title"]
        st.rerun()

    st.caption(
        "Customization settings remain available during "
        "the current Streamlit session."
    )
elif page == "EXPERIMENTAL ETUDES":
    if ETUDE_HTML.exists():
          html_code = ETUDE_HTML.read_text(encoding="utf-8")
          components.html(html_code, height=650, scrolling=True)
    else:
        st.error(f"Could not find `{ETUDE_HTML.name}` in your directory.")
elif page == "ASTRONAUT SIMULATION":
    if SIM_HTML.exists():
        code = SIM_HTML.read_text(encoding="utf-8")
        components.html(code, height=650, scrolling=True)
    else:
        st.error(f"Couldn't find {SIM_HTML.name}in directory")
elif page == "ORBITAL FOUNDRY":
    if ORBITAL_HTML.exists():
        code = ORBITAL_HTML.read_text(encoding="utf-8")
        components.html(code, height=650, scrolling=True)
    else:
        st.error(f"NOT FOUND{ORBITAL_HTML}")
elif page == "MINI FLIGHT SIMULATOR":
    if FLIGHT_HTML.exists():
            flight = FLIGHT_HTML.read_text(encoding="utf-8")
            components.html(flight, height=650, scrolling=True)
    else:
            st.error(f"NOT FOUND{FLIGHT_HTML}")
elif page == "SPACE ENGINEERING AND FLIGHT":
    if SPACE_HTML.exists():
        a = SPACE_HTML.read_text(encoding="utf-8")
        components.html(a, height=650, scrolling=True)            
    else:
        st.error("NOT FOUND {SPACE_HTML}")
elif page == "RADIO CONTROL AND PLANNING":
    if MISSION_HTML.exists():
        b = MISSION_HTML.read_text(encoding="utf-8")
        components.html(b, height=650, scrolling=False)
    else:
        st.error("NOT FOUND {MISSION_HTML}")
elif page == "INITIATE EXOPOLIS":
    if EXPOLIS_HTML.exists():
        c = EXPOLIS_HTML.read_text(encoding="utf-8")
        components.html(c, height=650, scrolling=True)            
    else:
        st.error("NOT FOUND {EXPOLIS_HTML}")
elif page == "ACADEMY LITE":
    if ACADEMY_HTML.exists():
        x = ACADEMY_HTML.read_text(encoding="utf-8")
        components.html(x, height=650, scrolling=True)
    else:
        st.error("NOT FOUND {ACADEMY.HTML}")