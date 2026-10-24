import math,colorsys
OL='#0A0A0D'
def hx(c):c=c.lstrip('#');return [int(c[i:i+2],16)/255 for i in (0,2,4)]
def lum(c,f):
    r,g,b=hx(c);h,l,s=colorsys.rgb_to_hls(r,g,b)
    l=l*f if f<1 else l+(1-l)*(f-1)*0.9
    r,g,b=colorsys.hls_to_rgb(h,max(0,min(1,l)),s);return '#%02X%02X%02X'%(round(r*255),round(g*255),round(b*255))
def roundpoly(pts,r=8,seg=4):
    n=len(pts);out=[]
    for i in range(n):
        p0,p1,p2=pts[i-1],pts[i],pts[(i+1)%n]
        a=(p0[0]-p1[0],p0[1]-p1[1]);b=(p2[0]-p1[0],p2[1]-p1[1])
        la=math.hypot(*a);lb=math.hypot(*b);rr=min(r,la/2.1,lb/2.1)
        if rr<1:out.append(p1);continue
        s=(p1[0]+a[0]/la*rr,p1[1]+a[1]/la*rr);e=(p1[0]+b[0]/lb*rr,p1[1]+b[1]/lb*rr)
        for k in range(seg+1):
            t=k/seg;q0=((1-t)*s[0]+t*p1[0],(1-t)*s[1]+t*p1[1]);q1=((1-t)*p1[0]+t*e[0],(1-t)*p1[1]+t*e[1])
            out.append(((1-t)*q0[0]+t*q1[0],(1-t)*q0[1]+t*q1[1]))
    return out
def rect(x,y,w,h):return [(x,y),(x+w,y),(x+w,y+h),(x,y+h)]
def circ(cx,cy,r,n=20):return [(cx+r*math.cos(2*math.pi*k/n),cy+r*math.sin(2*math.pi*k/n)) for k in range(n)]
def area(p):return sum(p[i][0]*p[(i+1)%len(p)][1]-p[(i+1)%len(p)][0]*p[i][1] for i in range(len(p)))/2
class Model:
    def __init__(s):s.parts=[]
    # Profil in Seitenansicht (x,y), extrudiert entlang z
    def prism(s,prof,col,z0,z1,r=0,emit=False,smooth=False,dec=None,hull=True):
        if r:prof=roundpoly(prof,r)
        if area(prof)<0:prof=prof[::-1]
        F=[];n=len(prof)
        F.append(dict(v=[(x,y,z1) for x,y in prof],n=(0,0,1),hard=True))
        F.append(dict(v=[(x,y,z0) for x,y in prof[::-1]],n=(0,0,-1),hard=True))
        for i in range(n):
            (ax,ay),(bx,by)=prof[i],prof[(i+1)%n]
            ex,ey=bx-ax,by-ay;L=math.hypot(ex,ey) or 1
            nx,ny=ey/L,-ex/L  # nach außen fuer positive Flaeche (y unten)
            F.append(dict(v=[(ax,ay,z1),(bx,by,z1),(bx,by,z0),(ax,ay,z0)],n=(-nx,-ny,0) if False else (nx,ny,0),hard=not smooth and not r))
        s.parts.append(dict(F=F,col=col,emit=emit,dec=dec or [],hull=hull))
        return s
    # Zylinder entlang x, Mittelpunkt (y,z)
    def cyl(s,x0,x1,cy,cz,R,col,n=24,dec=None,emit=False):
        ring=[(cy+R*math.sin(2*math.pi*k/n),cz+R*math.cos(2*math.pi*k/n)) for k in range(n)]
        F=[dict(v=[(x1,y,z) for y,z in ring],n=(1,0,0),hard=True),dict(v=[(x0,y,z) for y,z in ring[::-1]],n=(-1,0,0),hard=True)]
        for i in range(n):
            (ay,az),(by,bz)=ring[i],ring[(i+1)%n];my,mz=(ay+by)/2-cy,(az+bz)/2-cz;L=math.hypot(my,mz)
            F.append(dict(v=[(x0,ay,az),(x0,by,bz),(x1,by,bz),(x1,ay,az)],n=(0,my/L,mz/L),hard=False))
        s.parts.append(dict(F=F,col=col,emit=emit,dec=dec or []))
        return s
    # Aufkleber: plane 'z+'/'z-' (Seiten, Punkte x,y), 'x+' (Muendung, Punkte y,z), 'y-' (oben, Punkte x,z)
    def decal(s,plane,val,pts,col,emit=False,both=True):
        P=s.parts[-1]
        P['dec'].append((plane,val,pts,col,emit))
        if both and plane=='z+':P['dec'].append(('z-',-val,pts,col,emit))
        return s
