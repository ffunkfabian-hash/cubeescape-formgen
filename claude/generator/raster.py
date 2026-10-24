import math,io,base64,os,contextlib
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from PIL import Image,ImageDraw
WEBP_QUALITY=60   # war 92; Sichtprüfung 17.10.2026 (Blätter sind Release-Asset, Größe zählt)
from scipy import ndimage
import eng
SS=2
# WebP-Kodierung im Hintergrund (claude-0.19): sie ist ~70 % der Blattzeit (Profil KG02: 32,7 von 45,7 s, 21 Bilder, method=6) und
# gibt den GIL frei. Innerhalb von deferred() liefert rasterview einen Platzhalter, die Kodierung läuft in Threads weiter, während
# numpy das nächste Bild rechnet; resolve setzt am Blattende die Bilder ein. Gleiche Parameter, gleiche Bytes.
_POOL=None;_PENDING=None
WEBP_THREADS=int(os.environ.get('CE_WEBP_THREADS') or os.cpu_count() or 4)
def _webp_b64(img):
    buf=io.BytesIO();img.save(buf,'WEBP',quality=WEBP_QUALITY,method=6)
    return base64.b64encode(buf.getvalue()).decode()
def _image_b64(img):
    if _PENDING is None:return _webp_b64(img)
    tok=f'@@webp{len(_PENDING)}@@';_PENDING.append((tok,_POOL.submit(_webp_b64,img)));return tok
@contextlib.contextmanager
def deferred():
    """with raster.deferred() as resolve: page=resolve(baue_blatt()) – Bilder des Blatts parallel kodieren (verschachtelt: äußerer gilt)."""
    global _POOL,_PENDING
    if _PENDING is not None:yield lambda page:page;return
    if _POOL is None:_POOL=ThreadPoolExecutor(WEBP_THREADS,thread_name_prefix='webp')
    _PENDING=[]
    def resolve(page):
        for tok,fu in _PENDING:
            assert page.count(tok)<=1,tok
            page=page.replace(tok,fu.result())
        assert '@@webp' not in page
        return page
    try:yield resolve
    finally:_PENDING=None
