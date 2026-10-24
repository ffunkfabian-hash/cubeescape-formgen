from fontcss import FONT_CSS
from cepaths import E3D,OUT
# Große Konzeptblätter (Seite „Konzeptblätter“): Isometrie + 6 Ortho + Detail Abzug + Material/Texturen + Farbvarianten + Prompt
import math,copy,colorsys,pickle,sys,zlib,html as _h
import numpy as np
from scipy import ndimage
sys.path.insert(0,E3D+'')
from eng import *
import raster
from xlroles import *
from xlroles import _rgb,_hex,_lum,_sat,_mix
import skins,variants,texcat,texprofile,wtypes
from skinraster import skin_texture

ISO=('ISOMETRISCHE ANSICHT',-45,35.264)
ORTHO=[('SEITENANSICHT LINKS',0,0),('SEITENANSICHT RECHTS',180,0),('VORDERANSICHT',-90,0),('RÜCKANSICHT',90,0),('DRAUFSICHT',0,90),('UNTERANSICHT',0,-90)]
DETAIL_LABELS=['Abzug','Abzugbügel','Bügel','Griff','Pistolengriff','Griffstück','Magazin','Energiemagazin']
DETAIL_FRAME_EXTRA=['Pfeilauflage']  # Bogen: Pfeilauflage am Griff gehört mit in den Rahmen des Detailfelds

def make_texture(seed=3,unit_m=None):
    """Texturen im Objektraum: Muster hängen an Bauteil-Koordinaten (nicht an der Bildrichtung). Seit claude-0.8 stehen Muster und
    Maße im Texturkatalog (docs/textures/catalog.json, mm am Objekt); unit_m = Modelleinheit des Blatts (Spec units.model_unit_m,
    Meter je Modelleinheit) rechnet sie in Modelleinheiten um, ohne Angabe gilt der Startwert des Katalogs."""
    P=texcat.sheet_patterns(unit_m)
    AX={'length':0,'height':1,'width':2}
    def tex(col,pb,idb,decm,parts,SS,world=None,nrm=None):
        h,w=pb.shape
        keys=['lack','brushed','rubber','plastic','light']
        lut=np.array([keys.index(material_of(P_)) for P_ in parts]+[-1],np.int16)
        mat=np.where(pb>=0,lut[np.clip(pb,0,len(parts))],-1);mat[decm]=-1
        out=col.copy()
        WX,WY,WZ=world;NX,NY,NZ=np.abs(nrm[0]),np.abs(nrm[1]),np.abs(nrm[2])
        C=(WX,WY,WZ)
        # Längsachse je Teil
        ax=np.zeros(len(parts)+1,np.int8)
        for i,P_ in enumerate(parts):
            vs=[q for f in P_['F'] for q in f['v']]
            ext=[max(q[k] for q in vs)-min(q[k] for q in vs) for k in range(3)]
            ax[i]=int(np.argmax(ext))
        A=ax[np.clip(pb,0,len(parts))]
        def hsh(t):return np.sin(t*12.9898)*43758.5453%1.0
        # gebürstet: Schleifspuren entlang der Längsachse -> Muster hängt nur von den beiden Querachsen ab (Summe der Querachsen)
        q1=np.where(A==0,WY,np.where(A==1,WX,WX));q2=np.where(A==0,WZ,np.where(A==1,WZ,WY))
        qq=q1+q2
        br=1+P['brushed']['amp']*sum(wt*np.sin(k*qq+ph) for k,ph,wt in P['brushed']['waves'])
        # gummiert: Rautenrändel in der Flächenebene
        domx=NX>=np.maximum(NY,NZ);domy=(NY>=np.maximum(NX,NZ))&~domx
        u=np.where(domx,WY,WX);v=np.where(domx,WZ,np.where(domy,WZ,WY))
        p=P['knurl']['cell']
        rb=1-P['knurl']['dark']*((np.floor((u+v)/p)%2==0)&(np.floor((u-v)/p)%2==0))
        # lackiert: weicher Glanzverlauf über die Höhe des Bauteils
        g=1+sum(wv['amp']*np.cos(wv['k']*sum(C[AX[a]] for a in wv['axes'])) for wv in P['gloss'])
        # matt: feines Korn, fest am Objekt
        gc=P['grain']['cell'];h0,h1,h2=P['grain']['hash']
        pl=1+P['grain']['amp']*(hsh(np.floor(WX/gc)*h0+np.floor(WY/gc)*h1+np.floor(WZ/gc)*h2)-0.5)
        for k,f in ((0,g),(1,br),(2,rb),(3,pl)):
            mk=mat==k
            out[mk]=np.clip(out[mk]*f[mk][:,None],0,255)
        return out
    return tex

def swatch_svg(kind,w,h,col):
    """kleines Musterfeld je Material (Vektor)"""
    cid=f'sw{kind}{zlib.crc32(col.encode())%9999}'   # reproduzierbar (hash() ist je Prozess zufällig)
    if kind=='lack':return f'<defs><linearGradient id="{cid}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{_mix(col,"#FFFFFF",0.25)}"/><stop offset="0.55" stop-color="{col}"/><stop offset="1" stop-color="{_mix(col,"#000000",0.2)}"/></linearGradient></defs><rect width="{w}" height="{h}" rx="10" fill="url(#{cid})"/>'
    if kind=='brushed':
        lines=''.join(f'<line x1="0" y1="{y}" x2="{w}" y2="{y}" stroke="{_mix(col,"#FFFFFF" if (y*7)%3 else "#000000",0.18)}" stroke-width="1"/>' for y in range(2,h,3))
        return f'<rect width="{w}" height="{h}" rx="10" fill="{col}"/><g clip-path="inset(0 round 10px)">{lines}</g>'
    if kind=='rubber':
        d=''.join(f'<rect x="{x}" y="{y}" width="6" height="6" transform="rotate(45 {x+3} {y+3})" fill="{_mix(col,"#000000",0.35)}"/>' for x in range(4,w-4,12) for y in range(4,h-4,12))
        return f'<rect width="{w}" height="{h}" rx="10" fill="{col}"/>{d}'
    if kind=='plastic':
        import random;r=random.Random(5)
        d=''.join(f'<circle cx="{r.uniform(0,w):.1f}" cy="{r.uniform(0,h):.1f}" r="0.9" fill="{_mix(col,"#FFFFFF",0.2)}"/>' for _ in range(120))
        return f'<rect width="{w}" height="{h}" rx="10" fill="{col}"/>{d}'
    return f'<defs><radialGradient id="{cid}"><stop offset="0" stop-color="#FFFFFF"/><stop offset="0.35" stop-color="{col}"/><stop offset="1" stop-color="{_mix(col,"#000000",0.55)}"/></radialGradient></defs><rect width="{w}" height="{h}" rx="10" fill="url(#{cid})"/>'

# Texturprofil des Waffentyps auf dem Blatt (claude-0.9, Entscheidung des Nutzers 18.10.2026: „Ja, Texturprofil anzeigen“)
ENERGY_HEX={'orange':'#FF8A2A','blue':'#3D8BFF','violet':'#A15CFF','light_blue':'#7FD4FF','cyan':'#22E3E8'}
WEAR_DE={'subtle':'dezent','medium':'mittel','strong':'stark'}
PROFILE_TILES=[('housing','GEHÄUSE'),('metal','METALL'),('rubber','GUMMI'),('energy','ENERGIE'),('edge_wear','KANTENABNUTZUNG'),('decals','DECALS')]

