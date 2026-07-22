import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
import datetime

# =============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# =============================================================================
st.set_page_config(
    page_title="Painel Operacional | Grupo Paineiras",
    page_icon="🏔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# 2. IDENTIDADE VISUAL — cores extraídas da logo do Grupo Paineiras
# =============================================================================
COLORS = {
    "navy_dark":   "#14213D",   # azul marinho principal (logo/wordmark)
    "navy":        "#1E3A5F",   # azul secundário
    "navy_light":  "#4C7EA8",   # azul claro (acentos)
    "green":       "#6DBE45",   # verde principal (triângulo da logo)
    "green_dark":  "#3E8E2F",   # verde escuro
    "green_light": "#A9DC7A",   # verde claro
    "bg":          "#F4F6F9",   # fundo geral
    "card_bg":     "#FFFFFF",
    "text":        "#1F2937",
    "text_muted":  "#6B7280",
    "danger":      "#D64545",
    "warning":     "#E5A83E",
}

# Cor fixa por setor — mantém consistência em todos os gráficos
SERVICE_COLORS = {
    "Limpeza Industrial":  COLORS["green"],
    "Segurança":           COLORS["navy_dark"],
    "Manutenção Predial":  COLORS["green_dark"],
    "Portaria":            COLORS["navy_light"],
}

px.defaults.template = "plotly_white"
px.defaults.color_discrete_map = SERVICE_COLORS


def estilizar_grafico(fig, altura=360):
    """Aplica padrão visual (fonte, cores, grid) a todos os gráficos do painel."""
    fig.update_layout(
        height=altura,
        font=dict(family="Poppins, Inter, sans-serif", color=COLORS["text"], size=13),
        plot_bgcolor=COLORS["card_bg"],
        paper_bgcolor=COLORS["card_bg"],
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(color=COLORS["text"])),
        margin=dict(l=10, r=10, t=40, b=10),
        hoverlabel=dict(bgcolor="white", font_size=12, font_family="Inter, sans-serif",
                         font_color=COLORS["text"], bordercolor=COLORS["navy_light"]),
    )
    fig.update_xaxes(showgrid=False, linecolor="#E5E7EB",
                      tickfont=dict(color=COLORS["text"]), title_font=dict(color=COLORS["text"]))
    fig.update_yaxes(showgrid=True, gridcolor="#EEF1F5", zeroline=False,
                      tickfont=dict(color=COLORS["text"]), title_font=dict(color=COLORS["text"]))
    return fig