def _hex(c):c=c.lstrip('#');return np.array([int(c[i:i+2],16) for i in (0,2,4)],np.float32)
LAST={}
def _glass_pass(glass,rgba,zb,yaw,pitch,center,T,w,h,s,tol):
    """Glas (Visier-Serie, claude-0.6): durchscheinende Scheiben über dem fertigen Bild, nur wo sie vor dem Undurchsichtigen liegen.
    Teile mit P['alpha'] (Deckkraft der Zeichnung) und P['col'] (Tönung); dazu ein weicher Glanzverlauf ohne Linien (seit claude-0.7,
    vorher schräge Schraffur) und eine helle Kante.
    Liefert Anker der Glas-Beschriftungen (Bildpunkte)."""
    parts,_=eng.render(glass,yaw,pitch,center);anch={}
    for d,polys,P in parts:
        gc=_hex(P['col']);a0=float(P.get('alpha',0.34));hit=np.zeros((h,w),bool)
        for kind,v,c,hard in polys:
            pts=[T(p) for p in v];zs=[p[2]*s for p in v]
            x0=max(0,int(min(p[0] for p in pts))-1);x1=min(w,int(max(p[0] for p in pts))+2)
            y0=max(0,int(min(p[1] for p in pts))-1);y1=min(h,int(max(p[1] for p in pts))+2)
            if x1<=x0 or y1<=y0:continue
            im=Image.new('L',(x1-x0,y1-y0),0);ImageDraw.Draw(im).polygon([(px-x0,py-y0) for px,py in pts],fill=255)
            mk=np.asarray(im)>0
            A_=np.array([[px,py,1] for px,py in pts])
            try:coef=np.linalg.lstsq(A_,np.array(zs),rcond=None)[0]
            except Exception:coef=np.array([0,0,np.mean(zs)])
            if abs(coef[0])>50 or abs(coef[1])>50:coef=np.array([0,0,np.mean(zs)])   # fast auf der Kante: wie der undurchsichtige Durchgang
            yy,xx=np.mgrid[y0:y1,x0:x1];Z=coef[0]*(xx+0.5)+coef[1]*(yy+0.5)+coef[2]
            ok=mk&(Z>=zb[y0:y1,x0:x1]-tol)
            if not ok.any():continue
            hit[y0:y1,x0:x1]|=ok
            # dezenter Glanz statt Schraffur (Wunsch des Nutzers 18.10.2026): weicher Verlauf, oben links etwas deckender, keine Linien
            t=np.clip(((xx-x0)+(yy-y0))/max(1.0,0.6*((x1-x0)+(y1-y0))),0.0,1.0)
            a=(a0+0.07*(1.0-t)**2)[ok]
            sub=rgba[y0:y1,x0:x1];A=sub[...,3][ok]/255.0;rgb=sub[...,:3][ok]
            oa=a+A*(1-a);sub[...,:3][ok]=(gc[None,:]*a[:,None]+rgb*(A*(1-a))[:,None])/np.maximum(oa,1e-6)[:,None];sub[...,3][ok]=oa*255
        if hit.any():
            edge=hit&~ndimage.binary_erosion(hit,iterations=max(1,int(SS)))
            rgba[edge,:3]=np.clip(gc*0.35+255*0.65,0,255);rgba[edge,3]=np.maximum(rgba[edge,3],235)
            yy,xx=np.nonzero(hit);cx,cy=xx.mean(),yy.mean();k=np.argmin((xx-cx)**2+(yy-cy)**2)
            if P.get('label'):anch.setdefault(P['label'],(xx[k]/SS,yy[k]/SS))
    return anch
