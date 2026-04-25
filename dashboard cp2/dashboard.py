import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import re
from pathlib import Path

st.set_page_config(
    page_title="⚽ Análise de Cartões - Brasileirão",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a1a2e;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 12px;
        color: white;
        text-align: center;
    }
    .stMetric {
        background: #f8f9fa;
        padding: 0.8rem;
        border-radius: 10px;
        border-left: 4px solid #764ba2;
    }
    /* Garante legibilidade do st.metric em tema escuro */
    div[data-testid="stMetric"] {
        background: #f8f9fa;
        color: #111827;
    }
    div[data-testid="stMetric"] [data-testid="stMetricLabel"],
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #111827 !important;
    }
    .insight-box {
        background: #f0f4ff;
        border-left: 4px solid #4361ee;
        padding: 0.6rem 1rem;
        border-radius: 0 8px 8px 0;
        margin: 0.3rem 0 1rem 0;
        font-size: 0.88rem;
        color: #333;
    }
</style>
""", unsafe_allow_html=True)

def insight(text):
    st.markdown(f'<div class="insight-box">💡 {text}</div>', unsafe_allow_html=True)

# ─── HELPERS ───────────────────────────────────────────────────────────────────
def parse_placar(s):
    try:
        parts = str(s).replace('x', 'X').split('X')
        return int(parts[0]), int(parts[1])
    except:
        return None, None

def parse_first_minute(val):
    if pd.isna(val) or str(val).strip() in ('-', 'nan', ''):
        return None
    nums = re.findall(r"(\d+)'\+?(\d*)", str(val))
    if not nums:
        return None
    minutes = [int(m) + (int(a) if a else 0) for m, a in nums]
    return min(minutes)

def minuto_faixa(m):
    if pd.isna(m):
        return None
    m = float(m)
    if m <= 15:  return '0-15'
    if m <= 30:  return '16-30'
    if m <= 45:  return '31-45'
    if m <= 60:  return '46-60'
    if m <= 75:  return '61-75'
    return '76-90+'

FAIXAS_ORDER = ['0-15', '16-30', '31-45', '46-60', '61-75', '76-90+']

COLOR_MAP_IMP = {
    'Inversao de resultado':        '#e63946',
    'Resultado mantido':            '#2a9d8f',
    'Sem impacto (placar identico)':'#adb5bd',
}

# ─── LOAD DATA ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    base_dir = Path(__file__).resolve().parent
    csv_candidates = sorted(base_dir.glob("*.csv"))
    if not csv_candidates:
        raise FileNotFoundError(
            f"Nenhum arquivo .csv encontrado em: {base_dir}. "
            "Coloque o CSV na mesma pasta do dashboard.py."
        )
    preferred = [p for p in csv_candidates if "BRA" in p.name.upper()]
    csv_path = preferred[0] if preferred else csv_candidates[0]

    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    df['Gols_Total']   = df['Gol Casa'] + df['Gol Fora']
    df['Faltas_Total'] = df['Falta Casa'] + df['Falta Fora']
    df['CA_Total']     = df['Cartao Amarelo Casa'] + df['Cartao Amarelo Fora'] if 'Cartao Amarelo Casa' in df.columns else df['Cartão Amarelo Casa'] + df['Cartão Amarelo Fora']
    df['CV_Total']     = df['Cartao Vermelho Casa'] + df['Cartao Vermelho Fora'] if 'Cartao Vermelho Casa' in df.columns else df['Cartão Vermelho Casa'] + df['Cartão Vermelho Fora']

    # normalise column names for accented chars
    col_ca_casa = [c for c in df.columns if 'marelo' in c.lower() and 'asa' in c.lower()][0]
    col_ca_fora = [c for c in df.columns if 'marelo' in c.lower() and ('ora' in c.lower() or 'isa' in c.lower())][0]
    col_cv_casa = [c for c in df.columns if 'ermelho' in c.lower() and 'asa' in c.lower()][0]
    col_cv_fora = [c for c in df.columns if 'ermelho' in c.lower() and ('ora' in c.lower() or 'isa' in c.lower())][0]
    col_odd_casa   = [c for c in df.columns if 'odd' in c.lower() and 'asa' in c.lower()][0]
    col_odd_emp    = [c for c in df.columns if 'odd' in c.lower() and 'mpate' in c.lower()][0]
    col_odd_fora   = [c for c in df.columns if 'odd' in c.lower() and ('ora' in c.lower() or 'isa' in c.lower())][0]
    col_arb        = [c for c in df.columns if 'rbitro' in c.lower() or 'rbitro' in c][0]
    col_tv         = [c for c in df.columns if 'teve' in c.lower() and 'ermelho' in c.lower()][0]
    col_pre        = [c for c in df.columns if 'pr' in c.lower() and 'vermelho' in c.lower()][0]
    col_pos        = [c for c in df.columns if 'ltimo' in c.lower() or 'ltim' in c.lower()][0]
    col_min_casa   = [c for c in df.columns if 'min' in c.lower() and 'ermelho' in c.lower() and 'asa' in c.lower()][0]
    col_min_fora   = [c for c in df.columns if 'min' in c.lower() and 'ermelho' in c.lower() and ('ora' in c.lower() or 'isa' in c.lower())][0]

    df['_CA_Casa']   = df[col_ca_casa]
    df['_CA_Fora']   = df[col_ca_fora]
    df['_CV_Casa']   = df[col_cv_casa]
    df['_CV_Fora']   = df[col_cv_fora]
    df['_Odd_Casa']  = df[col_odd_casa]
    df['_Odd_Emp']   = df[col_odd_emp]
    df['_Odd_Fora']  = df[col_odd_fora]
    df['_Arbitro']   = df[col_arb]
    df['_TV']        = df[col_tv]
    df['_Pre']       = df[col_pre]
    df['_Pos']       = df[col_pos]
    df['_Min_Casa']  = df[col_min_casa]
    df['_Min_Fora']  = df[col_min_fora]

    df['CA_Total'] = df['_CA_Casa'] + df['_CA_Fora']
    df['CV_Total'] = df['_CV_Casa'] + df['_CV_Fora']

    def resultado(row):
        if row['Gol Casa'] > row['Gol Fora']:   return 'Vitoria Casa'
        elif row['Gol Casa'] < row['Gol Fora']: return 'Vitoria Fora'
        else:                                    return 'Empate'
    df['Resultado'] = df.apply(resultado, axis=1)

    def favorito(row):
        mn = min(row['_Odd_Casa'], row['_Odd_Emp'], row['_Odd_Fora'])
        if mn == row['_Odd_Casa']:  return 'Casa'
        elif mn == row['_Odd_Fora']: return 'Fora'
        else:                        return 'Equilibrio'
    df['Favorito'] = df.apply(favorito, axis=1)

    def fav_ganhou(row):
        if row['Favorito'] == 'Casa' and row['Resultado'] == 'Vitoria Casa':  return 'Sim'
        elif row['Favorito'] == 'Fora' and row['Resultado'] == 'Vitoria Fora': return 'Sim'
        elif row['Favorito'] == 'Equilibrio': return 'Indefinido'
        else: return 'Nao'
    df['Favorito_Ganhou'] = df.apply(fav_ganhou, axis=1)

    def quem_vermelho(row):
        if row['_TV'] != 'Sim': return 'Nenhum'
        if row['_CV_Casa'] > 0 and row['_CV_Fora'] > 0: return 'Ambos'
        elif row['_CV_Casa'] > 0: return 'Casa'
        elif row['_CV_Fora'] > 0: return 'Fora'
        return 'Nenhum'
    df['Quem_Vermelho'] = df.apply(quem_vermelho, axis=1)

    def vermelho_favorito(row):
        if row['_TV'] != 'Sim': return 'Sem vermelho'
        if row['Favorito'] == 'Casa' and row['_CV_Casa'] > 0:   return 'Favorito levou'
        elif row['Favorito'] == 'Fora' and row['_CV_Fora'] > 0: return 'Favorito levou'
        elif row['Favorito'] == 'Equilibrio': return 'Equilibrio'
        else: return 'Zebra levou'
    df['Vermelho_Favorito'] = df.apply(vermelho_favorito, axis=1)

    df[['Pre_Casa', 'Pre_Fora']] = df['_Pre'].apply(
        lambda x: pd.Series(parse_placar(x) if pd.notna(x) else (None, None))
    )
    df[['Pos_Casa', 'Pos_Fora']] = df['_Pos'].apply(
        lambda x: pd.Series(parse_placar(x) if pd.notna(x) else (None, None))
    )

    def situacao_pre(row):
        if pd.isna(row['Pre_Casa']): return 'N/A'
        if row['Pre_Casa'] > row['Pre_Fora']:   return 'Casa vencia'
        elif row['Pre_Casa'] < row['Pre_Fora']: return 'Fora vencia'
        else:                                    return 'Empate'
    df['Situacao_Pre'] = df.apply(situacao_pre, axis=1)

    df['Min1_Casa']    = df['_Min_Casa'].apply(parse_first_minute)
    df['Min1_Fora']    = df['_Min_Fora'].apply(parse_first_minute)
    df['Min1_Vermelho'] = df.apply(
        lambda r: min([m for m in [r['Min1_Casa'], r['Min1_Fora']] if pd.notna(m)], default=None)
        if (pd.notna(r['Min1_Casa']) or pd.notna(r['Min1_Fora'])) else None,
        axis=1
    )
    df['Faixa_Minuto'] = df['Min1_Vermelho'].apply(minuto_faixa)

    def impacto_causal(row):
        if row['_TV'] != 'Sim':
            return 'Sem vermelho'
        pc, pf = row['Pre_Casa'], row['Pre_Fora']
        gc, gf = row['Gol Casa'], row['Gol Fora']
        if pd.isna(pc) or pd.isna(pf):
            return 'Dados insuficientes'
        lider_pre = 'Casa' if pc > pf else ('Fora' if pc < pf else 'Empate')
        lider_pos = 'Casa' if gc > gf else ('Fora' if gc < gf else 'Empate')
        if pc == gc and pf == gf:
            return 'Sem impacto (placar identico)'
        if lider_pre == lider_pos:
            return 'Resultado mantido'
        return 'Inversao de resultado'
    df['Impacto_Causal'] = df.apply(impacto_causal, axis=1)

    return df

df = load_data()

# ─── SIDEBAR ───────────────────────────────────────────────────────────────────
st.sidebar.image(
    "https://upload.wikimedia.org/wikipedia/pt/4/42/Campeonato_Brasileiro_S%C3%A9rie_A_logo.png",
    width=80
)
st.sidebar.markdown("## Filtros Globais")

temporadas  = sorted(df['Temporada'].unique())
sel_temp    = st.sidebar.multiselect("Temporada", temporadas, default=temporadas)
todos_times = sorted(set(df['Casa'].unique()) | set(df['Visitante'].unique()))
sel_time    = st.sidebar.multiselect("Time (casa ou fora)", todos_times)
arbitros    = sorted(df['_Arbitro'].dropna().unique())
sel_arb     = st.sidebar.selectbox("Arbitro", ["Todos"] + arbitros)

df_f = df[df['Temporada'].isin(sel_temp)]
if sel_time:
    df_f = df_f[(df_f['Casa'].isin(sel_time)) | (df_f['Visitante'].isin(sel_time))]
if sel_arb != "Todos":
    df_f = df_f[df_f['_Arbitro'] == sel_arb]

df_red = df_f[df_f['_TV'] == 'Sim']

# ─── HEADER ────────────────────────────────────────────────────────────────────
st.markdown('<p class="main-header">Analise de Cartoes — Brasileirao Serie A</p>', unsafe_allow_html=True)
st.caption(
    f"Dados filtrados: **{len(df_f)}** partidas | "
    f"Com vermelho: **{len(df_red)}** | "
    f"Sem vermelho: **{len(df_f) - len(df_red)}**"
)
st.divider()

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Impacto do Cartao Vermelho",
    "Analise de Cartoes",
    "Odds e Favoritos",
    "Arbitros",
    "Times"
])

# ══════════════════════════════════════════════════════════════════════
# TAB 1
# ══════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Como o Cartao Vermelho Influencia o Resultado?")

    st.markdown("---")
    col_filt1, col_filt2 = st.columns([3, 1])
    with col_filt1:
        max_minuto = st.slider(
            "Considerar apenas vermelhos ocorridos ate o minuto:",
            min_value=0, max_value=90, value=90, step=5,
            help="Filtra jogos onde o 1 cartao vermelho ocorreu ate o minuto escolhido."
        )
    with col_filt2:
        n_sel = len(df_red[df_red['Min1_Vermelho'] <= max_minuto]) if max_minuto < 90 else len(df_red)
        st.metric("Jogos no filtro", n_sel)

    if max_minuto < 90:
        df_red_m = df_red[(df_red['Min1_Vermelho'].notna()) & (df_red['Min1_Vermelho'] <= max_minuto)]
    else:
        df_red_m = df_red.copy()

    st.markdown("---")

    # KPIs
    c1, c2, c3, c4, c5 = st.columns(5)
    pct_red = len(df_red_m) / len(df_f) * 100 if len(df_f) > 0 else 0
    with c1:
        st.metric("Jogos com Vermelho", f"{len(df_red_m)}", f"{pct_red:.1f}% do total")
    with c2:
        mgr = df_red_m['Gols_Total'].mean() if len(df_red_m) else 0
        mgn = df_f[df_f['_TV'] == 'Nao']['Gols_Total'].mean() if len(df_f[df_f['_TV'] == 'Nao']) else 0
        st.metric("Media de Gols (c/ vermelho)", f"{mgr:.2f}", f"{mgr - mgn:+.2f} vs sem")
    with c3:
        pe_r = (df_red_m['Resultado'] == 'Empate').mean() * 100 if len(df_red_m) else 0
        pe_n = (df_f[df_f['_TV'] == 'Nao']['Resultado'] == 'Empate').mean() * 100 if len(df_f[df_f['_TV'] == 'Nao']) else 0
        st.metric("Empates (c/ vermelho)", f"{pe_r:.1f}%", f"{pe_r - pe_n:+.1f}pp vs sem")
    with c4:
        cp = df_red_m[df_red_m['_CV_Casa'] > 0]
        pct_cp = (cp['Resultado'] != 'Vitoria Casa').mean() * 100 if len(cp) else 0
        st.metric("Casa perde apos vermelho", f"{pct_cp:.1f}%")
    with c5:
        inv = df_red_m[~df_red_m['Impacto_Causal'].isin(['Sem vermelho', 'Dados insuficientes'])]
        pct_inv = (inv['Impacto_Causal'] == 'Inversao de resultado').sum() / len(inv) * 100 if len(inv) else 0
        st.metric("% Inversao de Resultado", f"{pct_inv:.1f}%",
                  help="Jogos onde o lider antes do vermelho nao foi o vencedor final")

    st.markdown("---")

    # ── Bloco A: Impacto Causal
    st.markdown("### Impacto Causal do Cartao Vermelho no Resultado")

    col_imp1, col_imp2 = st.columns([1.6, 1])
    with col_imp1:
        imp_data = df_red_m[
            ~df_red_m['Impacto_Causal'].isin(['Sem vermelho', 'Dados insuficientes'])
        ]['Impacto_Causal'].value_counts(normalize=True).mul(100).reset_index()
        imp_data.columns = ['Categoria', 'Percentual']
        fig_imp = px.bar(
            imp_data, x='Categoria', y='Percentual',
            color='Categoria', text_auto='.1f',
            color_discrete_map=COLOR_MAP_IMP,
            labels={'Percentual': '% de Partidas', 'Categoria': ''},
        )
        fig_imp.update_layout(height=360, showlegend=False, yaxis_title="% de Partidas com Vermelho")
        fig_imp.update_traces(texttemplate='%{y:.1f}%', textposition='outside')
        st.plotly_chart(fig_imp, use_container_width=True)
        insight(
            "A inversao de resultado mede os casos em que quem vencia antes do vermelho nao "
            "saiu vitorioso — quanto maior essa fatia, maior o poder desestruturante da expulsao."
        )

    with col_imp2:
        inv_quem = df_red_m[df_red_m['Impacto_Causal'] == 'Inversao de resultado']
        if len(inv_quem) > 0:
            iq = inv_quem['Quem_Vermelho'].value_counts().reset_index()
            iq.columns = ['Quem levou', 'Inversoes']
            fig_iq = px.pie(iq, names='Quem levou', values='Inversoes',
                            title="Inversoes por quem levou o vermelho",
                            color_discrete_sequence=['#e63946','#457b9d','#f4a261'])
            fig_iq.update_layout(height=360)
            st.plotly_chart(fig_iq, use_container_width=True)
            insight(
                "Quando o time da casa e expulso, as inversoes de resultado sao mais frequentes — "
                "o favorito perde o controle do jogo que havia construido em casa."
            )

    # Impacto causal x situacao pre
    st.markdown("#### Impacto causal cruzado com a situacao antes do vermelho")
    imp_cross = df_red_m[
        ~df_red_m['Impacto_Causal'].isin(['Sem vermelho', 'Dados insuficientes']) &
        (df_red_m['Situacao_Pre'] != 'N/A')
    ]
    if len(imp_cross) > 0:
        cross_tab = imp_cross.groupby(['Situacao_Pre', 'Impacto_Causal']).size().reset_index(name='n')
        cross_tab['pct'] = cross_tab.groupby('Situacao_Pre')['n'].transform(lambda x: x / x.sum() * 100)
        fig_cross = px.bar(
            cross_tab, x='Situacao_Pre', y='pct', color='Impacto_Causal',
            barmode='stack', text_auto='.1f',
            color_discrete_map=COLOR_MAP_IMP,
            labels={'pct': '% de casos', 'Situacao_Pre': 'Situacao antes do vermelho', 'Impacto_Causal': 'Impacto'}
        )
        fig_cross.update_layout(height=370, yaxis_title="% de casos")
        st.plotly_chart(fig_cross, use_container_width=True)
        insight(
            "Jogos empatados no momento da expulsao geram as maiores taxas de inversao — "
            "o equilibrio e mais fragil e o desequilibrio numerico decide o jogo com mais frequencia."
        )

    st.markdown("---")

    # ── Bloco B: Minuto x Impacto
    st.markdown("### O Momento da Expulsao Importa?")
    st.caption("Quanto mais cedo o vermelho, maior o impacto esperado — confirmamos isso nos dados?")

    df_faixas = df_red_m[
        df_red_m['Faixa_Minuto'].notna() &
        ~df_red_m['Impacto_Causal'].isin(['Sem vermelho', 'Dados insuficientes'])
    ].copy()

    col_fx1, col_fx2 = st.columns(2)
    with col_fx1:
        faixa_inv = (
            df_faixas.groupby('Faixa_Minuto')
            .apply(lambda g: pd.Series({
                'Pct_Inversao': (g['Impacto_Causal'] == 'Inversao de resultado').mean() * 100,
                'N': len(g)
            })).reset_index()
        )
        faixa_inv['Faixa_Minuto'] = pd.Categorical(faixa_inv['Faixa_Minuto'], categories=FAIXAS_ORDER, ordered=True)
        faixa_inv = faixa_inv.sort_values('Faixa_Minuto')
        fig_fx = px.bar(
            faixa_inv, x='Faixa_Minuto', y='Pct_Inversao',
            text_auto='.1f', color='Pct_Inversao',
            color_continuous_scale='RdYlGn_r',
            labels={'Faixa_Minuto': 'Faixa de Minuto', 'Pct_Inversao': '% Inversao de Resultado'},
            custom_data=['N']
        )
        fig_fx.update_traces(
            texttemplate='%{y:.1f}%\n(%{customdata[0]} jogos)',
            textposition='outside'
        )
        fig_fx.update_layout(height=400, showlegend=False,
                             yaxis_title="% de Inversoes de Resultado",
                             coloraxis_showscale=False)
        st.plotly_chart(fig_fx, use_container_width=True)
        insight(
            "Vermelhos no 1 tempo (especialmente antes dos 30min) tendem a ter maior taxa de "
            "inversao — mais tempo em desvantagem numerica amplifica o desequilibrio competitivo."
        )

    with col_fx2:
        faixa_stack = df_faixas.groupby(['Faixa_Minuto', 'Impacto_Causal']).size().reset_index(name='n')
        faixa_stack['pct'] = faixa_stack.groupby('Faixa_Minuto')['n'].transform(lambda x: x / x.sum() * 100)
        faixa_stack['Faixa_Minuto'] = pd.Categorical(faixa_stack['Faixa_Minuto'], categories=FAIXAS_ORDER, ordered=True)
        faixa_stack = faixa_stack.sort_values('Faixa_Minuto')
        fig_fstack = px.bar(
            faixa_stack, x='Faixa_Minuto', y='pct', color='Impacto_Causal',
            barmode='stack', text_auto='.0f',
            color_discrete_map=COLOR_MAP_IMP,
            labels={'pct': '% de casos', 'Faixa_Minuto': 'Faixa de Minuto', 'Impacto_Causal': 'Impacto'}
        )
        fig_fstack.update_layout(height=400, yaxis_title="% de casos por faixa")
        st.plotly_chart(fig_fstack, use_container_width=True)
        insight(
            "Vermelhos no periodo final (76-90+) concentram mais casos de 'resultado mantido' — "
            "o jogo ja estava encaminhado e a expulsao tardia raramente altera a trajetoria."
        )

    st.markdown("---")

    # ── Bloco C: Comparativos gerais (originais)
    st.markdown("### Comparativos Gerais")
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("#### Resultado: Com vs Sem Cartao Vermelho")
        sem_tv = df_f[df_f['_TV'] == 'Nao']
        res_comp = pd.DataFrame({
            'Com Vermelho': df_red_m['Resultado'].value_counts(normalize=True) * 100,
            'Sem Vermelho': sem_tv['Resultado'].value_counts(normalize=True) * 100
        }).reset_index().rename(columns={'index': 'Resultado'})
        res_comp_melted = res_comp.melt(id_vars='Resultado', var_name='Grupo', value_name='Percentual')
        fig = px.bar(res_comp_melted, x='Resultado', y='Percentual', color='Grupo',
                     barmode='group', text_auto='.1f',
                     color_discrete_map={'Com Vermelho': '#e63946', 'Sem Vermelho': '#457b9d'})
        fig.update_layout(yaxis_title="% de Partidas", height=350)
        st.plotly_chart(fig, use_container_width=True)
        insight(
            "Jogos com vermelho tem distribuicao de resultados visivelmente diferente — "
            "compare especialmente a fatia de empates, que tende a crescer quando as equipes "
            "ficam mais cautelosas apos a expulsao."
        )

    with col_b:
        st.markdown("#### Quem levou o vermelho e o resultado")
        if len(df_red_m) > 0:
            pivot = df_red_m.groupby(['Quem_Vermelho', 'Resultado']).size().reset_index(name='count')
            pivot['pct'] = pivot.groupby('Quem_Vermelho')['count'].transform(lambda x: x / x.sum() * 100)
            fig2 = px.bar(pivot, x='Quem_Vermelho', y='pct', color='Resultado',
                          barmode='stack', text_auto='.1f',
                          color_discrete_map={
                              'Vitoria Casa': '#2a9d8f',
                              'Vitoria Fora': '#e76f51',
                              'Empate': '#e9c46a'
                          })
            fig2.update_layout(height=350, yaxis_title="% de Partidas")
            st.plotly_chart(fig2, use_container_width=True)
            insight(
                "Quando o visitante leva o vermelho, a vitoria da casa sobe significativamente — "
                "evidencia de que a expulsao fora de casa penaliza mais, onde o placar "
                "costuma ser desfavoravel ao time reduzido."
            )

    col_c, col_d = st.columns(2)
    with col_c:
        st.markdown("#### Placar no momento do 1 vermelho")
        if len(df_red_m) > 0:
            sit_pre = df_red_m[df_red_m['Situacao_Pre'] != 'N/A']['Situacao_Pre'].value_counts().reset_index()
            sit_pre.columns = ['Situacao', 'Count']
            fig3 = px.pie(sit_pre, names='Situacao', values='Count',
                          color_discrete_sequence=['#2a9d8f', '#e76f51', '#e9c46a'])
            fig3.update_layout(height=300)
            st.plotly_chart(fig3, use_container_width=True)
            insight(
                "A maioria dos vermelhos ocorre com o jogo empatado — isso amplifica o poder "
                "de decisao da expulsao, pois nenhum time havia construido vantagem a defender."
            )

    with col_d:
        st.markdown("#### Media de gols marcados apos o vermelho")
        if len(df_red_m) > 0:
            df_mudanca = df_red_m[['Pre_Casa','Pre_Fora','Pos_Casa','Pos_Fora','Quem_Vermelho']].dropna().copy()
            df_mudanca['Delta_Casa'] = df_mudanca['Pos_Casa'] - df_mudanca['Pre_Casa']
            df_mudanca['Delta_Fora'] = df_mudanca['Pos_Fora'] - df_mudanca['Pre_Fora']
            media_delta = df_mudanca.groupby('Quem_Vermelho')[['Delta_Casa','Delta_Fora']].mean().reset_index()
            media_delta_m = media_delta.melt(id_vars='Quem_Vermelho', var_name='Time', value_name='Gols apos vermelho')
            media_delta_m['Time'] = media_delta_m['Time'].map({'Delta_Casa': 'Casa', 'Delta_Fora': 'Fora'})
            fig4 = px.bar(media_delta_m, x='Quem_Vermelho', y='Gols apos vermelho', color='Time',
                          barmode='group', text_auto='.2f',
                          color_discrete_map={'Casa': '#264653', 'Fora': '#e9c46a'})
            fig4.update_layout(height=300)
            st.plotly_chart(fig4, use_container_width=True)
            insight(
                "O time que fica com 11 jogadores marca mais gols apos a expulsao — "
                "a diferenca revela o quanto a desigualdade numerica prejudica a capacidade "
                "ofensiva na parte final do jogo."
            )

# ══════════════════════════════════════════════════════════════════════
# TAB 2 — ANALISE DE CARTOES
# ══════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Media de Cartoes por Jogo")

    filtro_tipo = st.radio("Filtrar por:", ["Sem filtro", "Por Time", "Por Arbitro"], horizontal=True)
    if filtro_tipo == "Por Time":
        time_sel = st.selectbox("Selecione o time", todos_times)
        df_cart  = df_f[(df_f['Casa'] == time_sel) | (df_f['Visitante'] == time_sel)]
        titulo   = f"Time: {time_sel}"
    elif filtro_tipo == "Por Arbitro":
        arb_sel = st.selectbox("Selecione o arbitro", arbitros, key="arb_cart")
        df_cart = df_f[df_f['_Arbitro'] == arb_sel]
        titulo  = f"Arbitro: {arb_sel}"
    else:
        df_cart = df_f
        titulo  = "Todos os jogos"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Media CA Casa/jogo", f"{df_cart['_CA_Casa'].mean():.2f}")
    c2.metric("Media CA Fora/jogo", f"{df_cart['_CA_Fora'].mean():.2f}")
    c3.metric("Media CV Casa/jogo", f"{df_cart['_CV_Casa'].mean():.3f}")
    c4.metric("Media CV Fora/jogo", f"{df_cart['_CV_Fora'].mean():.3f}")
    st.markdown(f"*{titulo} — {len(df_cart)} partidas*")

    col_e, col_f = st.columns(2)
    with col_e:
        st.markdown("#### Distribuicao de Cartoes Amarelos por Jogo")
        fig5 = px.histogram(df_cart, x='CA_Total', nbins=15, color_discrete_sequence=['#f4a261'],
                            labels={'CA_Total': 'Total de Amarelos no Jogo'})
        fig5.add_vline(x=df_cart['CA_Total'].mean(), line_dash='dash', line_color='red',
                       annotation_text=f"Media: {df_cart['CA_Total'].mean():.1f}")
        fig5.update_layout(height=320)
        st.plotly_chart(fig5, use_container_width=True)
        insight(
            "A distribuicao de amarelos e assimetrica a direita — jogos com mais de 6 cartoes "
            "sao raros, mas indicam partidas de alta tensao que frequentemente tambem geram vermelhos."
        )

    with col_f:
        st.markdown("#### Media de Cartoes por Temporada")
        by_temp = df_f.groupby('Temporada')[['CA_Total','CV_Total']].mean().reset_index()
        fig6 = px.bar(by_temp, x='Temporada', y=['CA_Total','CV_Total'], barmode='group',
                      labels={'value':'Media por jogo','variable':'Tipo'},
                      color_discrete_map={'CA_Total':'#f4a261','CV_Total':'#e63946'})
        fig6.update_layout(height=320)
        st.plotly_chart(fig6, use_container_width=True)
        insight(
            "Variacoes entre temporadas podem refletir mudancas de criterio dos arbitros — "
            "uma queda nos amarelos nem sempre significa menos faltas, mas possivelmente mais tolerancia."
        )

    st.markdown("#### Top 10 Times com mais Cartoes Amarelos (media/jogo)")
    am_casa = df_f.groupby('Casa')['_CA_Casa'].mean().rename('Media CA')
    am_fora = df_f.groupby('Visitante')['_CA_Fora'].mean().rename('Media CA')
    am_geral = pd.concat([am_casa, am_fora]).groupby(level=0).mean().sort_values(ascending=False).head(10)
    fig7 = px.bar(am_geral.reset_index(), x='index', y='Media CA',
                  color='Media CA', color_continuous_scale='Oranges',
                  labels={'index':'Time','Media CA':'Media de Amarelos/jogo'})
    fig7.update_layout(height=350, showlegend=False)
    st.plotly_chart(fig7, use_container_width=True)
    insight(
        "Times com alta media de amarelos jogam de forma mais agressiva — o que tambem eleva "
        "o risco de acumulacao e vermelho por 2 amarelo, especialmente em jogos decisivos."
    )

# ══════════════════════════════════════════════════════════════════════
# TAB 3 — ODDS E FAVORITOS
# ══════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Analise de Odds — Favorito vs Resultado Real")

    c1, c2, c3 = st.columns(3)
    base_fav = df_f[df_f['Favorito'] != 'Equilibrio']
    fgp = (base_fav['Favorito_Ganhou'] == 'Sim').mean() * 100 if len(base_fav) else 0
    c1.metric("Favorito vence (geral)", f"{fgp:.1f}%")

    df_fav_red = df_red[df_red['Favorito'] != 'Equilibrio']
    df_fav_no  = df_f[(df_f['_TV'] == 'Nao') & (df_f['Favorito'] != 'Equilibrio')]
    pfr = (df_fav_red['Favorito_Ganhou'] == 'Sim').mean() * 100 if len(df_fav_red) else 0
    pfn = (df_fav_no['Favorito_Ganhou'] == 'Sim').mean() * 100  if len(df_fav_no)  else 0
    c2.metric("Favorito vence (c/ vermelho)",  f"{pfr:.1f}%", f"{pfr - pfn:+.1f}pp")
    c3.metric("Favorito vence (sem vermelho)", f"{pfn:.1f}%")
    insight(
        "A diferenca em pontos percentuais entre jogos com e sem vermelho mede diretamente "
        "o quanto a expulsao desestabiliza o favorito — se negativa, o vermelho nivela o campo."
    )

    col_g, col_h = st.columns(2)
    with col_g:
        st.markdown("#### Resultado quando Favorito leva o Vermelho")
        df_fav_leva = df_red[df_red['Vermelho_Favorito'] == 'Favorito levou']
        if len(df_fav_leva) > 0:
            rf = df_fav_leva['Resultado'].value_counts().reset_index()
            rf.columns = ['Resultado', 'Count']
            fig8 = px.pie(rf, names='Resultado', values='Count',
                          title=f"Favorito levou vermelho ({len(df_fav_leva)} jogos)",
                          color_discrete_sequence=['#2a9d8f','#e76f51','#e9c46a'])
            st.plotly_chart(fig8, use_container_width=True)
            insight(
                "Mesmo expulso, o favorito ainda vence em parte significativa dos casos — "
                "qualidade tecnica superior compensa a desvantagem numerica."
            )

    with col_h:
        st.markdown("#### Resultado quando Zebra leva o Vermelho")
        df_zebra_leva = df_red[df_red['Vermelho_Favorito'] == 'Zebra levou']
        if len(df_zebra_leva) > 0:
            rz = df_zebra_leva['Resultado'].value_counts().reset_index()
            rz.columns = ['Resultado', 'Count']
            fig9 = px.pie(rz, names='Resultado', values='Count',
                          title=f"Zebra levou vermelho ({len(df_zebra_leva)} jogos)",
                          color_discrete_sequence=['#2a9d8f','#e76f51','#e9c46a'])
            st.plotly_chart(fig9, use_container_width=True)
            insight(
                "Quando a zebra e expulsa, a vitoria do favorito sobe consideravelmente — "
                "a vantagem das odds se confirma ainda mais com o adversario em inferioridade."
            )

    st.markdown("#### Odd do favorito vs Resultado (dispersao)")
    df_odds = df_f[df_f['Favorito'] != 'Equilibrio'].copy()
    df_odds['Odd_Favorito'] = df_odds.apply(
        lambda r: r['_Odd_Casa'] if r['Favorito'] == 'Casa' else r['_Odd_Fora'], axis=1
    )
    fig10 = px.strip(df_odds, x='Resultado', y='Odd_Favorito', color='_TV',
                     color_discrete_map={'Sim':'#e63946','Nao':'#457b9d'},
                     labels={'Odd_Favorito': 'Odd do Favorito', 'Resultado': 'Resultado Final', '_TV': 'Teve Vermelho'})
    fig10.update_layout(height=380)
    st.plotly_chart(fig10, use_container_width=True)
    insight(
        "Para odds mais altas (favorito menos obvio), o vermelho tem maior poder de inverter "
        "o resultado esperado — jogos equilibrados sao mais sensiveis a expulsoes."
    )

# ══════════════════════════════════════════════════════════════════════
# TAB 4 — ARBITROS
# ══════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Perfil dos Arbitros")

    min_jogos = st.slider("Minimo de jogos apitados", 5, 30, 10)
    arb_stats = df_f.groupby('_Arbitro').agg(
        Jogos=('Data','count'),
        Media_CA=('CA_Total','mean'),
        Media_CV=('CV_Total','mean'),
        Media_Faltas=('Faltas_Total','mean'),
        Pct_Vermelho=('_TV', lambda x: (x=='Sim').mean() * 100)
    ).reset_index().rename(columns={'_Arbitro': 'Arbitro'})
    arb_stats = arb_stats[arb_stats['Jogos'] >= min_jogos].sort_values('Pct_Vermelho', ascending=False)

    col_i, col_j = st.columns(2)
    with col_i:
        st.markdown(f"#### Top arbitros por % de jogos com vermelho (min. {min_jogos} jogos)")
        fig11 = px.bar(arb_stats.head(15), x='Pct_Vermelho', y='Arbitro',
                       orientation='h', color='Pct_Vermelho',
                       color_continuous_scale='Reds', text_auto='.1f',
                       labels={'Pct_Vermelho':'% jogos c/ vermelho'})
        fig11.update_layout(height=420, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig11, use_container_width=True)
        insight(
            "Arbitros no topo desta lista nao sao necessariamente mais rigorosos — "
            "podem ter apitado mais classicos e jogos de alta tensao; cruzar com o tipo de "
            "partida e essencial para uma conclusao justa."
        )

    with col_j:
        st.markdown("#### Media de Cartoes Amarelos por Arbitro")
        arb_ca = arb_stats.sort_values('Media_CA', ascending=False).head(15)
        fig12 = px.bar(arb_ca, x='Media_CA', y='Arbitro',
                       orientation='h', color='Media_CA',
                       color_continuous_scale='Oranges', text_auto='.2f',
                       labels={'Media_CA':'Media CA/jogo'})
        fig12.update_layout(height=420, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig12, use_container_width=True)
        insight(
            "Alta media de amarelos combinada com baixa taxa de vermelhos indica arbitro preventivo — "
            "usa o amarelo para controlar o jogo antes que a situacao exija uma expulsao."
        )

    st.markdown("#### Dispersao: Media CA x % jogos com Vermelho")
    fig13 = px.scatter(arb_stats, x='Media_CA', y='Pct_Vermelho', size='Jogos',
                       hover_name='Arbitro', color='Media_Faltas',
                       color_continuous_scale='Viridis',
                       labels={'Media_CA':'Media Amarelos/jogo','Pct_Vermelho':'% jogos c/ Vermelho','Media_Faltas':'Media Faltas'})
    fig13.update_layout(height=400)
    st.plotly_chart(fig13, use_container_width=True)
    insight(
        "Arbitros no canto superior direito (muitos amarelos e vermelhos) tem perfil reativo; "
        "os do canto inferior esquerdo sao mais permissivos — a posicao no grafico revela o "
        "estilo de apitar, nao apenas o rigor."
    )

    st.markdown("#### Tabela completa de arbitros")
    arb_show = arb_stats.copy()
    for col in ['Media_CA','Media_CV','Media_Faltas','Pct_Vermelho']:
        arb_show[col] = arb_show[col].round(2)
    st.dataframe(arb_show, use_container_width=True, height=300)

# ══════════════════════════════════════════════════════════════════════
# TAB 5 — TIMES
# ══════════════════════════════════════════════════════════════════════
with tab5:
    st.subheader("Estatisticas por Time")

    times_stats = []
    for time in todos_times:
        jc = df_f[df_f['Casa'] == time]
        jf = df_f[df_f['Visitante'] == time]
        total = len(jc) + len(jf)
        if total == 0:
            continue
        vit  = ((jc['Resultado']=='Vitoria Casa').sum() + (jf['Resultado']=='Vitoria Fora').sum())
        emp  = ((jc['Resultado']=='Empate').sum()       + (jf['Resultado']=='Empate').sum())
        ca   = (jc['_CA_Casa'].sum() + jf['_CA_Fora'].sum()) / total
        cv   = (jc['_CV_Casa'].sum() + jf['_CV_Fora'].sum()) / total
        gm   = (jc['Gol Casa'].sum() + jf['Gol Fora'].sum()) / total
        gs   = (jc['Gol Fora'].sum() + jf['Gol Casa'].sum()) / total
        times_stats.append({
            'Time': time, 'Jogos': total,
            'Vitorias': vit, 'Empates': emp, 'Derrotas': total-vit-emp,
            'Win%': round(vit/total*100,1),
            'Media CA/jogo': round(ca,2), 'Media CV/jogo': round(cv,3),
            'Gols Marcados/j': round(gm,2), 'Gols Sofridos/j': round(gs,2)
        })

    df_times = pd.DataFrame(times_stats).sort_values('Win%', ascending=False)

    col_k, col_l = st.columns(2)
    with col_k:
        st.markdown("#### Win Rate por Time")
        fig14 = px.bar(df_times.head(15), x='Win%', y='Time', orientation='h',
                       color='Win%', color_continuous_scale='Greens', text_auto='.1f')
        fig14.update_layout(height=420, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig14, use_container_width=True)
        insight(
            "A distancia entre lider e lanterna reflete a assimetria competitiva do campeonato — "
            "times com alto win% tendem a ter menos vermelhos, pois dominam sem precisar de faltas taticas."
        )

    with col_l:
        st.markdown("#### Cartoes Amarelos Recebidos (media/jogo)")
        fig15 = px.bar(df_times.sort_values('Media CA/jogo', ascending=False).head(15),
                       x='Media CA/jogo', y='Time', orientation='h',
                       color='Media CA/jogo', color_continuous_scale='Oranges', text_auto='.2f')
        fig15.update_layout(height=420, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig15, use_container_width=True)
        insight(
            "Times com alta media de amarelos e baixo win% usam a falta como recurso defensivo "
            "frequente — um padrao reativo que aumenta exposicao a expulsoes em momentos criticos."
        )

    st.markdown("#### Gols Marcados x Gols Sofridos (por jogo)")
    fig16 = px.scatter(df_times, x='Gols Marcados/j', y='Gols Sofridos/j',
                       size='Jogos', text='Time', color='Win%',
                       color_continuous_scale='RdYlGn',
                       labels={'Gols Marcados/j':'Media Gols Marcados/jogo',
                               'Gols Sofridos/j':'Media Gols Sofridos/jogo'})
    fig16.add_hline(y=df_times['Gols Sofridos/j'].mean(), line_dash='dash', line_color='gray')
    fig16.add_vline(x=df_times['Gols Marcados/j'].mean(), line_dash='dash', line_color='gray')
    fig16.update_traces(textposition='top center')
    fig16.update_layout(height=500)
    st.plotly_chart(fig16, use_container_width=True)
    insight(
        "O quadrante superior esquerdo (marca pouco, sofre muito) concentra times em zona de "
        "rebaixamento; o inferior direito reune os candidatos ao titulo — as linhas tracejadas "
        "representam a media do campeonato em cada eixo."
    )

    st.markdown("#### Tabela completa")
    st.dataframe(df_times, use_container_width=True, height=350)

st.divider()
st.caption(
    "Dashboard criado por Lucas Massoni RM 561686 e Felipe Murad RM 562347 | "
    "Dados: Brasileirao Serie A 2024-2026"
)