def _profile_swatch(key,e,w,h,cols):
    """Musterfeld einer Profil-Kachel: Material-ID des Katalogs (Gehäuse/Metall/Gummi/Energie), Abnutzungsstufe, Toolgen-Decals"""
    if key=='edge_wear':
        lv=texcat.wear_levels();order=sorted(lv,key=lambda k:lv[k]['toolgen']);cov=lv[e['level']]['coverage']
        bare=texcat.bare_metal();base=cols['housing']
        import random;r=random.Random(zlib.crc32(e['level'].encode()))
        # Lackfläche, oben eine harte Kante mit blankem Metall; Anteil der Flecken = coverage der Stufe
        chips=''.join(f'<rect x="{x}" y="0" width="{r.uniform(3,9):.1f}" height="{r.uniform(3,6+20*cov):.1f}" rx="1.5" fill="{bare}"/>' for x in range(2,w-60,7) if r.random()<cov*2.2)
        meter=''.join(f'<rect x="{w-54+i*18}" y="{h-6-(12+i*10)}" width="14" height="{12+i*10}" rx="2" fill="{_mix(cols["accent"],"#0E1622",0 if i<=order.index(e["level"]) else 0.75)}"/>' for i in range(3))
        return f'<rect width="{w}" height="{h}" rx="8" fill="{base}"/><rect width="{w-62}" height="4" fill="{_mix(base,"#FFFFFF",0.25)}"/>{chips}<rect x="{w-62}" y="0" width="62" height="{h}" fill="#0E1622" opacity="0.55"/>{meter}'
    if key=='decals':
        ids=e['toolgen'][:2];fs=12
        tx=''.join(f'<text x="{w/2}" y="{h/2+(i-(len(ids)-1)/2)*16+4:.0f}" text-anchor="middle" font-family="JetBrains Mono, ui-monospace, monospace" font-size="{fs}" fill="#E6ECF2">{_h.escape(t)}</text>' for i,t in enumerate(ids))
        return f'<rect width="{w}" height="{h}" rx="8" fill="#0B121C" stroke="{cols["accent"]}" stroke-width="1.2" stroke-dasharray="5 4"/>{tx}'
    mid=e['material'];col=ENERGY_HEX.get(e.get('color'),cols['accent']) if key=='energy' else cols[key]
    kind={'painted':'lack','brushed':'brushed','rubber':'rubber','painted_matte':'plastic','energy_glass':'light'}.get(mid)
    if kind:return swatch_svg(kind,w,h,col)
    cid=f'pf{mid}{zlib.crc32(col.encode())%9999}'
    if mid=='ceramic':   # Keramik: heller, weicher Verlauf mit feinen Plattenfugen
        fug=''.join(f'<line x1="{x}" y1="0" x2="{x}" y2="{h}" stroke="{_mix(col,"#000000",0.18)}" stroke-width="1"/>' for x in range(w//3,w,w//3))
        return f'<defs><linearGradient id="{cid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{_mix(col,"#FFFFFF",0.45)}"/><stop offset="1" stop-color="{_mix(col,"#FFFFFF",0.1)}"/></linearGradient></defs><rect width="{w}" height="{h}" rx="10" fill="url(#{cid})"/>{fug}'
    if mid=='satin':     # satiniert: flacher, breiter Schimmer
        return f'<defs><linearGradient id="{cid}" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{_mix(col,"#000000",0.12)}"/><stop offset="0.5" stop-color="{_mix(col,"#FFFFFF",0.12)}"/><stop offset="1" stop-color="{_mix(col,"#000000",0.12)}"/></linearGradient></defs><rect width="{w}" height="{h}" rx="10" fill="url(#{cid})"/>'
    if mid=='polished':  # poliert: harter Glanzstreifen
        return f'<defs><linearGradient id="{cid}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{_mix(col,"#000000",0.3)}"/><stop offset="0.44" stop-color="{col}"/><stop offset="0.5" stop-color="#FFFFFF"/><stop offset="0.56" stop-color="{col}"/><stop offset="1" stop-color="{_mix(col,"#000000",0.35)}"/></linearGradient></defs><rect width="{w}" height="{h}" rx="10" fill="url(#{cid})"/>'
    # Rauguss: grobe helle und dunkle Poren
    import random;r=random.Random(11)
    d=''.join(f'<circle cx="{r.uniform(0,w):.1f}" cy="{r.uniform(0,h):.1f}" r="{r.uniform(0.8,2.2):.1f}" fill="{_mix(col,"#000000" if r.random()<0.6 else "#FFFFFF",0.3)}"/>' for _ in range(90))
    return f'<rect width="{w}" height="{h}" rx="10" fill="{col}"/>{d}'

def profile_strip(prof,type_de,w,h,cols,ptype=None):
    """Leiste TEXTURPROFIL unter der Materialansicht: sechs Kacheln aus texprofile (Gehäuse, Metall, Gummi, Energie, Abnutzung, Decals)"""
    G_=12;tw=(w-32-5*G_)//6;sh=44
    tiles=''
    for key,cap in PROFILE_TILES:
        e=prof[key]
        if key=='edge_wear':sub='Stufe '+WEAR_DE[e['level']]
        elif key=='decals':sub='Toolgen-Decals'
        else:sub=texcat.material(e['material'])['name']['de']
        sub=sub[:1].upper()+sub[1:]
        sw=f'<svg width="{tw}" height="{sh}" viewBox="0 0 {tw} {sh}" role="img" aria-label="{_h.escape(cap.title()+": "+sub)}">{_profile_swatch(key,e,tw,sh,cols)}</svg>'
        tiles+=(f'<div style="display:flex;flex-direction:column;gap:5px;width:{tw}px;min-width:0">{sw}'
                f'<span style="font-family:\'Chakra Petch\',sans-serif;font-size:13px;letter-spacing:1.4px;color:#8FA0B3;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{cap}</span>'
                f'<span style="font-family:\'Chakra Petch\',sans-serif;font-size:16px;font-weight:600;color:#E6ECF2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{_h.escape(sub)}</span>'
                f'<span style="font-size:15px;line-height:1.2;color:#C7D1DC;overflow:hidden;max-height:36px">„{_h.escape(e["text_de"])}“</span></div>')
    return (f'<div style="width:{w}px;height:{h}px;box-sizing:border-box;border-radius:18px;border:1px solid #22314A;background:#111A27;padding:12px 16px;display:flex;flex-direction:column;gap:10px;overflow:hidden;flex-shrink:0">'
            f'<span style="font-family:\'Chakra Petch\',sans-serif;font-size:16px;letter-spacing:3px;color:#8FA0B3;white-space:nowrap">TEXTURPROFIL · {_h.escape(type_de.upper())} · '
            +(f'VORSCHLAG · ABGELEITET VON {_h.escape(TYPE_DE_OF.get(src,src).upper())}' if (src:=texprofile.DERIVED_FROM.get(ptype)) else 'TEXTUR-BLATT WAFFEN 1–9')+'</span>'
            f'<div style="display:flex;gap:{G_}px">{tiles}</div></div>')

def _bbox(parts):
    vs=[q for P in parts for f in P['F'] for q in f['v']]
    return [(min(q[i] for q in vs),max(q[i] for q in vs)) for i in range(3)]

def detail_view(m,center,W,H,ow=3.0):
    core=[P for P in m.parts if (P.get('label') or '') in DETAIL_LABELS[:6]]
    sel=core or [P for P in m.parts if (P.get('label') or '') in DETAIL_LABELS]
    if not sel:return None,None
    names=sorted({P['label'] for P in sel},key=DETAIL_LABELS.index)
    yaw,pitch=-28,-22
    yw,pt=math.radians(yaw),math.radians(pitch)
    # Rahmen = sichtbarer Teil von Griff/Abzug/Bügel (der Griffkopf steckt im Gehäuse), mittig in der Fläche unter der Überschrift
    TOP,BOT,SIDE,FILL=58,26,40,1.4
    near=[P for P in m.parts if (P.get('label') or '') in DETAIL_LABELS+DETAIL_FRAME_EXTRA]
    pr=[tf((q[0]-center[0],q[1]-center[1],q[2]-center[2]),yw,pt) for P in near for f in P['F'] for q in f['v']]
    box=[min(p[0] for p in pr),min(p[1] for p in pr),max(p[0] for p in pr),max(p[1] for p in pr)]
    o=((box[0]+box[2])/2,(box[1]+box[3])/2)
    s0=min((W-2*SIDE)/max(box[2]-box[0],1),(H-TOP-BOT)/max(box[3]-box[1],1))
    svgview(m,yaw,pitch,center,W,H,s0,ow=ow,origin=o,shadow=False,image=False)  # Vorlauf: was davon ist sichtbar? (nur raster.LAST, kein Bild)
    vis=raster.LAST.get('boxes',{})
    vb=[vis[n] for n in names if n in vis]
    if vb:
        px=[min(b[0] for b in vb),min(b[1] for b in vb),max(b[2] for b in vb),max(b[3] for b in vb)]
        # Magazin im Griff (Pistole): Bodenplatte unter dem Griff gehört mit in den Rahmen; Magazin vor dem Abzug oder oben auf dem Gehäuse nicht
        for n in DETAIL_LABELS[6:]:
            b=vis.get(n)
            if n not in names and b and px[0]<=(b[0]+b[2])/2<=px[2] and (b[1]+b[3])/2>(px[1]+px[3])/2:
                px=[min(px[0],b[0]),min(px[1],b[1]),max(px[2],b[2]),max(px[3],b[3])]
        for n in DETAIL_FRAME_EXTRA:
            b=vis.get(n)
            if b:px=[min(px[0],b[0]),min(px[1],b[1]),max(px[2],b[2]),max(px[3],b[3])]
        box=[o[0]+(px[0]-W/2)/s0,o[1]+(px[1]-H/2)/s0,o[0]+(px[2]-W/2)/s0,o[1]+(px[3]-H/2)/s0]
        o=((box[0]+box[2])/2,(box[1]+box[3])/2)
    sc=min((W-2*SIDE)/max((box[2]-box[0])*FILL,1),(H-TOP-BOT)/max((box[3]-box[1])*FILL,1),4.5)
    v=svgview(m,yaw,pitch,center,W,H,sc,pad=(TOP-BOT)/2,ow=ow,origin=o,shadow=False)
    return v,names

def _callouts(anchors,MW,MH,col,cy_model,k=1.0):
    def pillw(lb):return (len(lb)*13.5+40)*k
    call=''
    items=sorted(anchors.items(),key=lambda kv:kv[1][0])
    top=[it for it in items if it[1][1]<cy_model];bot=[it for it in items if it[1][1]>=cy_model]
    for grp,yl in ((top,86*k),(bot,MH-66*k)):
        n=len(grp)
        if not n:continue
        wds=[pillw(lb) for lb,_ in grp]
        xsl=[0.5*MW*(i+1)/(n+1)+0.5*a[0] for i,(lb,a) in enumerate(grp)]
        for i in range(1,n):
            mn=xsl[i-1]+(wds[i-1]+wds[i])/2+16
            if xsl[i]<mn:xsl[i]=mn
        if xsl[-1]+wds[-1]/2>MW-28:
            xsl[-1]=MW-28-wds[-1]/2
            for i in range(n-2,-1,-1):
                mx_=xsl[i+1]-(wds[i]+wds[i+1])/2-16
                if xsl[i]>mx_:xsl[i]=mx_
        if xsl[0]-wds[0]/2<28:
            sh=28-(xsl[0]-wds[0]/2);xsl=[x+sh for x in xsl]
        for k_,(lb,(ax,ay)) in enumerate(grp):
            lx=xsl[k_];y0=yl+(16*k if yl<MH/2 else -34*k)
            # Knick-Hinweislinie: senkrecht vom Etikett, dann zum Anker
            ky=y0+(ay-y0)*0.35
            call+=f'<polyline points="{lx:.0f},{y0:.0f} {lx:.0f},{ky:.0f} {ax:.0f},{ay:.0f}" fill="none" stroke="#E6ECF2" stroke-width="1.8" opacity="0.9"/><circle cx="{ax:.0f}" cy="{ay:.0f}" r="{6*k:.0f}" fill="#E6ECF2" stroke="#0A0A0D" stroke-width="2"/>'
            w_=pillw(lb)
            call+=f'<g transform="translate({lx:.0f},{yl:.0f})"><rect x="{-w_/2:.0f}" y="{-34*k:.0f}" width="{w_:.0f}" height="{46*k:.0f}" rx="{23*k:.0f}" fill="#0E1622" stroke="{col}" stroke-width="1.8"/><text x="0" y="{-4*k:.0f}" text-anchor="middle" font-family="Chakra Petch, sans-serif" font-size="{19*k:.0f}" font-weight="600" letter-spacing="1.6" fill="#E6ECF2">{_h.escape(lb.upper())}</text></g>'
    return call

def DEFS(fid):return f'<defs><filter id="gl{fid}" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="8"/></filter><pattern id="gr{fid}" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="#1A2636" stroke-width="1"/></pattern></defs>'

OP_TILES=[('reload_de','NACHLADEN'),('action_de','SPANNEN · AUFLADEN · MECHANIK'),('fire_de','FEUERN · EINSATZ')]
def op_strip(op,moving,w,h,col):
    """Leiste BEDIENUNG (claude-0.10 neue Waffentypen, ab claude-0.11 alle Waffenblätter): Nachladen, Mechanik, Feuern aus META['op']
    bzw. ops.OPS, dazu die beweglichen Teile"""
    G_=12;tw=(w-32-2*G_)//3
    tiles=''.join(f'<div style="display:flex;flex-direction:column;gap:5px;width:{tw}px;min-width:0">'
                  f'<span style="font-family:\'Chakra Petch\',sans-serif;font-size:13px;letter-spacing:1.4px;color:{col};white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{cap}</span>'
                  f'<span style="font-size:15px;line-height:1.25;color:#E6ECF2;overflow:hidden;max-height:76px">{_h.escape(op[k])}</span></div>' for k,cap in OP_TILES)
    mv=' · '.join(moving) if moving else 'keine (fest verbunden)'
    return (f'<div style="width:{w}px;height:{h}px;box-sizing:border-box;border-radius:18px;border:1px solid #22314A;background:#111A27;padding:12px 16px;display:flex;flex-direction:column;gap:8px;overflow:hidden;flex-shrink:0">'
            f'<span style="font-family:\'Chakra Petch\',sans-serif;font-size:16px;letter-spacing:3px;color:#8FA0B3;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">BEDIENUNG · BEWEGLICHE TEILE: {_h.escape(mv.upper())}</span>'
            f'<div style="display:flex;gap:{G_}px">{tiles}</div></div>')

def panel(inner,w,h,label,fid,aria,small=False):
    return f'''<div style="position:relative;width:{w}px;height:{h}px;border-radius:18px;border:1px solid #22314A;background:#111A27;overflow:hidden;flex-shrink:0">
<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" style="display:block" role="img" aria-label="{_h.escape(aria)}">{DEFS(fid)}<rect width="{w}" height="{h}" fill="url(#gr{fid})"/>{inner}</svg>
<span style="position:absolute;left:12px;top:10px;padding:4px 10px;border-radius:8px;background:rgba(14,22,34,0.85);font-family:'Chakra Petch',sans-serif;font-size:{13 if small else 19}px;letter-spacing:3px;color:#8FA0B3">{label}</span></div>'''

EN={'Gehäuse':'receiver','Griff':'pistol grip','Abzug':'trigger with guard','Magazin':'magazine','Lauf':'barrel','Mündung':'muzzle','Mündungsbremse':'muzzle brake','Zielfernrohr':'scope on mounting rings','Visier':'sight','Schaft':'stock','Energiezelle':'energy cell','Kühlrippen':'cooling fins','Montageringe':'scope rings','Laufverkleidung':'barrel shroud','Vordergriff':'foregrip','Doppellauf':'double barrel','Trommel':'revolver cylinder','Sehne':'string','Wurfarm':'limb','Pfeil':'arrow','Umlenkrolle':'cam pulley','Pfeilauflage':'arrow rest','Stabilisator':'stabilizer','Rohr':'launch tube','Heckdüse':'rear exhaust','Abgasdüse':'rear exhaust','Raketenrohre':'rocket tubes','Handschutz':'handguard','Tragegriff':'carry handle','Kimme':'rear sight','Korn':'front sight','Ladeleiste':'charge indicator rail','Mündungsring':'muzzle ring','Schaftkappe':'butt plate','Wangenauflage':'cheek rest','Trommelmagazin':'drum magazine','Röhrenmagazin':'tube magazine','Pumpgriff':'pump grip','Kristallkern':'crystal core','Energiekugel':'energy orb','Bündelring':'focusing ring','Fokusring':'focusing ring','Fokusringe':'focusing rings','Laufmantel':'barrel jacket','Feuerkern':'fire core','Oberkiefer':'upper jaw','Unterkiefer':'lower jaw','Visierschiene':'sight rail','Ringvisier':'ring sight','Trichterheck':'flared rear funnel','Sicherungsmodul':'safety module','Rakete':'rocket','Spannmechanik':'cocking mechanism','Bolzen':'bolt','Mittelstück':'riser','Energie-Auge':'energy eye','Kondensator':'capacitor','Emitter':'emitter','Raketenkasten':'rocket pod','Heckkappe':'end cap','Verschluss':'breech','Kastenvisier':'box sight','Laufhülle':'barrel shroud','Laufkasten':'barrel housing','Ladekammer':'charging chamber','Beschleunigerring':'accelerator ring','Energiespule':'energy coil','Abschussrohr':'launch tube','Schalldämpfer':'suppressor','Montage':'mount','Rahmen':'frame','Energiekern':'energy core','Fokuskern':'focus core','Tragebügel mit Visier':'carry handle with sights','Oberlauf':'upper barrel','Unterlauf':'lower barrel','Energiemagazin':'energy magazine','Mittelstück':'riser','Abzugbügel':'trigger guard','Zweibein':'folded bipod','Kompensator':'compensator','Schlitten':'slide','Energiewürfel':'energy cube','Reflexvisier':'reflex sight','Käfig':'cage','Pulswürfel':'pulse cube','Feuerdämpfer':'flash hider','Kondensatorzelle':'capacitor cell','Fächeremitter':'fan emitter','Abschussrohre':'launch tubes','Kammerstängel':'bolt handle','Patronenfenster':'shell window','Klappschaft':'folding stock',
 # neue Typen claude-0.10
 'Ladehebel':'charging handle','Trommelriegel':'cylinder latch','Hahn':'hammer','Ausstoßerstange':'ejector rod','Kondensatorkammern':'capacitor chambers',
 'Beschleunigerschiene':'accelerator rail','Linearkern':'linear core','Spulenringe':'coil rings','Granathalter':'grenade holder','Ersatzgranate':'spare grenade',
 'Verriegelungshebel':'locking lever','Scharnier':'hinge','Kipplauf':'break-action barrel','Ladeklappe':'loading gate','Granattrommel':'grenade drum',
 'Trommelachse':'drum axle','Laufträger':'barrel carrier','Zuführdeckel':'feed cover','Munitionskasten':'ammo box','Patronengurt':'ammo belt',
 'Knauf':'pommel','Parierblock':'guard block','Parierstange':'cross guard','Klinge':'blade','Mittelrippe':'central ridge','Stange':'shaft',
 'Klingenfassung':'blade mount','Schildflügel':'shield wings','Schloss':'string latch','Bogenblock':'prod block','Spannhebel':'cocking lever',
 'Raketenmagazin':'rocket magazine','Abgasring':'exhaust ring',
 # neue Typen claude-0.10.1
 'Plasmakammer':'plasma chamber','Hitzeanzeige':'heat gauge','Entlüftungsklappe':'vent flap','Hitzespeicher':'heat sink','Raketenvorrat':'micro-missile reserve box',
 'Mikrorakete':'micro-missile','Kipprahmen':'top-break frame','Kippriegel':'top-break latch','Streumündung':'flared spread muzzle','Hahnschutz':'hammer shroud'}

def prompt_font(texts,width,height,sizes=(18,17,16,15,14)):
    """Schriftgröße des Prompt-Felds (claude-0.9): größte aus sizes, bei der die Absätze (JetBrains Mono, Zeichenbreite 0,6 em,
    Zeilenhöhe 1,5) samt zwei Zeilen Reserve in die Höhe passen; Umbruch an Leerzeichen wie im Browser, Bindestriche nicht mitgezählt
    (der Browser bricht dort zusätzlich, die Schätzung liegt also eher zu hoch)"""
    def lines(t,cpl):
        n,cur=1,0
        for w in t.split(' '):
            if cur and cur+1+len(w)>cpl:n+=1;cur=len(w)
            else:cur+=(1 if cur else 0)+len(w)
        return n
    for fs in sizes:
        cpl=int(width/(0.6*fs))
        if (sum(lines(t,cpl) for t in texts)+2)*fs*1.5<=height:return fs
    return sizes[-1]

def prompts(d,labels,mats,variant_letter,skin=None):
    pal=', '.join(d['palette']);vs=d.get('vs')
    import export_spec
    tp=texprofile.PROFILES.get(wtypes.key(d['name']))   # Texturprofil des Waffentyps (claude-0.9; neue Typen: Vorschlag 0.10); Bogen: kein Profil
    op=d.get('op');melee=d['name'] in wtypes.MELEE
    tp_de=tp_en=''
    if tp:
        tp_de='; '.join(f"{k} „{tp[f]['text_de']}“" for k,f in (('Gehäuse','housing'),('Metall','metal'),('Gummi','rubber'),('Energie','energy'),('Kantenabnutzung','edge_wear'),('Decals','decals')))
        en_=lambda f:texcat.material(tp[f]['material'])['name']['en']
        tp_en=(f"{en_('housing')} housing, {en_('metal')} metal, textured rubber grips, {tp['energy']['color'].replace('_',' ')} energy glass, "
               f"{tp['edge_wear']['level']} edge wear, decals ({', '.join(tp['decals']['toolgen'])})")
    vn=variants.name(variant_letter)   # englischer Variantenname (ab J), ältere Varianten ohne
    de=(f"Erstelle ein technisches Low-Poly-Concept-Art-Blatt für das Spiel Cube Escape: {d['name']}, Variante {variant_letter}{f' ({vn})' if vn else ''} „{d['nick']}“. "
        f"Form: {d['form']}. {d['desc']} "
        f"Pflicht-Bauteile, alle sichtbar und nachvollziehbar verbunden: {', '.join(labels)}. "
        f"Farbpalette: {pal}. Materialien: {', '.join(mats)}. "
        f"Ansichten: große isometrische Hauptansicht mit deutschen Bauteil-Beschriftungen, dazu Seitenansicht links und rechts, Vorder-, Rück-, Drauf- und Unteransicht – orthografisch, gleicher Maßstab, gemeinsame Bezugslinien – plus Detailansicht des {'Griffbereichs' if melee else 'Abzugsbereichs'}. "
        "Stil: futuristisch, industrial, Hard-Surface, abgeschrägte Gehäuse, kantige Panzerplatten, klare dunkle Konturen, flache Toon-Schattierung, dunkelblauer Rasterhintergrund. "
        +(MELEE_DE.get(d['name'],'') if melee else "Konstruktion: Abzug mit Bügel klar erkennbar, Magazin im Schacht, Lauf sichtbar aus dem Gehäuse, konsistente Achsen. Visier bzw. Zielfernrohr NICHT montiert zeichnen, sondern separat als modulares Anbauteil daneben; auf der Waffe bleibt nur die freie Visierschiene als Aufnahme. ")
        +(f"Visier: {vs['info']['title']} aus der Visier-Serie ({vs['id']}): {vs['info']['desc']} " if vs else "")
        +(f"Hauptskin „{skin[0]}“: {skin[1]}. " if skin else "")
        +(f"Texturprofil: {tp_de}. " if tp_de else "")
        +(f"Bedienung: Nachladen – {op['reload_de']}; Mechanik – {op['action_de']}; Feuern – {op['fire_de']}. " if op else "")+
        "Vermeiden: schwebende Teile, unbeabsichtigte Überschneidungen, zufällige Leuchtstreifen, Bloom, Unschärfe, Nebel, realistische Militärwaffen-Kopien.")
    if d['name']=='Raketenwerfer':
        de=de.replace('auf der Waffe bleibt nur die freie Visierschiene als Aufnahme.','auf der Waffe bleibt nur die freie Visierschiene als Aufnahme – seitlich links am Rohr montiert, damit das Rohr die Sichtlinie nicht verdeckt.')
    if d.get('iron'):   # feste Kimme/Korn (claude-0.17.1, KG01)
        de=de.replace('Visier bzw. Zielfernrohr NICHT montiert zeichnen, sondern separat als modulares Anbauteil daneben; auf der Waffe bleibt nur die freie Visierschiene als Aufnahme.',
                      'Kein Wechselvisier: Kimme mit Kerbe zwischen zwei Pfosten (hinten) und Korn (vorn) fest auf dem Schlitten, beschriftet, Kerbe und Kornspitze auf einer Linie parallel zum Lauf.')
    if d['name'] in CONSTRUCT_DE:de=de.replace('Magazin im Schacht',CONSTRUCT_DE[d['name']])   # Bauweise ohne Kastenmagazin (claude-0.10.1)
    en_parts=', '.join(EN.get(l,l) for l in labels)
    en=(f"Low-poly sci-fi weapon concept sheet for the game Cube Escape: futuristic {d.get('en_type','weapon')}, variant {variant_letter}{f' ({vn})' if vn else ''} \"{d['nick']}\". "
        f"Visible, logically connected parts: {en_parts}. Color palette {pal}. "
        +(MELEE_EN.get(d['name'],'') if melee else "Large isometric hero view with labeled callouts plus orthographic left, right, front, back, top and bottom views at identical scale, trigger-area detail. Draw the sight/scope detached as a separate modular attachment next to the weapon; the weapon shows only the empty sight rail. "
          if not d.get('iron') else "Large isometric hero view with labeled callouts plus orthographic left, right, front, back, top and bottom views at identical scale, trigger-area detail. No detachable sight: a rear sight with a notch between two posts and a front sight blade are fixed on the slide, labeled, notch and blade tip aligned parallel to the barrel. ")
        +("Sight rail mounted on the left side of the tube, offset from the bore axis. " if d['name']=='Raketenwerfer' else "")+
        (f"Sight: {VS_EN[vs['id']]} ({vs['id']}, sight series), drawn separately. " if vs else "")+
        (f"Skin \"{skin[0]}\": {skin[2]}. " if skin else "")+
        (f"Texture profile: {tp_en}. " if tp_en else "")+
        (f"Operation: reload – {op['reload_en']}; mechanism – {op['action_en']}; firing – {op['fire_en']}. " if op else "")+
        "Hard-surface industrial design, chamfered housings, clean dark outlines, flat cel shading, dark blue grid background, no bloom, no blur, no floating parts.")
    return de,en

TYPE_EN={'Pistole':'pistol','Sturmgewehr':'assault rifle','Impulsgewehr':'pulse rifle','Schrotflinte':'shotgun','Scharfschützengewehr':'sniper rifle','Maschinenpistole':'submachine gun','Fusionsgewehr':'fusion rifle','Spurgewehr':'trace rifle','Raketenwerfer':'rocket launcher','Bogen':'bow'}
TYPE_EN.update({'Scout-Gewehr':'semi-automatic scout rifle','Handfeuerwaffe':'heavy revolver hand cannon','Lineares Fusionsgewehr':'linear fusion rifle',
 'Spezial-Granatwerfer':'single-shot break-action grenade launcher','Schwerer Granatwerfer':'drum-fed heavy grenade launcher','Maschinengewehr':'belt-fed machine gun',
 'Schwert':'energy sword','Glefe':'glaive polearm with energy emitter','Schwere Armbrust':'heavy crossbow','Raketenpistole':'rocket-assisted sidearm',
 'Raketen-Impulsgewehr':'rocket-assisted pulse rifle','Slug-Schrotflinte':'semi-automatic slug shotgun'})   # neue Typen claude-0.10
TYPE_EN.update({'Hitze-Blaster':'magazine-less heat blaster pulse rifle with heat sink and vent flaps','Mikroraketen-Granatwerfer':'single-shot micro-missile grenade launcher',
 'Streuschuss-Handfeuerwaffe':'top-break spread-shot revolver hand cannon'})   # neue Typen claude-0.10.1
# Konstruktionssatz im Prompt: „Magazin im Schacht“ ersetzt, wo die Waffe kein Kastenmagazin hat (nur Typen ab claude-0.10.1; ältere Blätter bleiben bytegleich)
CONSTRUCT_DE={'Hitze-Blaster':'kein Magazin, stattdessen Hitzespeicher mit Kühlrippen und zwei seitliche Entlüftungsklappen',
 'Mikroraketen-Granatwerfer':'eine Mikrorakete im Abschussrohr, Vorrat im Raketenvorrat links',
 'Streuschuss-Handfeuerwaffe':'Trommel mit fünf Schrotkammern im Kipprahmen'}
TYPE_DE_OF={'pistol':'Pistole','assault_rifle':'Sturmgewehr','pulse_rifle':'Impulsgewehr','shotgun':'Schrotflinte','sniper_rifle':'Scharfschützengewehr',
 'smg':'Maschinenpistole','fusion_rifle':'Fusionsgewehr','trace_rifle':'Spurgewehr','rocket_launcher':'Raketenwerfer'}   # Toolgen-ID -> Blattname (Profilherkunft)
# Nahkampfwaffen (claude-0.10): eigener Konstruktionssatz im Prompt, kein Visier und keine Visierschiene
MELEE_DE={'Schwert':"Konstruktion: Klinge, Klingenwurzel, Parierblock, Parierstange, Griff und Knauf auf einer Achse fest verbunden; kein Abzug, kein Magazin, kein Visier und keine Visierschiene. ",
 'Glefe':"Konstruktion: Klinge mit Emitter, Klingenfassung, Energiezelle, Stange, Vordergriff und hinterer Griff mit Abzug im Bügel auf einer Achse fest verbunden; kein Visier und keine Visierschiene, der Emitter schießt aus der Hüfte. "}
MELEE_EN={'Schwert':"Large isometric hero view with labeled callouts plus orthographic left, right, front, back, top and bottom views at identical scale, grip-area detail. Blade, guard block, cross guard, grip and pommel on one axis; no trigger, no magazine, no sight, no rail. ",
 'Glefe':"Large isometric hero view with labeled callouts plus orthographic left, right, front, back, top and bottom views at identical scale, grip-area detail. Blade with emitter, blade mount with shield wings, energy cell, shaft, foregrip and rear grip with trigger on one axis; no sight, no rail, hip-fired emitter. "}

PRIO=['Gehäuse','Griff','Abzug','Magazin','Energiezelle','Energiemagazin','Trommelmagazin','Röhrenmagazin','Lauf','Doppellauf','Mündung','Mündungsbremse','Schaft','Visierschiene','Rohr','Abschussrohr','Abschussrohre','Wurfarm','Sehne','Pfeil','Mittelstück','Umlenkrolle','Pfeilauflage','Handschutz','Laufmantel','Laufverkleidung','Emitter']
def pick_labels(anchors,n=8):
    ks=sorted(anchors,key=lambda k:(PRIO.index(k) if k in PRIO else 50,k))[:n]
    return {k:anchors[k] for k in ks},[k for k in anchors if k not in ks]

def _shift_part(P,dx):
    Q=dict(P);Q['F']=[dict(f,v=[(x-dx,y,z) for x,y,z in f['v']]) for f in P['F']]
    dec=[]
    for plane,val,pts,c,em in P['dec']:
        if plane[0]=='z':pts=[(x-dx,y) for x,y in pts]
        elif plane[0]=='x':val=val-dx
        else:pts=[(x-dx,z) for x,z in pts]
        dec.append((plane,val,pts,c,em))
    Q['dec']=dec;return Q

def compact_sight(ms,gap=30):
    """Getrennte Visierteile (Kimme hinten, Korn vorne) rücken für die Visier-Ansicht zusammen,
    sonst bestimmt der Abstand über die ganze Waffenlänge den Maßstab und die Teile werden winzig."""
    xs=[(min(q[0] for f in P['F'] for q in f['v']),max(q[0] for f in P['F'] for q in f['v']),P) for P in ms.parts]
    cl=[]
    for x0,x1,P in sorted(xs,key=lambda t:t[0]):
        if cl and x0<=cl[-1][1]+gap:cl[-1][1]=max(cl[-1][1],x1);cl[-1][2].append(P)
        else:cl.append([x0,x1,[P]])
    if len(cl)<2:return ms,False
    out=Model();shift=0
    for i,(x0,x1,Ps) in enumerate(cl):
        if i:shift+=max(0,x0-cl[i-1][1]-gap)
        out.parts+=[_shift_part(P,shift) if shift else P for P in Ps]
    return out,shift>0

VS_EN={'VS01':'compact reflex sight with open window','VS02':'open holographic sight','VS03':'precision tube scope with objective lens',
 'VS04':'wide-angle round reflex sight','VS05':'high-precision long-range scope','VS06':'machine sight with closed tunnel hood',
 'VS07':'energy sight with glowing octagonal frame','VS08':'tracking sight window with marker corners, no tube',
 'VS09':'wide-range sight in a bolted industrial frame'}
def _sight_view(ms,yaw,pitch,center,W,H,sc,vs):
    """Visieransicht; Visier-Serie mit dem Glas-Durchgang wie auf den VS-Blättern (durchscheinend, Tönung des Visiers)"""
    if not vs:return svgview(ms,yaw,pitch,center,W,H,sc,ow=2.6,shadow=False)
    from vsheet import DRAW_ALPHA
    import vsmodels
    o=Model();g=Model();a=DRAW_ALPHA(vsmodels.TINTS[vs['info']['tint']][2])
    for P in ms.parts:
        if P.get('glass'):Q=dict(P);Q['alpha']=a;g.parts.append(Q)
        else:o.parts.append(P)
    return raster.rasterview(o,yaw,pitch,center,W,H,sc,0,2.6,shadow=False,glass=g)
def sight_panel(ms,center,w,h,fid,name,col,small=False,vs=None,none_text=None):
    if ms.parts and not vs:ms,_=compact_sight(ms)
    if not ms.parts:
        inner=f'<text x="{w/2}" y="{h/2}" text-anchor="middle" font-family="Chakra Petch, sans-serif" font-size="22" fill="#8FA0B3">{_h.escape(none_text or "Keine Optik – Visierschiene frei")}</text>'
        return panel(inner,w,h,'VISIER · SEPARAT',fid,name+' ohne separates Visier')
    hw_=w/2-24
    cap=1e9 if vs else 6   # Visier-Serie: formatfüllend (die Waffenblätter haben je eigenen Maßstab), sonst wie bis 0.6
    rear=name=='Bogen'      # Bogen-Pin: Rückansicht zeigt den Leuchtpunkt, wie ihn der Schütze sieht (claude-0.7)
    e1,e2=extent(ms,ISO[1],ISO[2],center);s1=min((hw_-40)/e1,(h-(60 if small else 130))/e2,cap)
    v1=_sight_view(ms,ISO[1],ISO[2],center,int(hw_),h-40,s1,vs)
    y2=90 if rear else 0
    e3,e4=extent(ms,y2,0,center);s2=min((hw_-40)/e3,(h-(60 if small else 130))/e4,cap)
    v2=_sight_view(ms,y2,0,center,int(hw_),h-40,s2,vs)
    labs=sorted({P['label'] for P in ms.parts if P.get('label')})
    cap=f"{vs['id']} · {vs['info']['title']}" if vs else " · ".join(labs) if labs else "Visier"
    inner=(f'<g transform="translate(16,24)">{v1}</g><g transform="translate({w/2+8:.0f},24)">{v2}</g>'
           f'<line x1="{w/2}" y1="56" x2="{w/2}" y2="{h-60}" stroke="#22314A" stroke-width="1.5"/>'
           f'<text x="{14 if small else 24}" y="{h-(12 if small else 26)}" font-family="Chakra Petch, sans-serif" font-size="{13 if small else 19}" letter-spacing="1.2" fill="#E6ECF2">{_h.escape(cap)} · modular auf Schiene, nicht fest verbaut</text>')
    return panel(inner,w,h,'VISIER · SEPARAT' if small else 'VISIER · SEPARAT (ISOMETRIE / '+('RÜCK' if rear else 'SEITE')+')',fid,name+(f' Visier {vs["id"]} {vs["info"]["title"]}' if vs else ' Visier')+' separat gezeichnet',small)

def _chip(x,y,c,fin,label):
    """Farbfeld eines Skin-Slots: Lack flach, poliert mit Verlauf und Glanzstreifen, Neon mit Leuchtrand"""
    from skinraster import tones
    if fin in ('polished_gold','polished_chrome'):
        t=tones(c,fin);gid=f'ch{zlib.crc32((c+fin).encode())%99999}'   # reproduzierbar (hash() ist je Prozess zufällig)
        sw=(f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{t[0]}"/><stop offset="0.42" stop-color="{t[1]}"/>'
            f'<stop offset="0.5" stop-color="{t[4]}"/><stop offset="0.58" stop-color="{t[1]}"/><stop offset="1" stop-color="{t[3]}"/></linearGradient></defs>'
            f'<rect x="{x}" y="{y}" width="34" height="34" rx="8" fill="url(#{gid})" stroke="#0A0A0D" stroke-width="1.5"/>')
    elif fin=='neon':sw=f'<rect x="{x-3}" y="{y-3}" width="40" height="40" rx="10" fill="{c}" opacity="0.35"/><rect x="{x}" y="{y}" width="34" height="34" rx="8" fill="{c}" stroke="#0A0A0D" stroke-width="1.5"/>'
    else:sw=f'<rect x="{x}" y="{y}" width="34" height="34" rx="8" fill="{c}" stroke="#0A0A0D" stroke-width="1.5"/>'
    return sw+f'<text x="{x+44}" y="{y+24}" font-family="Barlow, sans-serif" font-size="19" fill="#C7D1DC">{_h.escape(label)}</text>'

def skin_row(rsl,skinned,full,center,cw,ch,fid,name):
    """Feld SKIN/MUSTER: fünf Skins aus dem Katalog in der Basis-Palette, je mit Slots und Bausteinen"""
    out=''
    for j,rs in enumerate(rsl):
        mm,tx_,cs=skinned(0,rs,full)
        vh=ch-230
        e1,e2=extent(mm,ISO[1],ISO[2],center);sc=min((cw-70)/e1,(vh-70)/e2)
        vv=svgview(mm,ISO[1],ISO[2],center,cw,vh,sc,ow=2.6,texture=tx_).replace('<image x="0" y="0"','<image x="0" y="26"',1)
        inner=vv;y0=vh+24
        for k,sl in enumerate(skins.slots_used(rs)[:6]):
            c,fin,src=cs[sl]
            lab=skins.SLOT_DE[sl]+(' · '+skins.FINISH_DE[fin] if fin!='paint' else '')+(' *' if src=='swatch' else '')
            inner+=_chip(24+(k%2)*((cw-40)//2),y0+(k//2)*46,c,fin,lab)
        bl=' · '.join(skins.BLOCKS[b] for b in skins.summary(rs))
        if any(cs[sl][2]=='swatch' for sl in skins.slots_used(rs)):
            inner+=f'<text x="24" y="{ch-46}" font-family="Barlow, sans-serif" font-size="15" fill="#6F8093">* Kanal an der Waffe unbelegt: Farbfeld der Blatt-Palette</text>'
        inner+=f'<text x="24" y="{ch-22}" font-family="Chakra Petch, sans-serif" font-size="15" letter-spacing="0.8" fill="#8FA0B3">{_h.escape(bl.upper())}</text>'
        lab=f'SKIN/MUSTER {j+1}/5 · {rs["name"].upper()}'+(' · HAUPTSKIN' if j==0 else '')
        out+=panel(inner,cw,ch,lab,fid,f'{name} Skin {rs["name"]}')
    return out

def sheet(d,variant_letter):
    """Konzeptblatt XL -> (page, Prompt de, Prompt en); die Bilder kodiert raster.deferred parallel (claude-0.19)."""
    with raster.deferred() as resolve:
        page,de,en=_sheet(d,variant_letter)
        return resolve(page),de,en
def _sheet(d,variant_letter):
    full=d['m'];center=d['center'];fid='x'+d['fid'];col=d['col']
    m,ms=split_sight(full)
    iron=any(P.get('iron') for P in full.parts)   # feste Kimme/Korn auf dem Schlitten (claude-0.17.1, KG01): auf der Waffe gezeichnet, kein Wechselvisier
    import export_spec   # Modelleinheit des Blatts (Meter je Einheit) für die Katalog-Muster in mm
    unit_m=export_spec.model_unit(d['name'],full)
    # ---------- Skins (claude-0.3): fünf je Blatt, der erste ist der Hauptskin (Isometrie, Orthos, Farbvarianten)
    sid=f'K{variant_letter}{d["num"]}'
    rsl=[skins.resolve(full,k,sid,d['num'],d['palette']) for k in skins.pick(sid,full,d['num'],d['palette'])];hero=rsl[0]
    cpal,_=channel_palettes(full,m,d['palette'],d['pill'],CHANNELS)
    roles=color_roles(m)
    def skinned(j,rs,mf):
        cs=skins.slot_colors(rs,cpal[j]['channels'],cpal[j]['swatches'])
        return split_sight(skins.apply(mf,rs,cs))[0],skin_texture(rs,cs),cs
    mh,htex,_=skinned(0,hero,full)
    SKH=1000
    W,H0=4800,3400;PAD=80;G=32;H=H0+G+SKH
    # ---------- Isometrie mit Beschriftungen
    MW,MH=2700,1800
    ew,eh=extent(mh,ISO[1],ISO[2],center)
    sm=min((MW-200)/ew,(MH-420)/eh,6.0)
    v=svgview(mh,ISO[1],ISO[2],center,MW,MH,sm,ow=4.6,texture=htex)
    anchors,rest=pick_labels(dict(raster.LAST.get('anchors',{})))
    call=_callouts(anchors,MW,MH,col,MH/2,k=1.35)
    if rest:call+=f'<text x="28" y="{MH-24}" font-family="Barlow, sans-serif" font-size="20" fill="#8FA0B3">Weitere Bauteile: {_h.escape(", ".join(sorted(rest)))}</text>'
    iso=panel(v+call,MW,MH,ISO[0]+(' · KIMME/KORN AM SCHLITTEN · HAUPTSKIN ' if iron else ' · OHNE VISIER · HAUPTSKIN ')+hero['name'].upper(),fid,f"{d['name']} isometrische Ansicht mit Bauteilbeschriftungen, Visier separat")
    # ---------- Ortho
    RW=W-2*PAD-MW-G
    geo={lb:model_origin(mh,y,p,center) for lb,y,p in ORTHO}
    hwL,hhL=geo['SEITENANSICHT LINKS'][1],geo['SEITENANSICHT LINKS'][2];hhT=geo['DRAUFSICHT'][2];hwF=geo['VORDERANSICHT'][1]
    def obox(lb,yw,pt,w,h,ss):
        o,hw,hh=geo[lb]
        vv=svgview(mh,yw,pt,center,w,h,ss,ow=3.0,origin=o,texture=htex).replace('<image x="0" y="0"','<image x="0" y="12"',1)
        cy=h/2+12;cx=w/2;ref=''
        if pt==0:
            for yy in (cy-hh*ss,cy+hh*ss):ref+=f'<line x1="0" y1="{yy:.1f}" x2="{w}" y2="{yy:.1f}" stroke="#4A6080" stroke-width="1.4" stroke-dasharray="8 8"/>'
            ref+=f'<line x1="{cx}" y1="0" x2="{cx}" y2="{h}" stroke="#2E405A" stroke-width="1.2" stroke-dasharray="2 8"/>'
        else:
            for xx in (cx-hw*ss,cx+hw*ss):ref+=f'<line x1="{xx:.1f}" y1="0" x2="{xx:.1f}" y2="{h}" stroke="#4A6080" stroke-width="1.4" stroke-dasharray="8 8"/>'
            ref+=f'<line x1="0" y1="{cy}" x2="{w}" y2="{cy}" stroke="#2E405A" stroke-width="1.2" stroke-dasharray="2 8"/>'
        return panel(ref+vv,w,h,lb,fid,f"{d['name']} {lb.lower()}")
    AV=MH
    if hwL>2.0*hhL:
        g=18
        ss=min((RW-90)/(2*hwL),(AV-5*90-4*g)/(2*(3*hhL+2*hhT)),((RW-g)/2-70)/(2*hwF))
        hL=int(2*hhL*ss+90);hT=int(2*hhT*ss+90);hF=AV-2*hL-2*hT-4*g
        rows=[obox('SEITENANSICHT LINKS',0,0,RW,hL,ss),obox('SEITENANSICHT RECHTS',180,0,RW,hL,ss)]
        fr=obox('VORDERANSICHT',-90,0,(RW-g)//2,hF,ss)+obox('RÜCKANSICHT',90,0,(RW-g)//2,hF,ss)
        ortho=f'<div style="display:flex;flex-direction:column;gap:{g}px;width:{RW}px;height:{AV}px">'+rows[0]+rows[1]+f'<div style="display:flex;gap:{g}px">{fr}</div>'+obox('DRAUFSICHT',0,90,RW,hT,ss)+obox('UNTERANSICHT',0,-90,RW,hT,ss)+'</div>'
    else:
        g=22;bw=(RW-g)//2;bh=(AV-2*g)//3
        ss=min(min((bw/2-46)/hw,(bh/2-66)/hh) for _,hw,hh in geo.values())
        ortho=f'<div style="display:grid;grid-template-columns:repeat(2,{bw}px);grid-auto-rows:{bh}px;gap:{g}px">'+''.join(obox(lb,y,p,bw,bh,ss) for lb,y,p in ORTHO)+'</div>'
    # ---------- untere Reihe
    BH=H0-2*PAD-180-G-MH-G
    DW=900;ph=(BH-20)//2
    dv,dnames=detail_view(m,center,DW,ph)
    if dv is None:dv,dnames='',[]
    melee=d['name'] in wtypes.MELEE   # Schwert/Glefe (claude-0.10): Griffbereich, kein Visier
    det=panel(dv,DW,ph,('DETAIL · GRIFFBEREICH (' if melee and 'Abzug' not in dnames else 'DETAIL · ABZUGSBEREICH (')+(", ".join(dnames) if dnames else "Griff")+')',fid,f"{d['name']} Detailansicht Abzugsbereich von schräg unten")
    sp=sight_panel(ms,center,DW,ph,fid,d['name'],col,vs=d.get('vs'),none_text='Kein Visier – Nahkampfwaffe, keine Visierschiene' if melee else 'Kimme und Korn fest auf dem Schlitten – kein Wechselvisier' if iron else None)
    det=f'<div style="display:flex;flex-direction:column;gap:20px;width:{DW}px">{det}{sp}</div>'
    # Material
    MWd=1180
    pkey=wtypes.key(d['name'])
    prof=texprofile.PROFILES.get(pkey)   # Bogen: kein Profil, Feld wie bis 0.8
    PH=176 if prof else 0
    OH=150 if d.get('op') else 0          # Leiste BEDIENUNG (claude-0.10, neue Typen; ab 0.11 alle Waffenblätter)
    mh=BH-190-(PH+18 if prof else 0)-(OH+18 if OH else 0)
    me,mhh=extent(m,ISO[1],ISO[2],center)
    msc=min((MWd-90)/me,(mh-90)/mhh)
    mv=svgview(m,ISO[1],ISO[2],center,MWd,mh,msc,ow=3.0,texture=make_texture(unit_m=unit_m))
    used={}
    for P in m.parts:
        k=material_of(P);used.setdefault(k,P['col'])
    sw=''
    for nm,k in MATS:
        if k not in used:continue
        sw+=f'<div style="display:flex;flex-direction:column;gap:8px;width:210px"><svg width="210" height="96" viewBox="0 0 210 96" role="img" aria-label="Muster {nm.lower()}">{swatch_svg(k,210,96,used[k])}</svg><span style="font-family:\'Chakra Petch\',sans-serif;font-size:16px;letter-spacing:1.5px;color:#C7D1DC;line-height:1.25">{nm}</span></div>'
    pstrip=''
    if prof:   # Farben der Kacheln aus dem Blatt (Basis-Palette), Energie in der Farbe des Profils
        pcols=dict(housing=used.get('lack',d['palette'][0]),metal=used.get('brushed','#8C96A3'),rubber=used.get('rubber','#2A2F36'),accent=col)
        pstrip=profile_strip(prof,d['name'],MWd,PH,pcols,ptype=pkey)
    if OH:pstrip+=op_strip(d['op'],d['op'].get('moving') or [wtypes.MOTION_SHORT_DE[k] for k in wtypes.of(d['name']).get('motions',[])],MWd,OH,col)
    matp=f'<div style="display:flex;flex-direction:column;gap:18px;width:{MWd}px">{panel(mv,MWd,mh,"MATERIAL & TEXTUREN",fid,d["name"]+" Materialansicht mit Texturen")}<div style="display:flex;gap:18px">{sw}</div>{pstrip}</div>'
    # Farbvarianten
    VW=1380;vw=(VW-24)//2;vh=(BH-24)//2
    vs=''
    base=('BASIS · '+d['pill'],d['palette'])
    for j,(vn,pal) in enumerate([base]+VARIANTS[:3]):
        mm,tx_,_=skinned(j,hero,recolor(full,pal,role=roles) if j else full)
        e1,e2=extent(mm,ISO[1],ISO[2],center);sc=min((vw-60)/e1,(vh-110)/e2)
        vv=svgview(mm,ISO[1],ISO[2],center,vw,vh,sc,ow=2.4,texture=tx_)
        dots=''.join(f'<rect x="{24+i*36}" y="{vh-46}" width="28" height="28" rx="7" fill="{c}" stroke="#0A0A0D" stroke-width="1"/>' for i,c in enumerate(pal))
        vs+=panel(vv+dots,vw,vh,vn if len(vn)<44 else vn[:42]+'…',fid,f"{d['name']} Farbvariante {vn}")
    varp=f'<div style="display:grid;grid-template-columns:repeat(2,{vw}px);grid-auto-rows:{vh}px;gap:24px;width:{VW}px">{vs}</div>'
    # Prompt
    m=full
    labels=sorted({P['label'] for P in m.parts if P.get('label') and not (d.get('vs') and P.get('sight'))})   # Visier-Serie: Teile nicht einzeln
    mats=[nm.title() for nm,k in MATS if k in used]
    d2=dict(d);d2['en_type']=TYPE_EN.get(d['name'],'weapon')
    d2['iron']=iron
    de,en=prompts(d2,labels,mats,variant_letter,skin=(hero['name'],)+skins.DESC[hero['id']])
    PW=W-2*PAD-DW-MWd-VW-3*G
    pfs=prompt_font((de,en),PW-56,BH-150)   # Texturprofil verlängert die Prompts: Schrift nur bei Bedarf kleiner (Feld bleibt gleich groß)
    pr=f'''<div style="width:{PW}px;height:{BH}px;box-sizing:border-box;border-radius:18px;border:1px solid #22314A;background:#0B121C;padding:26px 28px;display:flex;flex-direction:column;gap:14px;overflow:hidden">
<span style="font-family:'Chakra Petch',sans-serif;font-size:19px;letter-spacing:3px;color:#8FA0B3">PROMPT · DEUTSCH</span>
<p style="margin:0;font-family:'JetBrains Mono',ui-monospace,monospace;font-size:{pfs}px;line-height:1.5;color:#E6ECF2;user-select:all">{_h.escape(de)}</p>
<span style="font-family:'Chakra Petch',sans-serif;font-size:19px;letter-spacing:3px;color:#8FA0B3;margin-top:8px">PROMPT · ENGLISCH (BILDGENERATOR)</span>
<p style="margin:0;font-family:'JetBrains Mono',ui-monospace,monospace;font-size:{pfs}px;line-height:1.5;color:#C7D1DC;user-select:all">{_h.escape(en)}</p></div>'''
    hdr_sight='OHNE VISIER' if melee else 'KIMME/KORN AM SCHLITTEN' if iron else 'VISIER SEPARAT'
    pal=''.join(f'<div style="display:flex;align-items:center;gap:10px"><div style="width:50px;height:50px;border-radius:12px;background:{c}"></div><span style="font-size:19px;color:#8FA0B3">{c}</span></div>' for c in d['palette'])
    page=f'''<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>{d['num']} {d['name']} Variante {_h.escape(variants.title(variant_letter))} Konzeptblatt XL</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
{FONT_CSS}
<style>body{{margin:0}}</style>
</helmet>
<div style="width:{W}px;height:{H}px;box-sizing:border-box;padding:{PAD}px;background:#0E1622;color:#E6ECF2;font-family:Barlow,sans-serif;display:flex;flex-direction:column;gap:{G}px">
<div style="height:180px;display:flex;justify-content:space-between;align-items:center;gap:40px">
<div style="display:flex;align-items:center;gap:30px;min-width:0">
<span style="font-family:'Chakra Petch',sans-serif;font-size:140px;font-weight:700;line-height:1;color:{col}">{d['num']}</span>
<div style="display:flex;flex-direction:column;gap:8px;min-width:0">
<span style="font-family:'Chakra Petch',sans-serif;font-size:74px;font-weight:700;letter-spacing:6px;line-height:1.05">{_h.escape(d['name'].upper())} · VARIANTE {_h.escape(variants.title(variant_letter).upper())}</span>
<span style="font-size:25px;letter-spacing:4px;color:#8FA0B3">„{_h.escape(d['nick'].upper())}“ · KONZEPTBLATT XL · {hdr_sight} · HAUPTSKIN {_h.escape(hero['name'].upper())} · {_h.escape(d['form'])}</span>
</div>
</div>
<div style="display:flex;align-items:center;gap:30px;flex-shrink:0">
<div style="display:flex;gap:20px">{pal}</div>
<span style="padding:16px 32px;border:1.5px solid {col};border-radius:999px;color:{col};font-family:'Chakra Petch',sans-serif;font-size:24px;font-weight:600;letter-spacing:3px;white-space:nowrap">{_h.escape(d['pill'])}</span>
</div>
</div>
<div style="display:flex;gap:{G}px;height:{MH}px">{iso}{ortho}</div>
<div style="display:flex;gap:{G}px;height:{BH}px">{det}{matp}{varp}{pr}</div>
<div style="display:flex;gap:{G}px;height:{SKH}px">{skin_row(rsl,skinned,full,center,(W-2*PAD-4*G)//5,SKH,fid,d['name'])}</div>
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
    return page,de,en