# =============================================================================
# 3. CSS CUSTOMIZADO — cards de KPI, cabeçalho, sidebar e tipografia
# =============================================================================
st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
    html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}

    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stHeader"],
    .main .block-container {{
        background-color: {COLORS['bg']} !important;
    }}
    .main, .main p, .main span, .main label {{ color: {COLORS['text']} !important; }}

    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background-color: {COLORS['navy_dark']};
    }}
    section[data-testid="stSidebar"] * {{ color: #EDF1F7 !important; }}
    section[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {{
        background-color: {COLORS['green']} !important;
    }}

    /* Cabeçalho */
    .paineiras-header {{
        background: linear-gradient(90deg, {COLORS['navy_dark']} 0%, {COLORS['navy']} 100%);
        padding: 22px 30px;
        border-radius: 14px;
        margin-bottom: 22px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }}
    .paineiras-header h1 {{
        color: white; font-family: 'Poppins', sans-serif; font-weight: 700;
        font-size: 26px; margin: 0;
    }}
    .paineiras-header p {{
        color: {COLORS['green_light']}; margin: 2px 0 0 0; font-size: 15px; font-weight: 500;
    }}
    .status-badge {{
        padding: 6px 16px; border-radius: 20px; font-weight: 600; font-size: 13px;
        color: white; white-space: nowrap;
    }}

    /* Cards de KPI */
    .kpi-card {{
        background-color: {COLORS['card_bg']} !important;
        border-radius: 12px;
        padding: 20px 20px;
        box-shadow: 0 1px 4px rgba(20,33,61,0.08);
        border-left: 5px solid {COLORS['green']};
        height: 100%;
        margin-bottom: 22px;
    }}
    .kpi-card .kpi-icon {{ font-size: 20px; margin-bottom: 4px; }}
    .kpi-card .kpi-label {{
        font-size: 12.5px; color: {COLORS['text_muted']}; font-weight: 600;
        text-transform: uppercase; letter-spacing: 0.03em; margin-bottom: 4px;
    }}
    .kpi-card .kpi-value {{
        font-size: 25px; font-weight: 700; color: {COLORS['navy_dark']};
        font-family: 'Poppins', sans-serif; line-height: 1.1;
    }}
    .kpi-card .kpi-delta {{ font-size: 12.5px; font-weight: 600; margin-top: 4px; }}
    .delta-pos {{ color: {COLORS['green_dark']}; }}
    .delta-neg {{ color: {COLORS['danger']}; }}

    /* Seções */
    .section-title {{
        font-family: 'Poppins', sans-serif; font-weight: 600; font-size: 17px;
        color: {COLORS['navy_dark']}; margin: 22px 0 14px 0;
        border-left: 4px solid {COLORS['green']}; padding-left: 10px;
    }}

    /* Cartão em volta de cada gráfico Plotly — garante fundo claro e legível
       independentemente do tema (claro/escuro) configurado no Streamlit */
    [data-testid="stPlotlyChart"] {{
        background-color: {COLORS['card_bg']} !important;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 1px 4px rgba(20,33,61,0.08);
        margin-bottom: 26px;
    }}

    /* Espaço extra entre blocos verticais empilhados (cards, gráficos, seções) */
    div[data-testid="stVerticalBlock"] > div[data-testid="stElementContainer"] {{
        margin-bottom: 4px;
    }}

    /* Abas */
    .stTabs [data-baseweb="tab-list"] {{ gap: 4px; }}
    .stTabs [data-baseweb="tab"] {{
        background-color: white; border-radius: 8px 8px 0 0; padding: 10px 18px;
        font-weight: 600; color: {COLORS['text_muted']};
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {COLORS['navy_dark']} !important; color: white !important;
    }}

    .insight-box {{
        background-color: white; border-radius: 12px; padding: 16px 20px;
        border-left: 5px solid {COLORS['navy']}; margin-bottom: 18px;
        color: {COLORS['text']} !important;
    }}
    .insight-box, .insight-box * {{
        color: {COLORS['text']} !important;
    }}
    .insight-box b {{
        color: {COLORS['navy_dark']} !important;
    }}
</style>
""", unsafe_allow_html=True)


# =============================================================================
# 4. GERAÇÃO DE DADOS FICTÍCIOS
#    Substituir esta função pela leitura da base real (ERP / planilhas / BI)
#    assim que houver integração — a estrutura do DataFrame deve ser mantida.
# =============================================================================
@st.cache_data
def carregar_dados():
    np.random.seed(42)
    datas = pd.date_range(start='2026-05-01', end='2026-07-20', freq='D')
    servicos = ['Limpeza Industrial', 'Segurança', 'Manutenção Predial', 'Portaria']
    efetivo_base = {'Limpeza Industrial': 30, 'Segurança': 12, 'Manutenção Predial': 8, 'Portaria': 5}

    linhas = []
    for data in datas:
        for servico in servicos:
            efetivo_previsto = efetivo_base[servico]
            faltas = int(np.random.choice([0, 0, 0, 1, 1, 2], p=[0.45, 0.15, 0.15, 0.15, 0.05, 0.05]))
            efetivo_realizado = max(efetivo_previsto - faltas, 0)

            sla = float(np.clip(np.random.normal(96, 2.5), 85, 100))
            custo = efetivo_previsto * 150.0 + np.random.uniform(100, 500)

            chamados_abertos = int(np.random.poisson(3 if servico == 'Manutenção Predial' else 1))
            chamados_resolvidos = int(np.random.binomial(chamados_abertos, 0.85)) if chamados_abertos else 0
            tempo_resolucao_h = float(np.clip(np.random.exponential(8), 0.5, 60))

            ocorrencia_seguranca = int(np.random.choice([0, 0, 0, 0, 1], p=[0.85, 0.05, 0.05, 0.03, 0.02]))
            csat = float(np.clip(np.random.normal(4.5, 0.3), 3.0, 5.0))
            horas_extras = float(np.clip(np.random.exponential(2), 0, 20))

            linhas.append({
                'Data': data,
                'Serviço': servico,
                'SLA_Realizado_%': round(sla, 1),
                'Efetivo_Previsto': efetivo_previsto,
                'Efetivo_Realizado': efetivo_realizado,
                'Faltas': faltas,
                'Custo_Operacional_R$': round(custo, 2),
                'Chamados_Abertos': chamados_abertos,
                'Chamados_Resolvidos': chamados_resolvidos,
                'Tempo_Resolucao_Horas': round(tempo_resolucao_h, 1),
                'Ocorrencias_Seguranca': ocorrencia_seguranca,
                'CSAT': round(csat, 2),
                'Horas_Extras': round(horas_extras, 1),
            })
    return pd.DataFrame(linhas)


df = carregar_dados()

# =============================================================================
# 5. CABEÇALHO
# =============================================================================
logo_path = "logo.png"
col_logo, col_titulo = st.columns([1, 5])
with col_logo:
    if os.path.exists(logo_path):
        st.image(logo_path, width=200)
    else:
        st.markdown(f"<div style='font-size:42px;'>🏔️</div>", unsafe_allow_html=True)

with col_titulo:
    st.markdown(f"""
    <div class="paineiras-header">
        <div>
            <h1>Painel de Performance Operacional</h1>
            <p>Cliente Estratégico: Nestlé &nbsp;|&nbsp; Grupo Paineiras — Facilities & Serviços</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# 6. FILTROS (SIDEBAR)
# =============================================================================

st.sidebar.markdown("## 🔎 Filtros de Análise")

data_min, data_max = df['Data'].min().date(), df['Data'].max().date()
periodo = st.sidebar.date_input(
    "Período", value=(data_min, data_max), min_value=data_min, max_value=data_max
)
if isinstance(periodo, tuple) and len(periodo) == 2:
    data_ini, data_fim = periodo
else:
    data_ini, data_fim = data_min, data_max

servico_selecionado = st.sidebar.multiselect(
    "Setor", df['Serviço'].unique(), default=list(df['Serviço'].unique())
)

meta_sla = st.sidebar.slider("Meta de SLA (%)", 80, 100, 95)

st.sidebar.markdown("---")
st.sidebar.caption("Painel elaborado pela equipe de BI & Indicadores · Grupo Paineiras")

df_filtrado = df[
    (df['Data'].dt.date >= data_ini) &
    (df['Data'].dt.date <= data_fim) &
    (df['Serviço'].isin(servico_selecionado))
]

if df_filtrado.empty:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")
    st.stop()

# =============================================================================
# 7. CÁLCULO DOS KPIs
# =============================================================================
media_sla = df_filtrado['SLA_Realizado_%'].mean()
total_faltas = int(df_filtrado['Faltas'].sum())
efetivo_total = df_filtrado['Efetivo_Previsto'].sum()
efetivo_realizado_total = df_filtrado['Efetivo_Realizado'].sum()
taxa_absenteismo = (total_faltas / efetivo_total) * 100 if efetivo_total > 0 else 0
custo_total = df_filtrado['Custo_Operacional_R$'].sum()
custo_per_capita = custo_total / efetivo_total if efetivo_total > 0 else 0

total_chamados = int(df_filtrado['Chamados_Abertos'].sum())
total_resolvidos = int(df_filtrado['Chamados_Resolvidos'].sum())
taxa_resolucao = (total_resolvidos / total_chamados * 100) if total_chamados > 0 else 0
mttr_medio = df_filtrado.loc[df_filtrado['Chamados_Resolvidos'] > 0, 'Tempo_Resolucao_Horas'].mean()
mttr_medio = 0 if pd.isna(mttr_medio) else mttr_medio

total_ocorrencias = int(df_filtrado['Ocorrencias_Seguranca'].sum())
csat_medio = df_filtrado['CSAT'].mean()
total_horas_extras = df_filtrado['Horas_Extras'].sum()


def fmt_moeda(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def kpi_card(col, icon, label, value, delta=None, positive=True):
    delta_html = ""
    if delta is not None:
        cls = "delta-pos" if positive else "delta-neg"
        seta = "▲" if positive else "▼"
        delta_html = f'<div class="kpi-delta {cls}">{seta} {delta}</div>'
    col.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# 8. BADGE DE STATUS GERAL (no cabeçalho)
# =============================================================================
status_cor = COLORS["green_dark"] if media_sla >= meta_sla else (COLORS["warning"] if media_sla >= meta_sla - 3 else COLORS["danger"])
status_texto = "Dentro da Meta" if media_sla >= meta_sla else "Atenção Necessária"
st.markdown(f"""
<div style="margin-top:-14px; margin-bottom:18px; text-align:right;">
    <span class="status-badge" style="background-color:{status_cor};">● {status_texto} — SLA {media_sla:.1f}% (meta {meta_sla}%)</span>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# 9. ABAS EXECUTIVAS
# =============================================================================
aba_geral, aba_operacional, aba_qualidade, aba_dados = st.tabs(
    ["📊 Visão Geral", "👥 Operacional", "🎯 Qualidade & Atendimento", "📋 Dados Detalhados"]
)

# ---------------------------------------------------------------- VISÃO GERAL
with aba_geral:
    c1, c2, c3, c4 = st.columns(4, gap="large")
    kpi_card(c1, "✅", "SLA Médio", f"{media_sla:.1f}%",
             f"{media_sla - meta_sla:+.1f} pp vs meta", positive=(media_sla >= meta_sla))
    kpi_card(c2, "💰", "Custo Operacional", fmt_moeda(custo_total))
    kpi_card(c3, "🧾", "Custo per Capita", fmt_moeda(custo_per_capita))
    kpi_card(c4, "⭐", "CSAT Médio", f"{csat_medio:.2f} / 5.0")

    # Resumo executivo automático
    setor_mais_caro = df_filtrado.groupby('Serviço')['Custo_Operacional_R$'].sum().idxmax()
    setor_melhor_sla = df_filtrado.groupby('Serviço')['SLA_Realizado_%'].mean().idxmax()
    setor_pior_sla = df_filtrado.groupby('Serviço')['SLA_Realizado_%'].mean().idxmin()
    st.markdown(f"""
    <div class="insight-box">
        <b>📌 Resumo Executivo:</b> No período selecionado, o SLA médio geral foi de <b>{media_sla:.1f}%</b>
        (meta: {meta_sla}%). O setor com melhor desempenho de SLA foi <b>{setor_melhor_sla}</b>, enquanto
        <b>{setor_pior_sla}</b> apresentou o menor índice, merecendo atenção. O maior custo operacional
        está concentrado em <b>{setor_mais_caro}</b>. A taxa de absenteísmo geral foi de <b>{taxa_absenteismo:.2f}%</b>.
    </div>
    """, unsafe_allow_html=True)

    g1, g2 = st.columns(2, gap="large")
    with g1:
        st.markdown('<div class="section-title">Evolução do SLA por Setor</div>', unsafe_allow_html=True)
        df_linha = df_filtrado.groupby(['Data', 'Serviço'])['SLA_Realizado_%'].mean().reset_index()
        fig_sla = px.line(df_linha, x='Data', y='SLA_Realizado_%', color='Serviço', markers=True)
        fig_sla.add_hline(y=meta_sla, line_dash="dash", line_color=COLORS["danger"],
                           annotation_text="Meta", annotation_position="bottom right")
        fig_sla.update_layout(yaxis_title="SLA (%)", xaxis_title="")
        st.plotly_chart(estilizar_grafico(fig_sla), use_container_width=True)

    with g2:
        st.markdown('<div class="section-title">Custo Operacional por Setor</div>', unsafe_allow_html=True)
        df_custo = df_filtrado.groupby('Serviço')['Custo_Operacional_R$'].sum().reset_index()
        fig_custo = px.pie(df_custo, names='Serviço', values='Custo_Operacional_R$', hole=0.55)
        fig_custo.update_traces(textinfo='percent+label', textfont_size=12)
        st.plotly_chart(estilizar_grafico(fig_custo), use_container_width=True)

# ---------------------------------------------------------------- OPERACIONAL
with aba_operacional:
    c1, c2, c3, c4 = st.columns(4, gap="large")
    kpi_card(c1, "🧍", "Efetivo Previsto", f"{efetivo_total:,}".replace(",", "."))
    kpi_card(c2, "✔️", "Efetivo Realizado", f"{efetivo_realizado_total:,}".replace(",", "."))
    kpi_card(c3, "🚫", "Total de Faltas", f"{total_faltas}", positive=False, delta=None)
    kpi_card(c4, "📉", "Taxa de Absenteísmo", f"{taxa_absenteismo:.2f}%")

    g1, g2 = st.columns(2, gap="large")
    with g1:
        st.markdown('<div class="section-title">Efetivo Previsto vs. Realizado por Setor</div>', unsafe_allow_html=True)
        df_efetivo = df_filtrado.groupby('Serviço')[['Efetivo_Previsto', 'Efetivo_Realizado']].mean().reset_index()
        fig_efetivo = go.Figure()
        fig_efetivo.add_bar(name='Previsto', x=df_efetivo['Serviço'], y=df_efetivo['Efetivo_Previsto'],
                             marker_color=COLORS['navy_light'])
        fig_efetivo.add_bar(name='Realizado', x=df_efetivo['Serviço'], y=df_efetivo['Efetivo_Realizado'],
                             marker_color=COLORS['green'])
        fig_efetivo.update_layout(barmode='group', yaxis_title="Colaboradores (média/dia)")
        st.plotly_chart(estilizar_grafico(fig_efetivo), use_container_width=True)

    with g2:
        st.markdown('<div class="section-title">Impacto de Faltas por Setor</div>', unsafe_allow_html=True)
        df_faltas = df_filtrado.groupby('Serviço')['Faltas'].sum().reset_index()
        fig_faltas = px.bar(df_faltas, x='Serviço', y='Faltas', color='Serviço', text='Faltas')
        fig_faltas.update_layout(showlegend=False, xaxis_title="", yaxis_title="Nº de Faltas Acumuladas")
        st.plotly_chart(estilizar_grafico(fig_faltas), use_container_width=True)

    st.markdown('<div class="section-title">Horas Extras Acumuladas por Setor</div>', unsafe_allow_html=True)
    df_he = df_filtrado.groupby('Serviço')['Horas_Extras'].sum().reset_index()
    fig_he = px.bar(df_he, x='Serviço', y='Horas_Extras', color='Serviço', text_auto='.0f')
    fig_he.update_layout(showlegend=False, xaxis_title="", yaxis_title="Horas Extras (h)")
    st.plotly_chart(estilizar_grafico(fig_he, altura=300), use_container_width=True)

# --------------------------------------------------------- QUALIDADE/ATENDIM.
with aba_qualidade:
    c1, c2, c3, c4 = st.columns(4, gap="large")
    kpi_card(c1, "🎫", "Chamados Abertos", f"{total_chamados}")
    kpi_card(c2, "✅", "Taxa de Resolução", f"{taxa_resolucao:.1f}%")
    kpi_card(c3, "⏱️", "MTTR Médio", f"{mttr_medio:.1f} h")
    kpi_card(c4, "🦺", "Ocorrências de Segurança", f"{total_ocorrencias}",
             positive=(total_ocorrencias == 0), delta=None)

    g1, g2 = st.columns(2, gap="large")
    with g1:
        st.markdown('<div class="section-title">Chamados: Abertos vs. Resolvidos</div>', unsafe_allow_html=True)
        df_chamados = df_filtrado.groupby('Data')[['Chamados_Abertos', 'Chamados_Resolvidos']].sum().reset_index()
        fig_chamados = go.Figure()
        fig_chamados.add_scatter(x=df_chamados['Data'], y=df_chamados['Chamados_Abertos'],
                                  name='Abertos', mode='lines', line=dict(color=COLORS['navy'], width=2),
                                  fill='tozeroy', fillcolor='rgba(30,58,95,0.10)')
        fig_chamados.add_scatter(x=df_chamados['Data'], y=df_chamados['Chamados_Resolvidos'],
                                  name='Resolvidos', mode='lines', line=dict(color=COLORS['green'], width=2),
                                  fill='tozeroy', fillcolor='rgba(109,190,69,0.15)')
        fig_chamados.update_layout(yaxis_title="Nº de Chamados", xaxis_title="")
        st.plotly_chart(estilizar_grafico(fig_chamados), use_container_width=True)

    with g2:
        st.markdown('<div class="section-title">Evolução da Satisfação do Cliente (CSAT)</div>', unsafe_allow_html=True)
        df_csat = df_filtrado.groupby('Data')['CSAT'].mean().reset_index()
        fig_csat = px.line(df_csat, x='Data', y='CSAT', markers=False)
        fig_csat.update_traces(line_color=COLORS['navy_dark'])
        fig_csat.add_hline(y=4.5, line_dash="dash", line_color=COLORS["green_dark"],
                            annotation_text="Meta CSAT", annotation_position="bottom right")
        fig_csat.update_layout(yaxis_title="CSAT (0-5)", xaxis_title="", yaxis_range=[3, 5])
        st.plotly_chart(estilizar_grafico(fig_csat), use_container_width=True)

# ------------------------------------------------------------- DADOS/RELAT.
with aba_dados:
    st.markdown('<div class="section-title">Relatório Consolidado Diário</div>', unsafe_allow_html=True)
    colunas_exibir = [
        'Data', 'Serviço', 'SLA_Realizado_%', 'Efetivo_Previsto', 'Efetivo_Realizado',
        'Faltas', 'Custo_Operacional_R$', 'Chamados_Abertos', 'Chamados_Resolvidos',
        'Tempo_Resolucao_Horas', 'Ocorrencias_Seguranca', 'CSAT'
    ]
    tabela = df_filtrado[colunas_exibir].sort_values(by='Data', ascending=False)
    st.dataframe(tabela, use_container_width=True, hide_index=True)

    csv = tabela.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')
    st.download_button(
        "⬇️ Exportar Relatório (CSV)", data=csv,
        file_name=f"relatorio_paineiras_{datetime.date.today()}.csv", mime="text/csv"
    )

st.markdown(f"""
<div style="text-align:center; color:{COLORS['text_muted']}; font-size:12px; margin-top:24px;">
    Grupo Paineiras · Painel de Performance Operacional · Dados atualizados automaticamente
</div>
""", unsafe_allow_html=True)