def tf(p,yaw,pitch):
    x,y,z=p;cy,sy=math.cos(yaw),math.sin(yaw);x1=x*cy+z*sy;z1=-x*sy+z*cy
    cp,sp=math.cos(pitch),math.sin(pitch);y2=y*cp+z1*sp;z2=-y*sp+z1*cp
    return (x1,y2,z2)
LV=(-0.35,-0.8,0.5);_l=math.sqrt(sum(a*a for a in LV));LV=tuple(a/_l for a in LV)
def shadef(col,nv,emit):
    if emit:return col
    d=nv[0]*LV[0]+nv[1]*LV[1]+nv[2]*LV[2]
    f=1.28 if d>0.75 else 1.08 if d>0.45 else 0.88 if d>0.1 else 0.62
    return lum(col,f)
def render(m,yaw,pitch,center):
    yaw=math.radians(yaw);pitch=math.radians(pitch);cx,cy,cz=center
    parts=[];allp=[]
    for P in m.parts:
        polys=[];zs=[]
        for f in P['F']:
            nv=tf(f['n'],yaw,pitch)
            if nv[2]<=1e-4:continue
            v=[tf((a-cx,b-cy,c-cz),yaw,pitch) for a,b,c in f['v']]
            polys.append(('f',v,shadef(P['col'],nv,P['emit']),f['hard']))
        for plane,val,pts,col,emit in P['dec']:
            if plane[0]=='z':
                nn=(0,0,1 if plane=='z+' else -1);v3=[(x,y,val+(0.4 if plane=='z+' else -0.4)) for x,y in pts]
            elif plane=='x+':nn=(1,0,0);v3=[(val+0.4,y,z) for y,z in pts]
            elif plane=='x-':nn=(-1,0,0);v3=[(val-0.4,y,z) for y,z in pts]
            else:nn=(0,-1,0);v3=[(x,val-0.4,z) for x,z in pts]
            nv=tf(nn,yaw,pitch)
            if nv[2]<=1e-4:continue
            v=[tf((a-cx,b-cy,c-cz),yaw,pitch) for a,b,c in v3]
            polys.append(('d',v,col if emit else shadef(col,nv,False),True))
        if not polys:continue
        pts=[p for _,v,_,_ in polys for p in v];allp+=pts
        wv=[q for f in P['F'] for q in f['v']]
        bc=tuple((min(q[i] for q in wv)+max(q[i] for q in wv))/2 for i in range(3))
        depth=tf((bc[0]-cx,bc[1]-cy,bc[2]-cz),yaw,pitch)[2]+P.get('bias',0)
        parts.append((depth,polys,P))
    parts.sort(key=lambda t:t[0])
    return parts,allp
def hull(pts):
    pts=sorted(set((round(x,2),round(y,2)) for x,y in pts))
    if len(pts)<3:return pts
    def cr(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lo=[];up=[]
    for p in pts:
        while len(lo)>=2 and cr(lo[-2],lo[-1],p)<=0:lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up)>=2 and cr(up[-2],up[-1],p)<=0:up.pop()
        up.append(p)
    return lo[:-1]+up[:-1]
def svgview(m,yaw,pitch,center,W,H,scale,pad=0,ow=3.0,origin=None,texture=None,shadow=True,image=True):
    import raster
    return raster.rasterview(m,yaw,pitch,center,W,H,scale,pad,ow,origin=origin,texture=texture,shadow=shadow,image=image)