def rasterview(m,yaw,pitch,center,W,H,scale,pad=0,ow=3.0,origin=None,texture=None,shadow=True,glass=None,image=True):
    """image=False: nur raster.LAST (Anker, Boxen, Ursprung) rechnen, kein Bild (Vorlauf in xl.detail_view, claude-0.19)."""
    parts,allp=eng.render(m,yaw,pitch,center)
    xs=[p[0] for p in allp];ys=[p[1] for p in allp]
    mx=(min(xs)+max(xs))/2;my=(min(ys)+max(ys))/2
    if origin is not None:mx,my=origin
    w,h=W*SS,H*SS;s=scale*SS
    def T(p):return ((p[0]-mx)*s+w/2,(p[1]-my)*s+h/2+pad*SS)
    zb=np.full((h,w),-1e9,np.float32);idb=np.full((h,w),-1,np.int32);pb=np.full((h,w),-1,np.int32)
    col=np.zeros((h,w,3),np.float32);emit=np.zeros((h,w),bool);decm=np.zeros((h,w),bool);nrmb=np.zeros((h,w,3),np.float32)
    gid=0;tol=0.08*s  # Gleichstand: spaeter gezeichnetes Teil gewinnt
    for pi,(d,polys,P) in enumerate(parts):
        smooth_id=None
        for kind,v,c,hard in polys:
            pts=[T(p) for p in v];zs=[p[2]*s for p in v]
            x0=max(0,int(min(p[0] for p in pts))-1);x1=min(w,int(max(p[0] for p in pts))+2)
            y0=max(0,int(min(p[1] for p in pts))-1);y1=min(h,int(max(p[1] for p in pts))+2)
            if x1<=x0 or y1<=y0:continue
            im=Image.new('L',(x1-x0,y1-y0),0)
            ImageDraw.Draw(im).polygon([(px-x0,py-y0) for px,py in pts],fill=255)
            mk=np.asarray(im)>0
            if not mk.any():continue
            A=np.array([[px,py,1] for px,py in pts]);zz=np.array(zs)
            try:coef=np.linalg.lstsq(A,zz,rcond=None)[0]
            except Exception:coef=np.array([0,0,np.mean(zz)])
            if abs(coef[0])>50 or abs(coef[1])>50:coef=np.array([0,0,np.mean(zz)])
            yy,xx=np.mgrid[y0:y1,x0:x1];Z=(coef[0]*(xx+0.5)+coef[1]*(yy+0.5)+coef[2]).astype(np.float32)
            sub=zb[y0:y1,x0:x1];sid=idb[y0:y1,x0:x1];spb=pb[y0:y1,x0:x1]
            if kind=='d':
                ok=mk&((Z>sub+tol)|((spb==pi)&(Z>sub-3*s)))
                gid+=1;fid=gid
            else:
                ok=mk&(Z>=sub-tol)
                if hard:gid+=1;fid=gid
                else:
                    if smooth_id is None:gid+=1;smooth_id=gid
                    fid=smooth_id
            sub[ok]=np.maximum(Z[ok],sub[ok]) if kind=='d' else Z[ok]
            sid[ok]=fid;spb[ok]=pi;decm[y0:y1,x0:x1][ok]=(kind=='d')
            if texture is not None:
                a_,b_,c_=np.array(v[0]),np.array(v[1]),np.array(v[2]);nn_=np.cross(b_-a_,c_-a_);ln=np.linalg.norm(nn_)
                if ln>1e-9:nrmb[y0:y1,x0:x1][ok]=nn_/ln
            col[y0:y1,x0:x1][ok]=_hex(c)
            em=emit[y0:y1,x0:x1];em[ok]=bool(P['emit'] or (kind=='d' and c.upper() in ()))
    fg=idb>=0
    if texture is not None:
        yw,pt=math.radians(yaw),math.radians(pitch);cyy,syy=math.cos(yw),math.sin(yw);cpp,spp=math.cos(pt),math.sin(pt)
        # nur im Rahmen der Waffe rechnen (Speicher: Isometrie 5400×3600 Bildpunkte)
        rws=np.nonzero(fg.any(1))[0];cls=np.nonzero(fg.any(0))[0]
        if len(rws):
            r0,r1=max(0,rws[0]-2),min(h,rws[-1]+3);c0,c1=max(0,cls[0]-2),min(w,cls[-1]+3);sl=(slice(r0,r1),slice(c0,c1))
            yy_,xx_=np.mgrid[r0:r1,c0:c1].astype(np.float32)
            X2=(xx_+0.5-w/2)/s+mx;Y2=(yy_+0.5-h/2-pad*SS)/s+my;Z2=zb[sl]/s
            def inv(X2,Y2,Z2):
                Y=Y2*cpp-Z2*spp;Z1=Y2*spp+Z2*cpp;X=X2*cyy-Z1*syy;Z=X2*syy+Z1*cyy;return X,Y,Z
            WX,WY,WZ=inv(X2,Y2,Z2);WX=WX+center[0];WY=WY+center[1];WZ=WZ+center[2]
            del X2,Y2,Z2,yy_,xx_
            nb=nrmb[sl];NX,NY,NZ=inv(nb[...,0],nb[...,1],nb[...,2])
            kw={'scale':s} if getattr(texture,'wants_scale',False) else {}
            col[sl]=texture(col[sl],pb[sl],idb[sl],decm[sl],[P for _,_,P in parts],SS,world=(WX,WY,WZ),nrm=(NX,NY,NZ),**kw)
    # Konturen: Grenzen zwischen Flaechen-IDs, Silhouette dicker
    e=np.zeros_like(fg);sil=np.zeros_like(fg)
    for dy in (-1,0,1):
        for dx in (-1,0,1):
            if dy==0 and dx==0:continue
            b=np.roll(np.roll(idb,dy,0),dx,1)
            e|=idb!=b
            sil|=(idb<0)^(b<0)
    inner=e&~sil
    ri=max(1,int(round(ow*0.8*SS/2)));rs=max(1,int(round(ow*1.25*SS/2)))
    inner=ndimage.binary_dilation(inner,iterations=ri-1) if ri>1 else inner
    silm=ndimage.binary_dilation(sil,iterations=rs) & ~fg | (ndimage.binary_dilation(sil,iterations=max(1,rs-1))&fg)
    line=(inner&fg)|silm
    rgba=np.zeros((h,w,4),np.float32)
    # Glow hinter emittierenden Flaechen
    if emit.any():
        g=np.zeros((h,w,3),np.float32);g[emit]=col[emit]
        a=ndimage.gaussian_filter(emit.astype(np.float32),4*SS)*0.3
        for k in range(3):g[...,k]=ndimage.gaussian_filter(g[...,k],4*SS)
        gn=np.where(a[...,None]>1e-4,g/np.maximum(ndimage.gaussian_filter(emit.astype(np.float32),4*SS),1e-4)[...,None],0)
        rgba[...,:3]=gn;rgba[...,3]=np.clip(a,0,0.3)*255
    rgba[fg,:3]=col[fg];rgba[fg,3]=255
    rgba[line,:3]=_hex(eng.OL);rgba[line,3]=255
    ganch=_glass_pass(glass,rgba,zb,yaw,pitch,center,T,w,h,s,tol) if glass is not None else {}
    anchors={};boxes={}
    labs={}
    for pi,(d,polys,P) in enumerate(parts):
        if P.get('label'):labs.setdefault(P['label'],[]).append(pi)
    for lb,pis in labs.items():
        vis=np.isin(pb,pis)
        rws=np.flatnonzero(vis.any(1))
        if not len(rws):continue   # nicht sichtbar: keine Box, kein Anker
        cls=np.flatnonzero(vis.any(0))
        boxes[lb]=(cls[0]/SS,rws[0]/SS,(cls[-1]+1)/SS,(rws[-1]+1)/SS)   # sichtbare Pixel-Box je Bauteil (Bildpunkte, ohne SS)
        # Anker nur im Rahmen des Bauteils rechnen (claude-0.19): Rand 4 > 3 Erosionsschritte, außerhalb ist vis leer – gleiche Pixel wie im ganzen Bild
        r0,c0=max(0,rws[0]-4),max(0,cls[0]-4);sl=(slice(r0,rws[-1]+5),slice(c0,cls[-1]+5))
        mk=vis[sl]&~line[sl]
        mk2=mk&~decm[sl]
        if mk2.sum()>=20*SS*SS:
            er=ndimage.binary_erosion(mk2,iterations=3);mk=er if er.sum()>0 else mk2
        if mk.sum()<20*SS*SS:continue
        yy,xx=np.nonzero(mk);yy=yy+r0;xx=xx+c0;cxm,cym=xx.mean(),yy.mean()
        k=np.argmin((xx-cxm)**2+(yy-cym)**2)
        anchors[lb]=(xx[k]/SS,yy[k]/SS)
    anchors.update(ganch)
    LAST.clear();LAST.update(anchors=anchors,boxes=boxes,origin=(mx,my))
    if not image:return ''
    img=Image.fromarray(np.clip(rgba,0,255).astype(np.uint8),'RGBA').resize((W,H),Image.LANCZOS)
    b64=_image_b64(img)
    sh_y=(max(ys)-my)*scale+H/2+pad+14
    shd=f'<ellipse cx="{W/2}" cy="{sh_y:.0f}" rx="{(max(xs)-min(xs))*scale*0.45:.0f}" ry="{max(8,14*scale):.0f}" fill="#000" opacity="0.32"/>' if shadow else ''
    return shd+f'<image x="0" y="0" width="{W}" height="{H}" href="data:image/webp;base64,{b64}"/>'
