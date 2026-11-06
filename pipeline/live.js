// In-page live scores for the Matchups tab (live site only; the download file has no script).
// While the current week has games on, the page asks Sleeper directly (it allows any origin) and patches the
// lineup rows in place: player points, FINAL / LIVE tile, game status, stat line, and each team's points total.
// Polling: every 60 s while a game is in progress and the page is visible; every 10 min otherwise.
// The hourly site rebuild still recomputes everything else (slate totals, optimal lineups, odds).
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
  function f1(x){return (Math.round(x*10)/10).toFixed(1)}
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
  function apply(st,mt){
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
      var st={},soon=false,now=Date.now();
      sc.forEach(function(x){var m=x.metadata||{},k=x.status==='in_game'?'in':x.status==='complete'?'post':'pre';
        if(m.home_team)st[m.home_team]=k;if(m.away_team)st[m.away_team]=k;
        var d=Date.parse(m.date_time||'');if(k==='pre'&&d&&d-now<15*60000&&d-now>-6*3600000)soon=true});
      var anyIn=Object.keys(st).some(function(k){return st[k]==='in'});
      if(!anyIn&&!soon&&last){rel();schedule(600000);return}
      var needStats=anyIn&&now-lastStats>110000||!lastStats;
      return Promise.all([get(A+'/league/'+L+'/matchups/'+W),needStats?get(S+'/stats/nfl/'+Y+'/'+W+'?season_type=regular'):null]).then(function(r){
        if(r[1]){stats={};r[1].forEach(function(x){if(x.stats&&(x.stats.gp||x.stats.gms_active||x.player&&x.player.position==='DEF'))stats[x.player_id]=x.stats});lastStats=now}
        if(!setup()){on=false;return}
        var n=apply(st,r[0]);last=now;data=[st,r[0],soon];
        var d=new Date();shown=d;show(n,d);rel();
        schedule(n>0||soon?60000:600000);
      });
    }).catch(function(){rel();schedule(120000)});
  }
  function schedule(ms){clearTimeout(timer);timer=setTimeout(tick,ms)}
  function start(){if(!setup())return;
    if(data){show(apply(data[0],data[1]),shown)}rel();  // the week was built again: last scores back at once
    if(!on){on=true;var age=Date.now()-last;schedule(!data||age>55000?0:Math.max(500,60000-age))}}
  document.addEventListener('visibilitychange',function(){if(on&&document.visibilityState==='visible'&&Date.now()-last>55000)schedule(500)});
  document.addEventListener('panebuilt',start);
  start();
})();
