"""Blatt der Visier-Serie (VS01–VS09, claude-0.6) im Stil der XL-Konzeptblätter: 4800 × 4432 px wie die Waffenblätter.

Ein Modell je Visier (vsmodels.py): Isometrie mit Beschriftungen, Seite/Oben/Rück im gleichen Maßstab mit Visierlinie und Ankern,
Durchsicht im Spiel, vier Varianten, Fadenkreuz-Varianten (nur Bild), Bausteine (Glas-Tönungen, Rahmen, Tech-Module) und die
Kerndaten des Sight-Specs (export_sight.build, dieselben Zahlen wie VSnn.spec.json).
"""
from fontcss import FONT_CSS
import math,copy,html as _h,random
import eng,raster
from eng import tf,extent,model_origin
import vsmodels as V
import export_sight
from xl import panel,_callouts,ISO
from xlroles import VARIANTS as XV,_mix

W,H,PAD,G=4800,4432,80,32
INK='#E6ECF2';MUTE='#8FA0B3';LINE='#22314A';CYAN='#38D6F5'
DRAW_ALPHA=lambda a:min(0.62,0.20+a)       # Deckkraft der Zeichnung: im Spiel fast klar, auf dem Blatt muss das Glas lesbar sein

def split(S,tint=None):
    """undurchsichtige Teile / Glas (mit Zeichen-Deckkraft der Tönung)"""
    tid=tint or 'blue';o=eng.Model();g=eng.Model();a=DRAW_ALPHA(V.TINTS[tid][2])
    for P in S.m.parts:
        if P.get('glass'):Q=dict(P);Q['alpha']=a;Q['col']=V.TINTS[tid][1];g.parts.append(Q)
        else:o.parts.append(P)
    return o,g
def center_of(S):
    vs=[q for P in S.m.parts for f in P['F'] for q in f['v']]
    return [(min(q[i] for q in vs)+max(q[i] for q in vs))/2 for i in range(3)]
def view(S,tint,yaw,pitch,center,Wv,Hv,sc,origin=None,pad=0,ow=3.0,shadow=False):
    o,g=split(S,tint)
    img=raster.rasterview(o,yaw,pitch,center,Wv,Hv,sc,pad,ow,origin=origin,shadow=False,glass=g)
    if not shadow:return img
    # eigener flacher Schatten: der des Rasters wächst mit dem Maßstab (Waffenblätter 2–6, Visiere in mm bis 40)
    ew,eh=extent(S.m,yaw,pitch,center)
    return f'<ellipse cx="{Wv/2:.0f}" cy="{Hv/2+pad+eh*sc/2+12:.0f}" rx="{ew*sc*0.42:.0f}" ry="{min(34,max(10,Hv*0.025)):.0f}" fill="#000" opacity="0.3"/>'+img
def proj(p,yaw,pitch,center,origin,sc,Wv,Hv,pad=0):
    q=tf((p[0]-center[0],p[1]-center[1],p[2]-center[2]),math.radians(yaw),math.radians(pitch))
    return ((q[0]-origin[0])*sc+Wv/2,(q[1]-origin[1])*sc+Hv/2+pad)
def recolor(S,channels):
    """Kopie des Visiers mit anderen Kanalfarben (Varianten); Leuchtteile, Glas und Gummi bleiben"""
    S2=copy.deepcopy(S)
    for P in S2.m.parts:
        if not P.get('glass') and not P['emit'] and P.get('label')!='Augenmuschel' and P['channel'] in channels:P['col']=channels[P['channel']]
    return S2
def T(x,y,txt,size=19,col=INK,anchor='start',font='Chakra Petch',weight=400,ls=1.2):
    return f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="{anchor}" font-family="{font}, sans-serif" font-size="{size}" font-weight="{weight}" letter-spacing="{ls}" fill="{col}">{_h.escape(txt)}</text>'

