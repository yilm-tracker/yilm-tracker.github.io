# Playoff bracket in columns, left to right: Wild Card (Week 15) with the two bye teams, Semi Finals (Week 16), Final
# (Week 17). Columns are a fixed width and the bracket scrolls sideways on a phone (two rounds on screen). Each team row:
# logo, seed and win chance on top with the points scored at the right; the name underneath with the projection (live
# once the week starts) at the right. Elbow lines join each game to the next round; the winners' path is lit.
# Same call as po_radial.build, plus av (team -> logo class or '') and live (team, week) -> (points, projection, started).
def build(S,GAMES,win,winp,PT,SHORT,seed,e,tone,final=None,av=lambda t:'',live=None):
    G={k:(w,pair) for k,w,pair,_ in GAMES}
    CG=18                                # gap between columns (px); column width --cw = half the visible width (two rounds on screen)
    HD,TB,GAP,HALF=62,60,14,30           # header height, team row height, gap inside a half, gap between the halves
    MH=2*TB+1
    y=[HD,HD+MH+GAP,HD+2*MH+GAP+HALF,HD+3*MH+2*GAP+HALF]
    c=[v+MH/2 for v in y]
    sfc=[(c[0]+c[1])/2,(c[2]+c[3])/2];fc=(sfc[0]+sfc[1])/2
    H=round(y[3]+MH)
    X=['0px',f'calc(var(--cw) + {CG}px)',f'calc(2*var(--cw) + {2*CG}px)'];CW='var(--cw)'
    box=[];ln=[]
    def team(t,w,won,pct=None,bye=False,played=True):
        a=av(t);lg=f'<i class="av pba {a}" aria-hidden="true"></i>' if a else ''
        if bye:sc,pj='',''
        else:
            pts,prj,started=live(t,w) if live else (PT[(t,w)],None,True)
            sc=f'<b class="pbs{"" if (started or final) else " pbz"}">{pts:.1f}</b>'
            pj=('' if final else f'<span class="pbp" title="{"Live projection" if started else "Projected"}">{prj:.1f}</span>') if prj is not None else ''
        wp=f'<span class="pbwp {"w" if pct>50 else "l" if pct<50 else ""}">{pct}%</span>' if pct is not None else ''
        return (f'<span class="pbt{" pbw" if won else ""}{" pbl" if (played and not won and not bye) else ""}">'
                f'<span class="pbr">{lg}<i class="ch {tone(seed(t))}"><span class="ct">{seed(t)}</span></i>{wp}<span class="pbsp"></span>{sc}</span>'
                f'<span class="pbr2"><span class="bn">{e(SHORT[t])}</span>{pj}</span></span>')
    def match(k,col,top):
        w,(a,b)=G[k];wn=win(a,b,w);pa=None if final else winp(a,b,w)
        box.append(f'<label for="bk-{k}" class="pbm" style="left:{X[col]};top:{top:.1f}px;width:{CW};height:{MH}px">'
                   f'{team(a,w,a==wn,pa)}<i class="pbd"></i>{team(b,w,b==wn,None if pa is None else 100-pa)}</label>')
        return wn
    def bye(t,top):
        box.append(f'<div class="pbm pby" style="left:{X[0]};top:{top:.1f}px;width:{CW};height:{MH}px">'
                   f'{team(t,15,True,bye=True)}<i class="pbd"></i><span class="pbt pbe">Bye</span></div>')
    def elbow(col,ya,yb,on_a,on_b,yn):
        x0=f'calc({X[col]} + var(--cw))';h2=CG/2
        for yy,on,up in ((ya,on_a,True),(yb,on_b,False)):
            t,h=(yy,yn-yy) if up else (yn,yy-yn)
            ln.append(f'<i class="pbc{" on" if on else ""} {"up" if up else "dn"}" style="left:{x0};width:{h2}px;top:{t:.1f}px;height:{h:.1f}px"></i>')
        ln.append(f'<i class="pbc st{" on" if (on_a or on_b) else ""}" style="left:calc({x0[5:-1]} + {h2}px);width:{h2}px;top:{yn-.75:.1f}px;height:0"></i>')
    bye(S[0],y[0]);q2=match('qf2',0,y[1]);bye(S[1],y[2]);q1=match('qf1',0,y[3])
    s1=match('sf1',1,sfc[0]-MH/2);s2=match('sf2',1,sfc[1]-MH/2)
    fw=match('fin',2,fc-MH/2)
    elbow(0,c[0],c[1],s1==S[0],s1==q2,sfc[0]);elbow(0,c[2],c[3],s2==S[1],s2==q1,sfc[1]);elbow(1,sfc[0],sfc[1],fw==s1,fw==s2,fc)
    hd=''.join(f'<span class="pbh" style="left:{X[i]};width:{CW}"><b>{r}</b>Week {wk}</span>' for i,(r,wk) in enumerate((('Wild Card',15),('Semi Finals',16),('Final',17))))
    html=(f'<div class="prd pbx"><div class="pbk" style="height:{H}px">{hd}{"".join(ln)}{"".join(box)}</div></div>'
          '<script>(function(){function fit(){document.querySelectorAll(".pbt .bn").forEach(function(el){if(!el.clientWidth||el.dataset.fw==el.clientWidth)return;'
          'el.dataset.fw=el.clientWidth;el.style.fontSize="";var f=parseFloat(getComputedStyle(el).fontSize),r=document.createRange();r.selectNodeContents(el);'
          'while(r.getBoundingClientRect().width>el.clientWidth-0.5&&f>11){f-=0.5;el.style.fontSize=f+"px"}})}'
          'fit();document.addEventListener("change",function(){requestAnimationFrame(fit)});window.addEventListener("resize",function(){requestAnimationFrame(fit)});'
          'if(document.fonts&&document.fonts.ready)document.fonts.ready.then(function(){document.querySelectorAll(".pbt .bn").forEach(function(el){el.dataset.fw=""});fit()})})()</script>'
          f'<div class="rkey"><span><i class="rk-l"></i>{"winning" if final else "projected"} path</span>'
          f'<span>swipe for the final · tap a game for lineups</span></div>')
    css=('.pbx{width:100%;overflow-x:auto;overflow-y:hidden;-webkit-overflow-scrolling:touch;scroll-snap-type:x proximity;margin:6px 0 0;padding-bottom:4px;scrollbar-width:none}'
         '.pbx::-webkit-scrollbar{display:none}'
         '.pbx{container-type:inline-size}.pbk{position:relative;--cw:max(148px,calc((100cqw - 18px)/2));width:calc(3*var(--cw) + 36px)}'
         '.pbh{position:absolute;top:0;display:flex;flex-direction:column;align-items:center;font-size:11.5px;color:var(--dim);line-height:1.2;scroll-snap-align:start}'
         '.pbh b{font-family:var(--display);font-weight:700;font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:var(--label)}'
         '.pbm{position:absolute;box-sizing:border-box;display:flex;flex-direction:column;border-radius:10px;background:var(--deck-2);'
         'border:1px solid var(--line-strong);overflow:hidden;cursor:pointer;-webkit-tap-highlight-color:transparent}'
         '.pbm.pby{cursor:default;background:var(--deck)}'
         '.pbd{display:block;height:1px;background:var(--hair);flex:none}'
         '.pbt{display:flex;flex-direction:column;justify-content:center;gap:5px;height:60px;padding:0 10px;box-sizing:border-box;min-width:0}'
         '.pbr,.pbr2{display:flex;align-items:center;gap:6px;line-height:1;min-width:0}.pbsp{flex:1}'
         '.pba{display:inline-block;width:24px;height:24px;flex:none;border-radius:50%;background-color:var(--deck-2);background-position:center;background-size:cover;background-repeat:no-repeat;box-shadow:0 0 0 1px var(--hair)}'
         '.pbs{font-family:var(--display);font-weight:700;font-size:17px;font-variant-numeric:tabular-nums;color:var(--steel)}'
         '.pbwp{font-family:var(--display);font-weight:700;font-size:12px;letter-spacing:.03em;color:var(--steel)}.pbwp.w{color:var(--win)}.pbwp.l{color:#ff8a9a}'
         '.pbt .bn{flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:14px;font-weight:500;line-height:1.15;color:var(--steel)}'
         '.pbp{flex:none;font-size:12px;font-weight:500;color:var(--dim);font-variant-numeric:tabular-nums}'
         '.pbw .bn{color:var(--chalk);font-weight:600}.pbw .pbs{color:var(--chalk)}.pbl{opacity:.62}'
         '.pbe{align-items:center;font-family:var(--display);font-weight:700;font-size:13px;letter-spacing:.14em;text-transform:uppercase;color:var(--dim)}'
         '.pbc{position:absolute;box-sizing:border-box;border:0 solid var(--line-strong);pointer-events:none}'
         '.pbc.up{border-top-width:1.5px;border-right-width:1.5px;border-top-right-radius:8px}'
         '.pbc.dn{border-bottom-width:1.5px;border-right-width:1.5px;border-bottom-right-radius:8px}'
         '.rkey{display:flex;justify-content:center;flex-wrap:wrap;gap:4px 14px;margin-top:10px;font-size:11.5px;color:var(--steel)}.rkey span{display:inline-flex;align-items:center;white-space:nowrap}.rk-l{display:inline-block;width:16px;height:1.5px;background:var(--label);margin-right:6px}'
         '.pbc.st{border-top-width:1.5px}.pbc.on{border-color:var(--label);z-index:1}.pbm .pbs.pbz{color:var(--dim);font-weight:600}')
    return html,css,H
