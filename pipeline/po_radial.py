# Radial playoff bracket: seed-1 half on the left, seed-2 half on the right, meeting at the championship in the centre.
# Quarterfinal teams sit on the outer ring; bye teams start one ring in (already in the semifinal).
import math
def build(S,GAMES,win,winp,PT,SHORT,seed,e,tone,final=None):
    # final(a,b,w) -> text for a played game's circle (the margin); None while the games are projected
    W=312.0
    RO,RQ,RS=0.40*W,0.27*W,0.17*W
    KY=1.0  # no vertical stretch (rings stay circular): room above/below each round for its label
    ROT=90  # whole bracket turned 90 deg anticlockwise: byes on the right, seeds 5/6 on the left, semifinals top and bottom
    rt=lambda a:(a+ROT)%360
    up=lambda a:math.sin(math.radians(rt(a)))>1e-9
    # extents from the team nodes (outer ring for QF teams, middle ring for byes); labels add ~40 above/below, ~52 sideways
    NODES=[(a,RO) for a in (165,99,15,81)]+[(245,RQ),(295,RQ)]
    xs=[r_*math.cos(math.radians(rt(a))) for a,r_ in NODES];ys=[KY*r_*math.sin(math.radians(rt(a))) for a,r_ in NODES]
    LAB,LABV=54.0,44.0
    CX=(W-(max(xs)+LAB)-(-min(xs)+LAB))/2+(-min(xs)+LAB)
    CY=max(ys)+LABV
    H=round(CY+(-min(ys))+LABV+4)
    def pol(a,r,cy):a=rt(a);return CX+r*math.cos(math.radians(a)),cy-KY*r*math.sin(math.radians(a))
    (q1,q2,s1,s2,fn)=[g[2] for g in GAMES]
    # left half: 4 at 160, 5 at 120 (QF qf2), seed 1 bye at 220; right half mirrored: 3 at 20, 6 at 60 (qf1), seed 2 at 320
    L=dict(qf='qf2',sf='sf1',pair=q2,angs=(165,99),qa=140,bye=S[0],ba=245,sa=180)
    R=dict(qf='qf1',sf='sf2',pair=q1,angs=(15,81),qa=40,bye=S[1],ba=295,sa=0)
    wk={'qf1':15,'qf2':15,'sf1':16,'sf2':16,'fin':17}
    paths=[];nodes=[];btns=[]
    def arc(r,a1,a2,cls):
        x1,y1=pol(a1,r,CY);x2,y2=pol(a2,r,CY);d=(a2-a1+180)%360-180;big=0;sw=0 if d>0 else 1
        paths.append(f'<path class="{cls}" d="M{x1:.2f} {y1:.2f}A{r:.2f} {KY*r:.2f} 0 {big} {sw} {x2:.2f} {y2:.2f}"/>')
    def spoke(a,r1,r2,cls):
        x1,y1=pol(a,r1,CY);x2,y2=pol(a,r2,CY);paths.append(f'<path class="{cls}" d="M{x1:.2f} {y1:.2f}L{x2:.2f} {y2:.2f}"/>')
    pos=lambda x,y:f'left:{x/W*100:.3f}%;top:{y/H*100:.3f}%'
    def team(t,a,r,w,winner,bye=False,above=False):
        x,y=pol(a,r,CY);sd=seed(t)
        sc='Bye' if bye else f'{PT[(t,w)]:.1f}'
        nodes.append(f'<span class="prn s-{(tone(sd).split() or ["n"])[0]}{" prw" if winner else ""}{" prby" if bye else ""}" style="{pos(x,y)}"><i>{sd}</i>'
                     f'<span class="prl{" up" if above else ""}{" lng" if len(SHORT[t])>16 and x<CX else ""}"><b>{e(SHORT[t])}</b><em>{sc}</em></span></span>')
    def btn(k,a,r,cls=''):
        x,y=pol(a,r,CY) if r else (CX,CY);a_,b_=dict((g[0],g[2]) for g in GAMES)[k];w=wk[k];wn=win(a_,b_,w);p=winp(wn,b_ if wn==a_ else a_,w)
        lab={'qf1':'Wild<br>Card','qf2':'Wild<br>Card','sf1':'Semi<br>Final','sf2':'Semi<br>Final','fin':'Final'}[k]
        # round label sits outside the circle: radially outward for QF/SF (between the two incoming lines), left of the final
        # round label outside the circle, its near edge a fixed gap away: left of the final, above / below the other rounds
        if k.startswith('qf'):  # diagonal, radially outward (between the two incoming lines), near edge 5px off the circle
            oa=math.radians(rt(a));d_=17+5;ex,ey=math.cos(oa),-math.sin(oa)
            st=f'left:calc(50% + {ex*d_:.1f}px);top:calc(50% + {ey*d_:.1f}px);transform:translate({-50+50*ex/max(abs(ex),abs(ey)):.0f}%,{-50+50*ey/max(abs(ex),abs(ey)):.0f}%)'
        else:
          st=('left:-10px;top:50%;transform:translate(-100%,-50%)' if not r else
              'left:50%;top:-5px;transform:translate(-50%,-100%)' if y<CY else 'left:50%;top:calc(100% + 5px);transform:translate(-50%,0)')
        btns.append(f'<label for="bk-{k}" class="prg{cls}{" fin" if final else ""}" style="{pos(x,y)}"><b>{final(a_,b_,w) if final else str(p)+"%"}</b><small style="{st}">{lab}</small></label>')
    for side in (L,R):
        a,b=side['pair'];wn=win(a,b,15)
        for t,ang in zip(side['pair'],side['angs']):
            cl='rp on' if t==wn else 'rp'
            spoke(ang,RO,RQ,cl);arc(RQ,ang,side['qa'],cl)
            team(t,ang,RO,15,t==wn,above=up(ang))
        sfa,sfb=dict((g[0],g[2]) for g in GAMES)[side['sf']];swn=win(sfa,sfb,16)
        # QF winner path into the semifinal, and the bye team's path
        cl='rp on' if wn==swn else 'rp';spoke(side['qa'],RQ,RS,cl);arc(RS,side['qa'],side['sa'],cl)
        cl='rp on' if side['bye']==swn else 'rp';spoke(side['ba'],RQ,RS,cl);arc(RS,side['ba'],side['sa'],cl)
        team(side['bye'],side['ba'],RQ,16,side['bye']==swn,bye=True,above=up(side['ba']))
        fa,fb=fn;fw=win(fa,fb,17)
        spoke(side['sa'],RS,0,'rp on' if swn==fw else 'rp')
        btn(side['qf'],side['qa'],RQ);btn(side['sf'],side['sa'],RS)
    btn('fin',0,0,' rf')
    svg=f'<svg viewBox="0 0 {W:.0f} {H}" aria-hidden="true">'+''.join(sorted(paths,key=lambda p:' on' in p))+'</svg>'
    html=f'<div class="prd" style="aspect-ratio:{W:.0f}/{H}">'+svg+''.join(nodes)+''.join(btns)+f'</div><div class="rkey"><span><b>Wild Card</b> Wk 15</span><span><b>Semi Final</b> Wk 16</span><span><b>Final</b> Wk 17</span><span><i class="rk-l"></i>{"winning" if final else "projected"} path</span></div>'
    css=('.prd{position:relative;width:100%;max-width:440px;margin:6px auto 0;container-type:inline-size}'
         '.prd svg{position:absolute;inset:0;width:100%;height:100%;overflow:visible}'
         '.prd path{fill:none;stroke:var(--line-strong);stroke-width:1.5;vector-effect:non-scaling-stroke;stroke-linecap:round}'
         '.prd path.on{stroke:var(--steel)}'
         '.prd .prn,.prd .prg{position:absolute;transform:translate(-50%,-50%)}'
         '.prd .prn>i{display:flex;align-items:center;justify-content:center;width:34px;height:34px;border-radius:50%;box-sizing:border-box;font-style:normal;'
         'font-family:var(--display);font-weight:700;font-size:17px;line-height:1;padding-top:1px;background:var(--deck-2);border:1.5px solid var(--line-strong);color:var(--steel)}'
         '.prd .prn.s-gold>i{color:#f4c451;border-color:rgba(244,196,81,.55);background:#221f19}.prd .prn.s-g>i{color:var(--win);border-color:rgba(63,214,155,.45);background:#17241f}'
         '.prd .prn.prby>i{box-shadow:0 0 0 3px var(--deck),0 0 0 4.5px var(--line-strong)}'
         '.prd .prl{position:absolute;left:50%;top:calc(100% + 4px);transform:translateX(-50%);display:flex;flex-direction:column;align-items:center;white-space:nowrap;line-height:1.15}'
         '.prd .prl.up{top:auto;bottom:calc(100% + 4px)}.prd .prby .prl{top:calc(100% + 7px)}.prd .prby .prl.up{top:auto;bottom:calc(100% + 7px)}'
         '.prd .prl b,.prd .prl em{white-space:nowrap!important}'
         '.prd .prl.lng b{white-space:normal!important;width:7.6em;text-align:center;text-wrap:balance}'
         '.prd .prl b{font-size:12.5px;font-weight:500;color:var(--steel)}.prd .prw .prl b{color:var(--chalk)}'
         '.prd .prl em{font-style:normal;font-family:var(--display);font-weight:600;font-size:13px;color:var(--steel);letter-spacing:.02em}.prd .prby .prl em{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--dim)}'
         '.prd .prg{display:flex;flex-direction:column;align-items:center;justify-content:center;width:34px;height:34px;border-radius:50%;box-sizing:border-box;cursor:pointer;'
         'background:var(--deck);border:1.5px solid var(--line-strong);line-height:1}'
         '.prd .prg small{position:absolute;transform:translate(-50%,-50%);font-family:var(--display);font-weight:700;font-size:11.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--chalk);white-space:nowrap;line-height:1;text-align:center;pointer-events:none}'
         '.prd .prg b{font-family:var(--display);font-weight:700;font-size:13px;color:var(--label);font-variant-numeric:tabular-nums;padding-top:1px}'
         '.rkey{display:flex;justify-content:center;flex-wrap:wrap;gap:4px 14px;margin-top:8px;font-size:11.5px;color:var(--steel)}.rkey b{font-family:var(--display);font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--label);margin-right:3px}'
         '.rkey span{display:inline-flex;align-items:center;white-space:nowrap}.rk-l{display:inline-block;width:16px;height:1.5px;background:var(--steel);margin-right:6px}'
         '.prd .prg.rf{width:58px;height:58px}.prd .prg.rf small{font-size:14px}.prd .prg.rf b{font-size:19px}.prd .prg.fin b{font-size:11.5px;letter-spacing:0}.prd .prg.rf.fin b{font-size:16px}')
    return html,css,H
