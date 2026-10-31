# Team-colour badges (primary background, contrasting text) used instead of logos
NFLC={'ARI':('#97233F','#fff'),'ATL':('#A71930','#fff'),'BAL':('#241773','#fff'),'BUF':('#00338D','#fff'),'CAR':('#0085CA','#fff'),
'CHI':('#0B162A','#F26A2E'),'CIN':('#FB4F14','#000'),'CLE':('#311D00','#FF6A2C'),'DAL':('#003594','#fff'),'DEN':('#FB4F14','#002244'),
'DET':('#0076B6','#fff'),'GB':('#203731','#FFB612'),'HOU':('#03202F','#F0525F'),'IND':('#002C5F','#fff'),'JAX':('#006778','#E8B53A'),
'KC':('#E31837','#FFD24A'),'LV':('#000000','#C4C8CB'),'LAC':('#0080C6','#FFD13A'),'LAR':('#003594','#FFD100'),'MIA':('#008E97','#fff'),
'MIN':('#4F2683','#FFC62F'),'NE':('#002244','#F0525F'),'NO':('#D3BC8D','#101820'),'NYG':('#0B2265','#fff'),'NYJ':('#125740','#fff'),
'PHI':('#004C54','#fff'),'PIT':('#FFB612','#101820'),'SF':('#AA0000','#fff'),'SEA':('#002244','#7DD13A'),'TB':('#D50A0A','#fff'),
'TEN':('#0C2340','#5FA8E8'),'WAS':('#5A1414','#FFB612')}
def badge(t):
    bg,fg=NFLC.get(t,('#3a4254','#eef0f4'));return f'<em class="nfl" style="background:{bg};color:{fg}"><span class="ct">{t}</span></em>'
def badge_c(t):return f'<em class="nfl n-{t}"><span class="ct">{t}</span></em>'
NFL_CSS=''.join(f'.n-{t}{{background:{bg};color:{fg}}}' for t,(bg,fg) in NFLC.items())
def team_tiles(on):
    """CSS that paints position tiles (.pq carrying a t-TEAM class) in NFL team colours when the selector `on` matches,
    e.g. on='#plc-t:checked~.plb'. Text inside the tile follows the team's contrasting colour."""
    return (''.join(f'{on} .pq.t-{t}{{--pc:{bg};color:{fg}!important}}' for t,(bg,fg) in NFLC.items())
            +f'{on} .pq[class*=" t-"] .pqi>span,{on} .pq[class*=" t-"] .pqi>b{{color:inherit!important}}')