# ---------------------------------------------------------------- Fadenkreuze (nur Bild)
def reticle_svg(rid,cx,cy,s,col,sw=None):
    """Fadenkreuz rid, Mitte (cx, cy), Größe s (halbe Breite). Linien in col; Cube Escape zeichnet es zur Laufzeit."""
    w=sw or max(2.0,s*0.06);o=f'stroke="{col}" stroke-width="{w:.1f}" fill="none" stroke-linecap="round"'
    def L(x0,y0,x1,y1):return f'<line x1="{cx+x0*s:.1f}" y1="{cy+y0*s:.1f}" x2="{cx+x1*s:.1f}" y2="{cy+y1*s:.1f}" {o}/>'
    def C(r,fill=False):return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r*s:.1f}" '+(f'fill="{col}"' if fill else o)+'/>'
    def corners(a,b):
        return ''.join(L(sx*a,sy*a,sx*a,sy*b)+L(sx*a,sy*a,sx*b,sy*a) for sx in (1,-1) for sy in (1,-1))
    if rid=='dot':return C(0.09,True)
    if rid=='circle':return C(0.55)+C(0.05,True)
    if rid=='cross':return L(-0.8,0,-0.15,0)+L(0.15,0,0.8,0)+L(0,-0.8,0,-0.15)+L(0,0.15,0,0.8)
    if rid=='t_dot':return L(-0.7,0,-0.18,0)+L(0.18,0,0.7,0)+L(0,0.18,0,0.8)+C(0.06,True)
    if rid=='circle_cross':return C(0.55)+L(-0.85,0,-0.3,0)+L(0.3,0,0.85,0)+L(0,-0.85,0,-0.3)+L(0,0.3,0,0.85)+C(0.05,True)
    if rid=='chevron':return f'<polyline points="{cx-0.45*s:.1f},{cy+0.3*s:.1f} {cx:.1f},{cy-0.2*s:.1f} {cx+0.45*s:.1f},{cy+0.3*s:.1f}" {o}/>'
    if rid=='target_field':return corners(0.6,0.3)+C(0.05,True)
    if rid=='fine':return L(-0.95,0,0.95,0)+L(0,-0.95,0,0.95)
    if rid=='mil_dot':return L(-0.95,0,0.95,0)+L(0,-0.95,0,0.95)+''.join(f'<circle cx="{cx+k*0.2*s:.1f}" cy="{cy:.1f}" r="{0.05*s:.1f}" fill="{col}"/><circle cx="{cx:.1f}" cy="{cy+k*0.2*s:.1f}" r="{0.05*s:.1f}" fill="{col}"/>' for k in (-4,-3,-2,-1,1,2,3,4))
    if rid=='ballistic':return L(-0.95,0,0.95,0)+L(0,-0.95,0,0.95)+''.join(L(-0.12*(4-k),0.18*k,0.12*(4-k),0.18*k) for k in (1,2,3))
    if rid=='digital':return L(-0.95,0,-0.25,0)+L(0.25,0,0.95,0)+L(0,-0.6,0,-0.25)+L(0,0.25,0,0.6)+f'<rect x="{cx-0.12*s:.1f}" y="{cy-0.12*s:.1f}" width="{0.24*s:.1f}" height="{0.24*s:.1f}" {o}/>'+T(cx+0.35*s,cy-0.3*s,'128',max(10,int(0.22*s)),col,font='JetBrains Mono')
    if rid=='dynamic':return ''.join(L(sx*0.25,sy*0.25,sx*0.6,sy*0.6) for sx in (1,-1) for sy in (1,-1))+C(0.06,True)
    if rid=='energy':return L(-0.95,0,-0.35,0)+L(0.35,0,0.95,0)+L(0,-0.95,0,-0.35)+L(0,0.35,0,0.95)+C(0.3)+''.join(L(k*0.1,-0.06,k*0.1,0.06) for k in (-8,-7,-6,6,7,8))
    if rid=='focus':return C(0.45)+C(0.18)+C(0.04,True)+L(-0.7,0,-0.5,0)+L(0.5,0,0.7,0)
    if rid=='tracking':return corners(0.55,0.32)+C(0.18)+L(-0.08,0,0.08,0)+L(0,-0.08,0,0.08)
    if rid=='quad':return ''.join(f'<polyline points="{cx+sx*0.6*s:.1f},{cy+sy*0.25*s:.1f} {cx+sx*0.35*s:.1f},{cy+sy*0.35*s:.1f} {cx+sx*0.25*s:.1f},{cy+sy*0.6*s:.1f}" {o}/>' for sx in (1,-1) for sy in (1,-1))
    if rid=='box':return f'<rect x="{cx-0.42*s:.1f}" y="{cy-0.42*s:.1f}" width="{0.84*s:.1f}" height="{0.84*s:.1f}" {o}/>'+L(-0.2,-0.2,0.2,0.2)+L(-0.2,0.2,0.2,-0.2)
    if rid=='lock_on':return corners(0.6,0.38)+L(-0.25,-0.25,0.25,0.25)+L(-0.25,0.25,0.25,-0.25)+C(0.12)
    if rid=='grid':return ''.join(L(k*0.25,-0.75,k*0.25,0.75)+L(-0.75,k*0.25,0.75,k*0.25) for k in (-3,-2,-1,0,1,2,3)).replace(f'stroke-width="{w:.1f}"',f'stroke-width="{w*0.5:.1f}"')+L(-0.95,0,0.95,0)+L(0,-0.95,0,0.95)
    raise KeyError(rid)

