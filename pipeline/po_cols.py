# Playoff bracket in columns, left to right: Wild Card (Week 15) with the two bye teams, Semi Finals (Week 16), Final
# (Week 17). Each game is a box of two team rows (seed and points on top, name underneath), joined to the next round by
# elbow lines; the line from each game's winner (projected, or actual once played) is lit. Same call as po_radial.build.
def build(S,GAMES,win,winp,PT,SHORT,seed,e,tone,final=None):
    G={k:(w,pair) for k,w,pair,_ in GAMES}
    HD,TB,GAP,HALF=58,40,10,22          # header height, team row height, gap inside a half, gap between the halves
    MH=2*TB+1
    y=[HD,HD+MH+GAP,HD+2*MH+GAP+HALF,HD+3*MH+2*GAP+HALF]
    c=[v+MH/2 for v in y]
    sfc=[(c[0]+c[1])/2,(c[2]+c[3])/2];fc=(sfc[0]+sfc[1])/2
    H=round(y[3]+MH)
    X=[0.0,34.5,69.0];W=31.0;GX=3.5     # column lefts and width (%), gap between columns (%)
    box=[];ln=[]
    def team(t,w,won,bye=False,played=True):
        sc='' if bye else f'<b class="pbs">{PT[(t,w)]:.1f}</b>'
        return (f'<span class="pbt{" pbw" if won else ""}{" pbl" if (played and not won and not bye) else ""}">'
                f'<span class="pbr"><i class="ch {tone(seed(t))}"><span class="ct">{seed(t)}</span></i>{sc}</span>'
                f'<span class="bn">{e(SHORT[t])}</span></span>')
    def match(k,col,top):
        w,(a,b)=G[k];wn=win(a,b,w)
        box.append(f'<label for="bk-{k}" class="pbm" style="left:{X[col]}%;top:{top:.1f}px;width:{W}%;height:{MH}px">'
                   f'{team(a,w,a==wn)}<i class="pbd"></i>{team(b,w,b==wn)}</label>')
        return wn
    def bye(t,top):
        box.append(f'<div class="pbm pby" style="left:{X[0]}%;top:{top:.1f}px;width:{W}%;height:{MH}px">'
                   f'{team(t,15,True,bye=True)}<i class="pbd"></i><span class="pbt pbe">Bye</span></div>')
    def elbow(col,ya,yb,on_a,on_b,yn):
        """lines from two boxes (centres ya, yb) in column col into the next column's box centred on yn"""
        x0=X[col]+W;xm=x0+GX/2
        for yy,on,up in ((ya,on_a,True),(yb,on_b,False)):
            t,h=(yy,yn-yy) if up else (yn,yy-yn)
            ln.append(f'<i class="pbc{" on" if on else ""} {"up" if up else "dn"}" style="left:{x0}%;width:{GX/2}%;top:{t:.1f}px;height:{h:.1f}px"></i>')
        ln.append(f'<i class="pbc st{" on" if (on_a or on_b) else ""}" style="left:{xm}%;width:{GX/2}%;top:{yn-.75:.1f}px;height:0"></i>')
    w15b=[S[0],S[1]]
    bye(S[0],y[0]);q2=match('qf2',0,y[1]);bye(S[1],y[2]);q1=match('qf1',0,y[3])
    s1=match('sf1',1,sfc[0]-MH/2);s2=match('sf2',1,sfc[1]-MH/2)
    fw=match('fin',2,fc-MH/2)
    elbow(0,c[0],c[1],s1==S[0],s1==q2,sfc[0]);elbow(0,c[2],c[3],s2==S[1],s2==q1,sfc[1]);elbow(1,sfc[0],sfc[1],fw==s1,fw==s2,fc)
    hd=''.join(f'<span class="pbh" style="left:{X[i]}%;width:{W}%"><b>{r}</b>Wk {wk}</span>' for i,(r,wk) in enumerate((('Wild Card',15),('Semi Finals',16),('Final',17))))
    html=(f'<div class="prd pbk" style="height:{H}px">{hd}{"".join(ln)}{"".join(box)}</div>'
          '<script>(function(){function fit(){document.querySelectorAll(".pbt .bn").forEach(function(el){if(!el.clientWidth||el.dataset.fw==el.clientWidth)return;'
          'el.dataset.fw=el.clientWidth;el.style.fontSize="";var f=parseFloat(getComputedStyle(el).fontSize),r=document.createRange();r.selectNodeContents(el);'
          'while(r.getBoundingClientRect().width>el.clientWidth-0.5&&f>9.5){f-=0.5;el.style.fontSize=f+"px"}})}'
          'fit();document.addEventListener("change",function(){requestAnimationFrame(fit)});window.addEventListener("resize",function(){requestAnimationFrame(fit)});'
          'if(document.fonts&&document.fonts.ready)document.fonts.ready.then(function(){document.querySelectorAll(".pbt .bn").forEach(function(el){el.dataset.fw=""});fit()})})()</script>'
          f'<div class="rkey"><span><i class="rk-l"></i>{"winning" if final else "projected"} path</span><span>{"final scores" if final else "projected points · tap a game for details"}</span></div>')
    css=('.pbk{position:relative;width:100%;margin:6px 0 0}'
         '.pbh{position:absolute;top:0;display:flex;flex-direction:column;align-items:center;font-size:11px;color:var(--dim);line-height:1.15}'
         '.pbh b{font-family:var(--display);font-weight:700;font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--label)}'
         '.pbm{position:absolute;box-sizing:border-box;display:flex;flex-direction:column;border-radius:9px;background:var(--deck-2);'
         'border:1px solid var(--line-strong);overflow:hidden;cursor:pointer;-webkit-tap-highlight-color:transparent}'
         '.pbm.pby{cursor:default;background:var(--deck)}'
         '.pbd{display:block;height:1px;background:var(--hair);flex:none}'
         '.pbt{display:flex;flex-direction:column;justify-content:center;gap:3px;height:40px;padding:0 7px;box-sizing:border-box;min-width:0}'
         '.pbr{display:flex;align-items:center;justify-content:space-between;line-height:1}'
         '.pbr .ch{transform:scale(.92);transform-origin:left center}'
         '.pbs{font-family:var(--display);font-weight:600;font-size:13px;font-variant-numeric:tabular-nums;color:var(--steel)}'
         '.pbt .bn{display:block;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12.5px;font-weight:500;line-height:1.1;color:var(--steel)}'
         '.pbw .bn{color:var(--chalk);font-weight:600}.pbw .pbs{color:var(--chalk)}.pbl{opacity:.62}'
         '.pbe{align-items:center;font-family:var(--display);font-weight:700;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--dim)}'
         '.pbc{position:absolute;box-sizing:border-box;border:0 solid var(--line-strong);pointer-events:none}'
         '.pbc.up{border-top-width:1.5px;border-right-width:1.5px;border-top-right-radius:7px}'
         '.pbc.dn{border-bottom-width:1.5px;border-right-width:1.5px;border-bottom-right-radius:7px}'
         '.pbc.st{border-top-width:1.5px}.pbc.on{border-color:var(--label);z-index:1}')
    return html,css,H