def svgview_vec(m,yaw,pitch,center,W,H,scale,pad=0,ow=3.0):
    parts,allp=render(m,yaw,pitch,center)
    xs=[p[0] for p in allp];ys=[p[1] for p in allp]
    mx=(min(xs)+max(xs))/2;my=(min(ys)+max(ys))/2
    T=lambda p:'%.1f,%.1f'%((p[0]-mx)*scale+W/2,(p[1]-my)*scale+H/2+pad)
    o=[]
    sh_y=(max(ys)-my)*scale+H/2+pad+14
    o.append(f'<ellipse cx="{W/2}" cy="{sh_y:.0f}" rx="{(max(xs)-min(xs))*scale*0.45:.0f}" ry="{max(8,14*scale):.0f}" fill="#000" opacity="0.32"/>')
    for d,polys,P in parts:
        g=[]
        for k,v,c,hard in polys:
            pts=' '.join(T(p) for p in v)
            if k=='d':g.append(f'<polygon points="{pts}" fill="{c}" stroke="{OL}" stroke-width="{ow*0.55:.1f}" stroke-linejoin="round"/>')
            elif hard:g.append(f'<polygon points="{pts}" fill="{c}" stroke="{OL}" stroke-width="{ow*0.6:.1f}" stroke-linejoin="round"/>')
            elif not P.get('hull',True):g.append(f'<polygon points="{pts}" fill="{c}" stroke="{OL}" stroke-width="{ow*0.6:.1f}" stroke-linejoin="round"/>')
            else:g.append(f'<polygon points="{pts}" fill="{c}" stroke="{c}" stroke-width="1" stroke-linejoin="round"/>')
        hp=hull([p[:2] for kk,v,_c,k2 in polys if kk!='d' for p in v])
        if P.get('hull',True) and not P.get('nohull'):g.append(f'<polygon points="{" ".join(T(p) for p in hp)}" fill="none" stroke="{OL}" stroke-width="{ow:.1f}" stroke-linejoin="round"/>')
        if P['emit'] and P.get('hull',True):o.append(f'<polygon points="{" ".join(T(p) for p in hp)}" fill="{P["col"]}" filter="url(#gl)" opacity="0.35"/>')
        o.append('<g>'+''.join(g)+'</g>')
    return '\n'.join(o)
def extent(m,yaw,pitch,center):
    _,allp=render(m,yaw,pitch,center);xs=[p[0] for p in allp];ys=[p[1] for p in allp]
    return max(xs)-min(xs),max(ys)-min(ys)

def label(m,name):
    m.parts[-1]['label']=name;return m

# Cube-Escape-Farbkanäle (Docs/EQUIPMENT.md › Farbkanäle). Ein ausdrücklicher Kanal gilt nur für den Export
# (spec.json); das Blatt (Zeichnung, recolor) liest ihn nicht. Ohne Angabe ordnet xlroles.assign_channels() per Heuristik zu.
CHANNELS=('MT_Primary','MT_Secondary','MT_Accent','MT_Metal','MT_Energy','MT_Emission','MT_Detail')
def channel(m,ch):
    """ordnet das zuletzt angelegte Teil ausdrücklich einem Kanal zu"""
    assert ch in CHANNELS,ch
    m.parts[-1]['channel']=ch;return m
def copy_channels(m,entries):
    """übernimmt 'ch' (Teil) und 'dch' (alle Aufkleber des Teils, claude-0.15.2) aus Bau-Einträgen (fgen-ITEMS, flib-Spec; gleiche
    Reihenfolge wie m.parts)"""
    assert len(m.parts)==len(entries),(len(m.parts),len(entries))
    for P,e in zip(m.parts,entries):
        if e.get('ch'):assert e['ch'] in CHANNELS,e['ch'];P['channel']=e['ch']
        if e.get('dch'):assert e['dch'] in CHANNELS,e['dch'];P['dec_channel']=e['dch']
    return m
def model_origin(m,yaw,pitch,center):
    """Projektion des Bounding-Box-Mittelpunkts aller Teile (gemeinsamer Bezugspunkt)."""
    vs=[q for P in m.parts for f in P['F'] for q in f['v']]
    bc=[(min(q[i] for q in vs)+max(q[i] for q in vs))/2 for i in range(3)]
    yw,pt=math.radians(yaw),math.radians(pitch)
    p=tf((bc[0]-center[0],bc[1]-center[1],bc[2]-center[2]),yw,pt)
    hw=max(abs(tf((q[0]-center[0],q[1]-center[1],q[2]-center[2]),yw,pt)[0]-p[0]) for q in vs)
    hh=max(abs(tf((q[0]-center[0],q[1]-center[1],q[2]-center[2]),yw,pt)[1]-p[1]) for q in vs)
    return (p[0],p[1]),hw,hh

def sight(m):
    """markiert das zuletzt angelegte Teil als Visier-/Optik-Bauteil (wird separat gezeichnet)"""
    m.parts[-1]['sight']=True;return m
def split_sight(m):
    g=Model();s=Model()
    for P in m.parts:(s if P.get('sight') and not P.get('iron') else g).parts.append(P)   # feste Kimme/Korn (iron) bleiben auf der Waffe gezeichnet
    return g,s
