// In-page live scores for the Matchups tab (live site only; the download file has no script).
// While the current week has games on, the page asks Sleeper directly (it allows any origin) and patches the
// lineup rows in place: player points, FINAL / LIVE tile, game status, stat line, each team's points total, its live
// projection (the small figure under it) and the "Needs over proj" line, slate by slate (2026-11-13).
// Polling: every 60 s while a game is in progress and the page is visible; every 10 min otherwise.
// The site rebuild still recomputes everything else (slate status, slate and running totals, optimal lineups, odds).
// On-demand tabs (2026-11-04): the current week's lineups are on the page only while Matchups is open on that week
// (lazy.js builds it from its chunk and drops it after leaving). Polling runs while they are on the page; each time the
// week is built again the last scores are put back at once, and a fresh poll follows if they are over 55 s old.
(function(){
  if(!window.fetch)return;
  var box,cells,W=0,L='1335450123487961088',Y='2026',A='https://api.sleeper.app/v1',S='https://api.sleeper.com';
  var last=0,lastStats=0,stats={},timer=null,on=false,data=null,shown=null;
  function setup(){box=document.getElementById('mlive');if(!box){rel();return false}W=+box.dataset.w;cells=document.querySelectorAll('.cv[data-p]');if(!cells.length){rel();return false}return true}
  // drop the references after each use: a Matchups week left on the page by nothing but these variables stayed in memory after
  // the tab was dropped (2026-11-05 heap snapshot); setup() finds them again on the next poll
  function rel(){box=null;cells=null}
  function get(u){return fetch(u,{cache:'no-store'}).then(function(r){if(!r.ok)throw r.status;return r.json()})}
  function f1(x){return r1(x).toFixed(1)}
  function grp(lab,nums){return '<span class="sit"><u>'+lab+'</u> '+nums.map(function(n){return typeof n==='number'&&n<0?'(−'+(-n)+')':String(n)}).join('-')+'</span>'}
  function statline(pos,s){  // same compact format as the build (statline.py)
    if(!s)return '';var g=function(k){return Math.round(s[k]||0)},o=[],td=function(c,y,t){return t?[c,y,t]:[c,y]};
    if(pos==='QB'){var pa=[g('pass_yd')];if(g('pass_int'))pa.push(g('pass_td'),g('pass_int'));else if(g('pass_td'))pa.push(g('pass_td'));o.push(grp('PA',pa));if(g('rush_att'))o.push(grp('RU',td(g('rush_att'),g('rush_yd'),g('rush_td'))))}
    else if(pos==='RB'){if(g('rush_att'))o.push(grp('RU',td(g('rush_att'),g('rush_yd'),g('rush_td'))));if(g('rec'))o.push(grp('REC',td(g('rec'),g('rec_yd'),g('rec_td'))));if(!o.length)o.push(grp('RU',[0,0]))}
    else if(pos==='WR'||pos==='TE'){if(g('rec')||g('rec_tgt'))o.push(grp('REC',td(g('rec'),g('rec_yd'),g('rec_td'))));if(g('rush_att'))o.push(grp('RU',td(g('rush_att'),g('rush_yd'),g('rush_td'))));if(!o.length)o.push(grp('REC',[0,0]))}
    else if(pos==='K'){o.push(grp('FG',[g('fgm')+'/'+g('fga')]),grp('XP',[g('xpm')+'/'+g('xpa')]))}
    else if(pos==='DEF'){o.push(grp('SK',[g('sack')]),grp('TO',[g('int')+g('fum_rec')]));if(g('def_td'))o.push(grp('TD',[g('def_td')]));o.push(grp('PA',[g('pts_allow')]))}
    return o.join('<i class="sdt">•</i>');
  }
  // 2026-11-13: each lineup's live projection (the Points band's small figure .llv) and "Needs over proj" (slate by slate,
  // as mu_build sview: finished = frozen gap, current = gap between the two .llv, later = empty), by the build's formula (mu_build _lx):
  // finished = points, in progress = points + projection x share of the game left (game clock, as sleeper.mjs pullLive),
  // not started = projection; no game, or a team the feed does not list = the build's own value (data-x)
  function lx(el,st,pp,lf){
    var x=+el.dataset.x||0,pid=el.dataset.p,cn=el.previousElementSibling;
    while(cn&&!cn.classList.contains('cn'))cn=cn.previousElementSibling;
    var g=pid&&cn&&cn.querySelector('.gp[data-t]'),t=g?g.dataset.t:null,s=t&&st[t],j=+el.dataset.j;
    if(!pid)return [x,false,false];                              // no game this week: never finished, nothing left to play
    if(s==='post')return [pp[pid]||0,true,false];
    if(s==='in')return [(pp[pid]||0)+j*(lf[t]!==undefined?lf[t]:0.5),false,true];
    if(s==='pre')return [j,false,true];
    var f=(el.querySelector('small')||{}).textContent==='FINAL';return [x,f,!f];
  }
  function r1(x){var v=Math.round(Math.abs(x)*1e5),q=Math.floor(v/10000),r=v-q*10000;if(r>5000||(r===5000&&q%2))q++;return (x<0?-q:q)/10}   // one decimal: noise removed, nearest, exact ties to even (mu_build _r1)
  function proj(st,pp,lf){
    document.querySelectorAll('.lus').forEach(function(lu){
      var band=lu.querySelector('.ltot.lsb');if(!band||band.querySelectorAll('[data-r]').length!==2)return;  // current week only
      ['.lus-a','.lus-o'].forEach(function(sel){
        var bk=lu.querySelector(sel),lp=bk&&bk.querySelector(':scope>.lpv');if(!lp)return;
        var S={a:[0,true,false],b:[0,true,false]},n=0;
        lp.querySelectorAll('.cv').forEach(function(el){if(el.dataset.x===undefined)return;n++;
          var sd=el.classList.contains('a')?'a':'b',r=lx(el,st,pp,lf);S[sd][0]+=r[0];S[sd][1]=S[sd][1]&&r[1];S[sd][2]=S[sd][2]||r[2]});
        if(!n)return;
        if(sel==='.lus-a')band.querySelectorAll('[data-r]').forEach(function(sp,i){var v=sp.querySelector('.llv'),q=S[i?'b':'a'];if(!v)return;
          if(q[1]){v.className='llv fz';v.removeAttribute('title');v.textContent='Final'}else{v.className='llv';v.title='Live projection';v.textContent=f1(q[0])}});
        // slate by slate (2026-11-13): finished slates (every game in them over, from the scores feed, not the slate chip)
        // keep the gap as it stood when they ended, G = actual points in slates up to it + pre-game projection (data-j)
        // after it; the current slate (first not finished) shows the live gap; later slates and No game: empty
        var D=r1(r1(S.a[0])-r1(S.b[0])),X=[];
        bk.querySelectorAll(':scope>.lsv>.slx').forEach(function(sx){
          var q={el:sx,bye:sx.classList.contains('sx-bye'),fin:true,n:0,act:[0,0],pj:[0,0],gm:[false,false]};   // gm: a starter with a game in this slate
          sx.querySelectorAll('.cv').forEach(function(el){if(el.dataset.x===undefined)return;q.n++;
            var i=el.classList.contains('a')?0:1,r=lx(el,st,pp,lf);if(el.dataset.p)q.fin=q.fin&&r[1];if(r[1]||!el.dataset.p)q.act[i]+=r[0];   // a starter without a game line (no data-p) never holds a slate open
            q.pj[i]+=el.dataset.j!==undefined?+el.dataset.j:+el.dataset.x;if(el.dataset.p)q.gm[i]=true});
          X.push(q)});
        var cur=-1;for(var k=0;k<X.length;k++)if(!X[k].bye&&!(X[k].n&&X[k].fin)){cur=k;break}
        X.forEach(function(q,k){
          var c=q.el.querySelector('.sltw');if(!c)return;c=c.querySelectorAll(':scope>span');if(c.length!==2)return;
          var d=null,lt=[false,false];
          if(q.bye||(cur>=0&&k>cur)){}                                           // later slates and No game: empty
          else if(k===cur){d=D;lt=[S.a[2],S.b[2]]}                                // current slate: the live gap
          else{var g=[0,0];X.forEach(function(p,m){for(var i=0;i<2;i++){g[i]+=(!p.bye&&m<=k)?p.act[i]:p.pj[i];
                if(!p.bye&&m>k&&p.gm[i])lt[i]=true}});   // '–' only if nobody played after it
            d=r1(r1(g[0])-r1(g[1]))}                                              // finished slate: frozen at its end
          var tr=d===null?-1:d<=-0.05?0:d>=0.05?1:-1;
          for(var i=0;i<2;i++){var h=i!==tr?'':lt[i]?'<i class="dlt dn">+'+Math.abs(d).toFixed(1)+'</i>':'\u2013';if(c[i].innerHTML!==h)c[i].innerHTML=h}
        });
      });
    });
  }
  function apply(st,mt,lf){
    var pp={},tot={},live=0,done=0;
    mt.forEach(function(m){tot[m.roster_id]=m.points;for(var k in (m.players_points||{}))pp[k]=m.players_points[k]});
    cells.forEach(function(el){
      var pid=el.dataset.p,row=el.closest('.cr'),gp=row&&row.querySelector('.gp[data-t]');
      var cn=el.previousElementSibling; while(cn&&!cn.classList.contains('cn'))cn=cn.previousElementSibling;
      var t=cn&&cn.querySelector('.gp[data-t]');t=t?t.dataset.t:null;var s=t&&st[t];if(!s||s==='pre')return;
      var v=pp[pid]||0,j=+el.dataset.j,fin=s==='post';
      el.classList.remove('pjc');el.classList.add('act');
      var df=Math.round((v-j)*10)/10;el.innerHTML='<span class="fs '+(fin?(v>=j?'up':'dn'):'lv')+'" title="Projected '+f1(j)+'">'+'<em class="fdf">'+(fin?(df>=0?'+':'\u2212')+Math.abs(df).toFixed(1):'')+'</em>'+f1(v)+'<small>'+(fin?'FINAL':'LIVE')+'</small></span>';
      var gl=cn.querySelector('.gp[data-t]');
      if(gl){var w=gl.querySelector('.gwhen'),sp=gl.querySelector('.gsep');
        if(fin){if(w)w.remove();if(sp)sp.remove();gl.classList.add('fin')}else if(w)w.textContent='Live'}
      var z=row.querySelector('[data-sp="'+pid+'"]');
      if(z&&stats[pid]!==undefined){var h=statline(z.dataset.pos,stats[pid]);if(h){z.innerHTML=h;z.className='sln '+(z.className.indexOf('sla')>=0?'sla':'slb')}}
    });
    proj(st,pp,lf||{});
    document.querySelectorAll('.muc2 .sc[data-r]').forEach(function(sp){var r=+sp.dataset.r;if(tot[r]!==undefined&&tot[r]>0)sp.textContent=f1(tot[r])});  // game picker
    if(window.luFit)requestAnimationFrame(window.luFit);  // 2026-11-06: game lines changed (Live / Final): refit the lineup sizes
    document.querySelectorAll('.ltot [data-r]').forEach(function(sp){var r=+sp.dataset.r,b=sp.querySelector('.lt-v');if(b&&tot[r]!==undefined&&tot[r]>0)b.textContent=f1(tot[r])});
    document.querySelectorAll('.ltot').forEach(function(row){var s=row.querySelectorAll('[data-r]');if(s.length!==2)return;
      var a=+s[0].querySelector('.lt-v').textContent||0,b=+s[1].querySelector('.lt-v').textContent||0;s[0].classList.toggle('up',a>b);s[1].classList.toggle('up',b>a)});
    for(var k in st){if(st[k]==='in')live++;if(st[k]==='post')done++}
    return live;
  }
  function show(n,d){box.hidden=false;box.classList.toggle('on',n>0);
    box.textContent=(n>0?'Live · ':'Updated ')+d.toLocaleTimeString([],{hour:'numeric',minute:'2-digit'})}
  function tick(){
    if(!setup()){on=false;clearTimeout(timer);return}  // this week's lineups are not on the page: wait for 'panebuilt'
    if(document.visibilityState!=='visible'){rel();schedule(60000);return}
    get(S+'/scores/nfl/regular/'+Y+'/'+W).then(function(sc){
      var st={},lf={},soon=false,now=Date.now();
      sc.forEach(function(x){var m=x.metadata||{},k=x.status==='in_game'?'in':x.status==='complete'?'post':'pre';
        if(m.home_team)st[m.home_team]=k;if(m.away_team)st[m.away_team]=k;
        if(k==='in'){var q=+m.quarter_num||1,tr=String(m.time_remaining||'15:00').split(':').map(Number),  // share of the game left (sleeper.mjs pullLive)
          lr=q>4?0.02:Math.max(0,Math.min(1,((4-q)*900+(tr[0]||0)*60+(tr[1]||0))/3600));lr=Math.round(lr*1000)/1000;
          if(m.home_team)lf[m.home_team]=lr;if(m.away_team)lf[m.away_team]=lr}
        var d=Date.parse(m.date_time||'');if(k==='pre'&&d&&d-now<15*60000&&d-now>-6*3600000)soon=true});
      var anyIn=Object.keys(st).some(function(k){return st[k]==='in'});
      var chg=!data||JSON.stringify(st)!==JSON.stringify(data[0]);   // a game changed state (e.g. a slate just finished): apply once more
      if(!anyIn&&!soon&&last&&!chg){rel();schedule(600000);return}
      var needStats=anyIn&&now-lastStats>110000||!lastStats;
      return Promise.all([get(A+'/league/'+L+'/matchups/'+W),needStats?get(S+'/stats/nfl/'+Y+'/'+W+'?season_type=regular'):null]).then(function(r){
        if(r[1]){stats={};r[1].forEach(function(x){if(x.stats&&(x.stats.gp||x.stats.gms_active||x.player&&x.player.position==='DEF'))stats[x.player_id]=x.stats});lastStats=now}
        if(!setup()){on=false;return}
        var n=apply(st,r[0],lf);last=now;data=[st,r[0],soon,lf];
        var d=new Date();shown=d;show(n,d);rel();
        schedule(n>0||soon?60000:600000);
      });
    }).catch(function(){rel();schedule(120000)});
  }
  function schedule(ms){clearTimeout(timer);timer=setTimeout(tick,ms)}
  function start(){if(!setup())return;
    if(data){show(apply(data[0],data[1],data[3]),shown)}rel();  // the week was built again: last scores back at once
    if(!on){on=true;var age=Date.now()-last;schedule(!data||age>55000?0:Math.max(500,60000-age))}}
  document.addEventListener('visibilitychange',function(){if(on&&document.visibilityState==='visible'&&Date.now()-last>55000)schedule(500)});
  document.addEventListener('panebuilt',start);
  start();
})();