# ---------------------------------------------------------------- Szene hinter dem Glas (Durchsicht im Spiel)
def scene_svg(w,h,seed):
    r=random.Random(seed);hz=h*0.58
    s=(f'<defs><linearGradient id="sky{seed}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2E5C8F"/><stop offset="0.7" stop-color="#8DB8DC"/>'
       f'<stop offset="1" stop-color="#C9DCEB"/></linearGradient><linearGradient id="fl{seed}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#6A5A44"/>'
       f'<stop offset="1" stop-color="#2A241D"/></linearGradient></defs><rect width="{w}" height="{h}" fill="url(#sky{seed})"/>')
    for layer,(tone,top,cnt) in enumerate((('#5D7896',0.18,14),('#3E5470',0.30,10),('#283648',0.42,7))):
        x=-r.uniform(0,w*0.1)
        while x<w:
            bw=r.uniform(0.05,0.12)*w*(1+layer*0.3);bh=r.uniform(top,top+0.25)*h
            for k in range(int(bh//(bw*0.5))+1):
                y=hz-bh+k*bw*0.5
                s+=f'<rect x="{x:.0f}" y="{y:.0f}" width="{bw-2:.0f}" height="{min(bw*0.5,hz-y)-2:.0f}" fill="{tone}" stroke="{_mix(tone,"#000000",0.25)}" stroke-width="2"/>'
            if r.random()<0.25:
                dx=x+bw*0.3;s+=f'<rect x="{dx:.0f}" y="{hz-bh*0.45:.0f}" width="{bw*0.35:.0f}" height="{bh*0.45:.0f}" fill="#FF9A3C" opacity="0.85"/>'
            x+=bw+r.uniform(4,30)
    s+=f'<rect x="0" y="{hz:.0f}" width="{w}" height="{h-hz:.0f}" fill="url(#fl{seed})"/>'
    for k in range(-12,13):s+=f'<line x1="{w/2:.0f}" y1="{hz:.0f}" x2="{w/2+k*w*0.12:.0f}" y2="{h}" stroke="#F2A33A" stroke-opacity="0.25" stroke-width="2"/>'
    for k in range(1,8):yy=hz+(h-hz)*(k/8)**1.8;s+=f'<line x1="0" y1="{yy:.0f}" x2="{w}" y2="{yy:.0f}" stroke="#F2A33A" stroke-opacity="0.2" stroke-width="2"/>'
    return s

# ---------------------------------------------------------------- Blatt
def sheet(vid):
    """Blatt der Visier-Serie; die Bilder kodiert raster.deferred parallel (claude-0.19)."""
    with raster.deferred() as resolve:return resolve(_sheet(vid))
def _sheet(vid):
    d=V.load(vid);S=d['S'];info=d['info'];geo=d['geo'];ly=geo['line_y'];win=geo['window']
    spec=export_sight.build(vid)
    tint=info['tint'];hud=info['hud'];acc=V.ORANGE;fid='v'+vid.lower()
    c=center_of(S)
    # ---------- Isometrie mit Beschriftungen
    MW,MH=2600,1700
    ew,eh=extent(S.m,ISO[1],ISO[2],c);sm=min((MW-420)/ew,(MH-430)/eh)
    iv=view(S,tint,ISO[1],ISO[2],c,MW,MH,sm,ow=4.6,shadow=True)
    an={k:v for k,v in raster.LAST['anchors'].items() if '·' not in k}
    PRIO=['Glas','Rahmen','Leuchtrahmen','Markierungsrahmen','Gehäuse','Halterung','Emitter','Abdeckung','Montageringe','Augenmuschel',
          'Verstellturm','Entfernungsanzeige','Windkompensation','Zielmarkierung','Energiezelle','Rückring','Stütze','Schrauben']
    keys=sorted(an,key=lambda k:(PRIO.index(k) if k in PRIO else 60,k))[:9]
    call=_callouts({k:an[k] for k in keys},MW,MH,acc,MH/2,k=1.35)
    iso=panel(iv+call,MW,MH,'ISOMETRISCHE ANSICHT · MODULARES ANBAUTEIL · '+V.FRAMES[info['frame']].upper()+'-RAHMEN',fid,f"{vid} Visier isometrisch mit Bauteilbeschriftungen")
    # ---------- Seite / Oben / Rück: gleicher Maßstab, Visierlinie und Anker
    RW=W-2*PAD-MW-G
    OV=[('SEITE',0,0),('OBEN',0,90),('RÜCK',90,0)]
    geo_={lb:model_origin(S.m,y,p,c) for lb,y,p in OV}
    long_=geo_['SEITE'][1]>1.6*geo_['SEITE'][2]
    if long_:
        g=G;hS=int((MH-2*g)*0.3);hT=hS;hR=MH-hS-hT-2*g;rw=(RW-g)//2
        boxes={'SEITE':(RW,hS),'OBEN':(RW,hT),'RÜCK':(rw,hR)};dataw,datah=RW-rw-g,hR
    else:
        g=G;bw=(RW-g)//2;bh=(MH-g)//2
        boxes={'SEITE':(bw,bh),'RÜCK':(bw,bh),'OBEN':(bw,bh)};dataw,datah=bw,bh
    ss=min(min((boxes[lb][0]-150)/(2*geo_[lb][1]),(boxes[lb][1]-170)/(2*geo_[lb][2])) for lb,_,_ in OV)
    def obox(lb,yw,pt):
        bw_,bh_=boxes[lb];o,hw,hh=geo_[lb];pad=14
        vv=view(S,tint,yw,pt,c,bw_,bh_,ss,origin=o,pad=pad,ow=3.0)
        cx,cy=bw_/2,bh_/2+pad;ref=''
        for xx in (cx-hw*ss,cx+hw*ss):ref+=f'<line x1="{xx:.1f}" y1="40" x2="{xx:.1f}" y2="{bh_-10}" stroke="#4A6080" stroke-width="1.4" stroke-dasharray="8 8"/>'
        for yy in (cy-hh*ss,cy+hh*ss):ref+=f'<line x1="10" y1="{yy:.1f}" x2="{bw_-10}" y2="{yy:.1f}" stroke="#4A6080" stroke-width="1.4" stroke-dasharray="8 8"/>'
        P_=lambda p:proj(p,yw,pt,c,o,ss,bw_,bh_,pad)
        ov=''
        x0m,x1m=min(q[0] for P in S.m.parts for f in P['F'] for q in f['v']),max(q[0] for P in S.m.parts for f in P['F'] for q in f['v'])
        if lb!='RÜCK':
            a,b=P_((x0m-14,ly,0)),P_((x1m+14,ly,0))
            ov+=f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="{CYAN}" stroke-width="3" stroke-dasharray="14 9"/>'
            ov+=T(max(a[0],0)+16,a[1]-12,'VISIERLINIE −Y',16,CYAN,'start',ls=2)
        marks=[('Socket_Mount',(0,0,0)),('Socket_Sight',(win['x0'],ly,0)),('Socket_Reticle',(win['glass_x'],ly,0))]
        if geo.get('tube'):marks.append(('Socket_Eye',(geo['tube']['eye_x'],ly,0)))
        if lb=='SEITE':
            for k,(nm,p) in enumerate(marks):
                q=P_(p);dy=(-34-26*(k%2)) if nm!='Socket_Mount' else 8
                ov+=f'<circle cx="{q[0]:.1f}" cy="{q[1]:.1f}" r="8" fill="{acc if nm!="Socket_Mount" else INK}" stroke="#0A0A0D" stroke-width="2.5"/>'
                lb_=nm.replace('Socket_','').upper();tw_=len(lb_)*11+22
                if nm=='Socket_Mount':q=(q[0]-tw_/2-26,q[1])
                ov+=(f'<line x1="{q[0]:.1f}" y1="{q[1]:.1f}" x2="{q[0]:.1f}" y2="{q[1]+dy+(8 if dy<0 else -14):.1f}" stroke="{INK}" stroke-width="1.4"/>'
                     f'<rect x="{q[0]-tw_/2:.1f}" y="{q[1]+dy-19:.1f}" width="{tw_}" height="26" rx="13" fill="#0E1622" stroke="{acc}" stroke-width="1.2"/>'+T(q[0],q[1]+dy,lb_,15,INK,'middle',ls=1.5))
            # Maße
            bb=spec['dimensions_m'];y_=bh_-24
            a,b=P_((x0m,0,0)),P_((x1m,0,0))
            ov+=f'<line x1="{a[0]:.1f}" y1="{y_}" x2="{b[0]:.1f}" y2="{y_}" stroke="{MUTE}" stroke-width="1.6"/>'+T((a[0]+b[0])/2,y_-8,f'{bb["length"]*1000:.0f} mm',16,MUTE,'middle')
        if lb=='RÜCK':
            q=P_((win['glass_x'],ly,0));ov+=reticle_svg(info['reticles'][0],q[0],q[1],min(win['w'],win['h'])*ss*0.22,hud)
            ov+=T(q[0],q[1]+win['h']*ss*0.5+30 if not geo.get('tube') else bh_-20,f'Fenster {win["w"]:.0f} × {win["h"]:.0f} mm',16,CYAN,'middle')
        return panel(ref+vv+ov,bw_,bh_,{'SEITE':'SEITE (LINKS) · VISIERLINIE UND ANKER','OBEN':'OBEN','RÜCK':'RÜCK · DURCHSICHT −Y'}[lb],fid,f'{vid} {lb.lower()}')
    # ---------- Daten (aus dem Spec)
    def kv(rows,w_,h_):
        y=74;out=''
        for k,v in rows:
            if k=='':y+=14;continue
            out+=T(26,y,k,17,MUTE,font='Chakra Petch',ls=1.4)+f'<text x="{int(w_*0.33)}" y="{y}" font-family="JetBrains Mono, monospace" font-size="18" fill="{INK}">{_h.escape(v)}</text>';y+=30
        return out
    an_=spec['anchors'];tb=spec['tube']
    rows=[('TYP',f"{spec['sight']['type']} · {spec['sight']['type_de']}"),('KIND (TOOLGEN)',f"{spec['sight']['kind']} · Fenster {spec['sight']['window_kind']}"),
          ('RAHMEN',f"{spec['frame']['type']} · {spec['frame']['name_de']}"),
          ('FENSTER',f"{spec['window']['shape']} · {spec['window']['width_m']*1000:.1f} × {spec['window']['height_m']*1000:.1f} mm"),
          ('GLAS',f"{spec['glass']['name_de']} · RGBA lin {', '.join(f'{v:.3f}' for v in spec['glass_tint'])}"),
          ('RÖHRE',f"{tb['length_m']*1000:.0f} mm · Linse r {tb['lens_radius_m']*1000:.1f} · Auge r {tb['eye_radius_m']*1000:.1f}" if tb else 'keine'),
          ('MODUL',f"{spec['module']['name_de']} ({spec['module']['side']})" if spec['module'] else 'keins'),
          ('VISIERLINIE',f"{spec['dimensions_m']['line_height_m']*1000:.0f} mm über Halterung · frei: {'ja' if spec['sight_line']['clear'] else 'NEIN'}"),('',''),
          ('SOCKET_SIGHT',' '.join(f'{v:+.4f}' for v in an_['Socket_Sight']['position_m'])+' m'),
          ('SOCKET_RETICLE',' '.join(f'{v:+.4f}' for v in an_['Socket_Reticle']['position_m'])+' m'),
          ('SOCKET_EYE',(' '.join(f'{v:+.4f}' for v in an_['Socket_Eye']['position_m'])+' m') if an_['Socket_Eye'] else '–'),
          ('SOCKET_MOUNT','0 0 0 (Ursprung, auf Visierschiene)'),('',''),
          ('RAHMEN · ACHSEN','Blender, vorn −Y, oben +Z, m; Blick lokal +Z'),
          ('WAFFEN-SPEC',f"{spec['weapon']['toolgen_id']} · {', '.join(spec['weapon']['weapon_spec']['sheets'][:6])}")]
    data=panel(kv(rows,dataw,datah)+T(26,datah-24,f'{vid}.spec.json · {spec["format"]} v{spec["format_version"]}',15,MUTE,font='JetBrains Mono',ls=0.5),
               dataw,datah,'DATEN · SIGHT-SPEC',fid,f'{vid} Kerndaten des Sight-Specs')
    if long_:
        ortho=(f'<div style="display:flex;flex-direction:column;gap:{G}px;width:{RW}px">'+obox('SEITE',0,0)+obox('OBEN',0,90)+
               f'<div style="display:flex;gap:{G}px">'+obox('RÜCK',90,0)+data+'</div></div>')
    else:
        ortho=(f'<div style="display:grid;grid-template-columns:repeat(2,{boxes["SEITE"][0]}px);grid-auto-rows:{boxes["SEITE"][1]}px;gap:{G}px">'+
               obox('SEITE',0,0)+obox('RÜCK',90,0)+obox('OBEN',0,90)+data+'</div>')
    # ---------- Reihe B: Durchsicht, Fadenkreuze, Varianten
    BH=1250
    DW=1560
    o,g_=split(S,tint)
    if geo.get('tube'):
        R_=geo['tube']['lens_r']+4;sc=(BH*0.84)/(2*R_);pad=-40
    else:
        sc=min(DW*0.48/win['w'],BH*0.44/win['h']);pad=-BH*0.08
    rp=(win['glass_x'],ly,0);q=tf((rp[0]-c[0],rp[1]-c[1],rp[2]-c[2]),math.radians(90),0)
    dv=raster.rasterview(o,90,0,c,DW,BH,sc,pad,4.0,origin=(q[0],q[1]),shadow=False,glass=g_)
    rc=(DW/2,BH/2+pad);rs=min(win['w'],win['h'])*sc*0.32
    durch=(scene_svg(DW,BH,int(info['num']))+dv+reticle_svg(info['reticles'][0],rc[0],rc[1],rs,hud,sw=max(3.0,rs*0.05))+
           f'<rect x="0" y="{BH-64}" width="{DW}" height="64" fill="#0E1622" opacity="0.82"/>'+
           T(24,BH-24,f"Blick entlang −Y durch {'die Röhre' if geo.get('tube') else 'das freie Fenster'} · Glas {V.TINTS[tint][0]} · Fadenkreuz {V.RETICLES[info['reticles'][0]]} (Cube Escape zeichnet es)",19,INK))
    dur=panel(durch,DW,BH,'DURCHSICHT IM SPIEL',fid,f'{vid} Durchsicht im Spiel')
    FW=1000
    tiles='';tw,th=(FW-3*24)//2,(BH-110-24)//2
    for k,rid in enumerate(info['reticles']):
        x=24+(k%2)*(tw+24);y=70+(k//2)*(th+24)
        tiles+=(f'<g transform="translate({x},{y})"><rect width="{tw}" height="{th}" rx="16" fill="#0B121C" stroke="{hud if k==0 else LINE}" stroke-width="{2.5 if k==0 else 1.5}"/>'
                +reticle_svg(rid,tw/2,th/2-24,min(tw,th)*0.3,hud)+T(tw/2,th-30,V.RETICLES[rid].upper()+(' · STANDARD' if k==0 else ''),20,INK,'middle',weight=600,ls=2)+'</g>')
    tiles+=T(24,BH-22,'Nur Bild – das Fadenkreuz zeichnet Cube Escape zur Laufzeit an Socket_Reticle',17,MUTE,font='Barlow')
    ret=panel(tiles,FW,BH,'FADENKREUZ-VARIANTEN',fid,f'{vid} Fadenkreuz-Varianten')
    VW=W-2*PAD-DW-FW-2*G;vw=(VW-G)//2;vh=(BH-G)//2
    vs=''
    for k,va in enumerate(spec['variants']):
        S2=recolor(S,va['channels']) if k else S
        e1,e2=extent(S2.m,ISO[1],ISO[2],c);sv=min((vw-80)/e1,(vh-150)/e2)
        vv=view(S2,va['glass_tint'],ISO[1],ISO[2],c,vw,vh,sv,ow=2.6,shadow=True)
        dots=''.join(f'<rect x="{24+i*36}" y="{vh-46}" width="28" height="28" rx="7" fill="{col}" stroke="#0A0A0D" stroke-width="1"/>' for i,col in enumerate(va['channels'].values()))
        dots+=T(24+len(va['channels'])*36+14,vh-25,'Glas '+V.TINTS[va['glass_tint']][0],17,MUTE,font='Barlow')
        vs+=panel(vv+dots,vw,vh,f"VARIANTE {k+1}/4 · {va['name_de'].upper()}",fid,f"{vid} Variante {va['name_de']}")
    varp=f'<div style="display:grid;grid-template-columns:repeat(2,{vw}px);grid-auto-rows:{vh}px;gap:{G}px;width:{VW}px">{vs}</div>'
    # ---------- Reihe C: Bausteine
    CH=H-2*PAD-180-MH-BH-3*G
    GW,FRW=1300,1950;MDW=W-2*PAD-GW-FRW-2*G
    gt='';sw_=(GW-5*24)//4;sh_=(CH-110-24)//2
    for k,(tid,(nm,hx,a)) in enumerate(V.TINTS.items()):
        x=24+(k%4)*(sw_+24);y=66+(k//4)*(sh_+24);act=tid==tint
        chk=''.join(f'<rect x="{12+i*22}" y="{12+j*22}" width="22" height="22" fill="{"#C9D3DD" if (i+j)%2 else "#56606C"}"/>' for i in range((sw_-24)//22) for j in range((sh_-90)//22))
        gt+=(f'<g transform="translate({x},{y})"><rect width="{sw_}" height="{sh_}" rx="14" fill="#0B121C" stroke="{acc if act else LINE}" stroke-width="{3 if act else 1.5}"/>{chk}'
             f'<rect x="12" y="12" width="{sw_-24}" height="{sh_-90}" rx="10" fill="{hx}" fill-opacity="{DRAW_ALPHA(a):.2f}" stroke="{_mix(hx,"#FFFFFF",0.5)}" stroke-width="2"/>'
             +T(sw_/2,sh_-46,nm.upper(),18,INK,'middle',weight=600,ls=1.6)+T(sw_/2,sh_-20,f'{hx} · α {a:.2f}'+(' · AKTIV' if act else ''),14,acc if act else MUTE,'middle',font='JetBrains Mono',ls=0.3)+'</g>')
    glp=panel(gt,GW,CH,'BAUSTEINE · GLAS-TÖNUNGEN (RGBA IM SPEC LINEAR)',fid,f'{vid} Glas-Tönungen')
    ft='';fw_=(FRW-4*24)//3;fh_=(CH-90-24)//2
    for k,st in enumerate(V.FRAMES):
        Sf=V.frame_variant(st,win['shape']);cf=center_of(Sf);act=st==info['frame']
        e1,e2=extent(Sf.m,ISO[1],ISO[2],cf);sv=min((fw_-60)/e1,(fh_-110)/e2)
        x=24+(k%3)*(fw_+24);y=62+(k//3)*(fh_+24)
        ft+=(f'<g transform="translate({x},{y})"><rect width="{fw_}" height="{fh_}" rx="14" fill="#0B121C" stroke="{acc if act else LINE}" stroke-width="{3 if act else 1.5}"/>'
             +view(Sf,tint,ISO[1],ISO[2],cf,fw_,fh_-40,sv,ow=2.2)+T(fw_/2,fh_-22,V.FRAMES[st].upper()+(' · DIESES VISIER' if act else ''),18,acc if act else INK,'middle',weight=600,ls=1.8)+'</g>')
    frp=panel(ft,FRW,CH,'BAUSTEINE · RAHMEN-VARIANTEN',fid,f'{vid} Rahmen-Varianten')
    mt='';mw_=(MDW-3*24)//2;mh_=(CH-90-24)//2
    for k,mid in enumerate(V.MODULES):
        Sm=V.module_model(mid);cm=center_of(Sm);act=mid==S.module
        e1,e2=extent(Sm.m,ISO[1],ISO[2],cm);sv=min((mw_-60)/e1,(mh_-110)/e2)
        x=24+(k%2)*(mw_+24);y=62+(k//2)*(mh_+24)
        mt+=(f'<g transform="translate({x},{y})"><rect width="{mw_}" height="{mh_}" rx="14" fill="#0B121C" stroke="{acc if act else LINE}" stroke-width="{3 if act else 1.5}"/>'
             +view(Sm,tint,ISO[1],ISO[2],cm,mw_,mh_-40,sv,ow=2.2)+T(mw_/2,mh_-22,V.MODULES[mid].upper()+(' · VERBAUT' if act else ''),17,acc if act else INK,'middle',weight=600,ls=1.4)+'</g>')
    mdp=panel(mt,MDW,CH,'BAUSTEINE · TECH-MODULE (OPTIONAL)'+('' if S.module else ' · HIER KEINS'),fid,f'{vid} Tech-Module')
    # ---------- Kopf
    pal=''.join(f'<div style="display:flex;align-items:center;gap:10px"><div style="width:50px;height:50px;border-radius:12px;background:{col}"></div><span style="font-size:19px;color:{MUTE}">{col}</span></div>'
                for col in (V.WHITE,V.DARK,V.ORANGE,V.TINTS[tint][1]))
    sub=(f"VISIER-SERIE · ZIELBILD FÜR WAFFE {int(info['num'])} · {info['title'].upper()} · MODULARES ANBAUTEIL · FENSTER FREI DURCHSICHTIG · "
         f"EIN MODELL FÜR ANSICHTEN UND {vid}.SPEC.JSON")
    page=f'''<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>{vid} Visier {_h.escape(info['weapon'])} – {_h.escape(info['title'])}</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
{FONT_CSS}
<style>body{{margin:0}}</style>
</helmet>
<div style="width:{W}px;height:{H}px;box-sizing:border-box;padding:{PAD}px;background:#0E1622;color:{INK};font-family:Barlow,sans-serif;display:flex;flex-direction:column;gap:{G}px">
<div style="height:180px;display:flex;justify-content:space-between;align-items:center;gap:40px">
<div style="display:flex;align-items:center;gap:30px;min-width:0">
<span style="font-family:'Chakra Petch',sans-serif;font-size:140px;font-weight:700;line-height:1;color:{acc}">{vid}</span>
<div style="display:flex;flex-direction:column;gap:8px;min-width:0">
<span style="font-family:'Chakra Petch',sans-serif;font-size:74px;font-weight:700;letter-spacing:6px;line-height:1.05">{_h.escape(info['weapon'].upper())} · {_h.escape(V.TYPES_DE[info['type']].upper())}</span>
<span style="font-size:25px;letter-spacing:4px;color:{MUTE}">{_h.escape(sub)}</span>
</div>
</div>
<div style="display:flex;align-items:center;gap:30px;flex-shrink:0">
<div style="display:flex;gap:20px">{pal}</div>
<span style="padding:16px 32px;border:1.5px solid {acc};border-radius:999px;color:{acc};font-family:'Chakra Petch',sans-serif;font-size:24px;font-weight:600;letter-spacing:3px;white-space:nowrap">{_h.escape(info['type'].upper()+' · '+info['frame'].upper())}</span>
</div>
</div>
<div style="display:flex;gap:{G}px;height:{MH}px">{iso}{ortho}</div>
<div style="display:flex;gap:{G}px;height:{BH}px">{dur}{ret}{varp}</div>
<div style="display:flex;gap:{G}px;height:{CH}px">{glp}{frp}{mdp}</div>
</div>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{"$preview":{{"width":{W},"height":{H}}}}}'>
class Component extends DCLogic {{
renderVals() {{
return {{}};
}}
}}
</script>
</body>
</html>
'''
    return page
