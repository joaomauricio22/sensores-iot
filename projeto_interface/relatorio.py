"""Geração do relatório visual (HTML autocontido) de uma rota.

Produz um único arquivo ``.html`` que pode ser aberto por duplo clique e
impresso em PDF (Ctrl+P). Tudo fica embutido no próprio arquivo: CSS, o logo do
Sentinela e os gráficos (PNG em base64) — não há arquivos auxiliares.

Os gráficos são desenhados com ``matplotlib.figure.Figure`` (API orientada a
objetos, sem ``pyplot``), o que permite gerar a imagem tanto dentro da interface
Tkinter (backend TkAgg) quanto num script de linha de comando (backend Agg) sem
conflito de backends.

Formato do relatório:
  1. cabeçalho com logo, nome da rota e data de geração;
  2. cards de indicadores (score, distância, duração, velocidade, RPM, eventos);
  3. gráfico de velocidade no tempo com os eventos marcados;
  4. gráfico de eventos por classificação;
  5. tabela de resumo e tabela dos eventos mais relevantes.
"""
import base64
import html
import os
import re
import unicodedata
from datetime import datetime
from io import BytesIO

from matplotlib.figure import Figure

# --------------------------------------------------------------------------- #
# Paleta e metadados (espelham tabs.py; mantidos aqui para o módulo ser
# utilizável também por um script CLI sem importar Tkinter).
# --------------------------------------------------------------------------- #
CORES_TIPO = {
    "Frenagem brusca": "#d63031",
    "Aceleração brusca": "#e17055",
    "Curva em alta velocidade": "#6c5ce7",
    "Excesso de velocidade": "#f39c12",
    "RPM excessivo": "#e84393",
    "Acelerador brusco": "#00b894",
    "Comportamento atípico": "#636e72",
}

PESO_TIPO = {
    "Frenagem brusca": 6,
    "Curva em alta velocidade": 5,
    "Aceleração brusca": 4,
    "Excesso de velocidade": 3,
    "RPM excessivo": 2,
    "Acelerador brusco": 2,
    "Comportamento atípico": 1,
}

COR_SCORE = {True: "#00b894", False: None}  # placeholder; função dedicada abaixo

NAVY = "#0d1b2a"
TEXTO = "#2d3436"
CINZA = "#636e72"
BORDA = "#dfe6e9"

_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

# Pasta padrão dos relatórios gerados (junto do material de apresentação).
PASTA_RELATORIOS = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "apresentacao", "relatorios"))


def nome_arquivo(titulo):
    """Converte um título legível num nome de arquivo seguro (sem acentos)."""
    texto = unicodedata.normalize("NFKD", titulo or "")
    texto = texto.encode("ascii", "ignore").decode("ascii")
    texto = re.sub(r"[^A-Za-z0-9]+", "_", texto).strip("_")
    return texto or "relatorio"


def _cor_score(score):
    if score >= 80:
        return "#00b894"
    if score >= 50:
        return "#f39c12"
    return "#d63031"


def _formatar_duracao(segundos):
    s = int(segundos or 0)
    h, resto = divmod(s, 3600)
    m, s = divmod(resto, 60)
    if h:
        return f"{h}h {m:02d}min {s:02d}s"
    if m:
        return f"{m}min {s:02d}s"
    return f"{s}s"


def _formatar_hora(data_hora):
    if not data_hora:
        return "—"
    texto = str(data_hora).replace("T", " ").split(".")[0].split("+")[0]
    return texto.split(" ")[1] if " " in texto else texto


def _fig_png(fig) -> str:
    """Renderiza a figura em PNG e devolve uma string base64 (data URI)."""
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                facecolor="white")
    buf.seek(0)
    return "data:image/png;base64," + base64.b64encode(buf.read()).decode("ascii")


def _grafico_velocidade(grafico) -> Figure:
    """Velocidade no tempo, com os eventos de risco marcados por cor."""
    pontos = (grafico or {}).get("pontos") or []
    fig = Figure(figsize=(9.4, 3.6), dpi=100)
    ax = fig.add_subplot(111)

    tempos = [p.get("tempo", 0) / 60.0 for p in pontos]
    vels = [p.get("velocidade") for p in pontos]
    ax.plot(tempos, vels, color=NAVY, linewidth=1.4, zorder=2)

    # Linha do limite de excesso de velocidade (referência padrão do projeto).
    ax.axhline(100.0, color="#f39c12", linewidth=1.0, linestyle="--", alpha=0.8)
    ax.text(tempos[-1] if tempos else 0, 100.0, "  100 km/h", color="#f39c12",
            fontsize=8, va="center")

    # Marca cada ponto de risco com a cor da sua classificação.
    por_tipo = {}
    for p in pontos:
        if not p.get("risco"):
            continue
        tipo = (p.get("classificacoes") or ["Comportamento atípico"])[0]
        por_tipo.setdefault(tipo, {"x": [], "y": []})
        por_tipo[tipo]["x"].append(p.get("tempo", 0) / 60.0)
        por_tipo[tipo]["y"].append(p.get("velocidade"))

    for tipo, dados in por_tipo.items():
        ax.scatter(dados["x"], dados["y"], s=18, color=CORES_TIPO.get(tipo, CINZA),
                   label=tipo, zorder=3, edgecolors="white", linewidths=0.4)

    ax.set_xlabel("Tempo (min)")
    ax.set_ylabel("Velocidade (km/h)")
    ax.set_title("Velocidade no tempo — eventos de risco marcados", fontsize=11,
                 color=TEXTO, loc="left")
    ax.grid(True, color="#eef1f5", linewidth=0.6)
    ax.set_axisbelow(True)
    for esp in ("top", "right"):
        ax.spines[esp].set_visible(False)
    ax.tick_params(labelsize=8)
    if por_tipo:
        ax.legend(fontsize=7, loc="upper left", frameon=False, ncol=2)
    fig.tight_layout()
    return fig


def _grafico_tipos(eventos_por_tipo) -> Figure:
    """Barras horizontais: quantidade de eventos por classificação."""
    itens = sorted((eventos_por_tipo or {}).items(), key=lambda kv: kv[1])
    fig = Figure(figsize=(9.4, 2.9), dpi=100)
    ax = fig.add_subplot(111)

    rotulos = [t for t, _ in itens]
    valores = [n for _, n in itens]
    cores = [CORES_TIPO.get(t, CINZA) for t in rotulos]
    ax.barh(rotulos, valores, color=cores)
    for i, v in enumerate(valores):
        ax.text(v, i, f" {v}", va="center", fontsize=8, color=TEXTO)

    ax.set_title("Eventos por classificação", fontsize=11, color=TEXTO, loc="left")
    ax.set_xlabel("Quantidade (instantes de risco distintos)")
    ax.grid(True, axis="x", color="#eef1f5", linewidth=0.6)
    ax.set_axisbelow(True)
    for esp in ("top", "right"):
        ax.spines[esp].set_visible(False)
    ax.tick_params(labelsize=8)
    fig.tight_layout()
    return fig


def _logo_base64() -> str:
    caminho = os.path.join(_ASSETS, "sentinela_logo.png")
    if not os.path.exists(caminho):
        return ""
    with open(caminho, "rb") as arquivo:
        return "data:image/png;base64," + base64.b64encode(arquivo.read()).decode("ascii")


def _esc(texto) -> str:
    """Escapa conteúdo para inserção segura no HTML."""
    if texto is None:
        return "—"
    return html.escape(str(texto))


def _tabela_eventos(eventos, limite=20):
    """Ordena os eventos por severidade e devolve as linhas (HTML) mais relevantes."""
    ordenados = sorted(
        eventos,
        key=lambda e: (-PESO_TIPO.get(e.get("classificacao"), 0), str(e.get("data_hora") or "")),
    )[:limite]
    linhas = []
    for e in ordenados:
        tipo = e.get("classificacao") or "Comportamento atípico"
        cor = CORES_TIPO.get(tipo, CINZA)
        fg = e.get("forca_g")
        fg = f"{fg:.2f}" if isinstance(fg, (int, float)) else "—"
        val = e.get("valor")
        val = f"{val:.2f}" if isinstance(val, (int, float)) else "—"
        linhas.append(
            "<tr>"
            f"<td><span class='bolinha' style='background:{cor}'></span>{_esc(tipo)}</td>"
            f"<td>{_esc(e.get('metodo'))}</td>"
            f"<td>{_formatar_hora(e.get('data_hora'))}</td>"
            f"<td class='num'>{val}</td>"
            f"<td class='num'>{fg}</td>"
            f"<td class='desc'>{_esc(e.get('descricao'))}</td>"
            "</tr>"
        )
    return "\n".join(linhas)


def gerar_relatorio(resumo, eventos, grafico, caminho, titulo=None):
    """Gera o relatório visual e grava em ``caminho`` (arquivo HTML único).

    ``titulo`` é o nome que aparece no cabeçalho e no ``<title>`` do documento.
    Quando omitido, usa "Relatório de Telemetria Veicular".
    """
    resumo = resumo or {}
    eventos = eventos or []
    nome = resumo.get("nome") or "Rota sem nome"
    titulo = titulo or "Relatório de Telemetria Veicular"
    score = resumo.get("score", 0)
    cor_score = _cor_score(score)

    png_velocidade = _fig_png(_grafico_velocidade(grafico)) if (grafico or {}).get("pontos") else ""
    png_tipos = _fig_png(_grafico_tipos(resumo.get("eventos_por_tipo"))) if resumo.get("eventos_por_tipo") else ""

    logo = _logo_base64()

    blocos = []

    # ---------------------------------------------------------------- cards
    cards = [
        ("Score de segurança", str(score), cor_score, "font-size:40px"),
        ("Distância", f"{resumo.get('distancia_km', 0):.2f} km", TEXTO, ""),
        ("Duração", _formatar_duracao(resumo.get("duracao_segundos")), TEXTO, ""),
        ("Velocidade média", f"{resumo.get('velocidade_media', 0):.1f} km/h", TEXTO, ""),
        ("Velocidade máxima", f"{resumo.get('velocidade_maxima', 0):.1f} km/h", TEXTO, ""),
        ("RPM máximo", f"{resumo.get('rpm_maximo', 0):.0f} RPM", TEXTO, ""),
        ("Total de eventos", str(resumo.get("total_eventos", 0)), TEXTO, ""),
    ]
    cards_html = "\n".join(
        f"<div class='card'><div class='card-label'>{label}</div>"
        f"<div class='card-valor' style='color:{cor};{style}'>{valor}</div></div>"
        for label, valor, cor, style in cards
    )
    blocos.append(f"<div class='cards'>{cards_html}</div>")

    # ---------------------------------------------------------------- gráficos
    if png_velocidade:
        blocos.append(
            f"<div class='figura'><img src='{png_velocidade}' alt='Velocidade no tempo'></div>"
        )
    if png_tipos:
        blocos.append(
            f"<div class='figura'><img src='{png_tipos}' alt='Eventos por classificação'></div>"
        )

    # ---------------------------------------------------------------- tabela resumo
    resumo_linhas = "".join(
        f"<tr><th>{_esc(t)}</th><td class='num'>{n}</td></tr>"
        for t, n in sorted((resumo.get("eventos_por_tipo") or {}).items(),
                           key=lambda kv: -kv[1])
    ) or "<tr><td colspan='2'>Nenhum evento de risco detectado.</td></tr>"
    blocos.append(
        "<h2>Eventos por tipo</h2>"
        f"<table class='tabela'><thead><tr><th>Classificação</th><th>Ocorrências</th></tr>"
        f"</thead><tbody>{resumo_linhas}</tbody></table>"
    )

    # ---------------------------------------------------------------- tabela eventos
    if eventos:
        corpo = _tabela_eventos(eventos)
        blocos.append(
            "<h2>Eventos mais relevantes</h2>"
            "<table class='tabela'><thead><tr><th>Tipo</th><th>Método</th><th>Hora</th>"
            "<th>Valor</th><th>Força G</th><th>Descrição</th></tr></thead>"
            f"<tbody>{corpo}</tbody></table>"
        )

    logo_html = f"<img class='logo' src='{logo}' alt='Sentinela'>" if logo else "Sentinela"
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")

    html_final = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(titulo)}</title>
<style>
  :root {{ --navy:#0d1b2a; --texto:#2d3436; --cinza:#636e72; --borda:#dfe6e9; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; font-family:'Segoe UI', Arial, sans-serif; color:var(--texto);
          background:#f5f6fa; }}
  .capa {{ background:var(--navy); color:#fff; padding:26px 34px; display:flex;
           align-items:center; gap:20px; }}
  .capa .logo {{ height:52px; }}
  .capa h1 {{ margin:0; font-size:22px; }}
  .capa .sub {{ color:#b2bec3; font-size:13px; margin-top:4px; }}
  .capa .data {{ margin-left:auto; color:#9badd4; font-size:12px; text-align:right; }}
  main {{ max-width:1000px; margin:0 auto; padding:24px 20px 40px; }}
  .cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
            gap:12px; margin-bottom:22px; }}
  .card {{ background:#fff; border:1px solid var(--borda); border-radius:10px;
           padding:14px 16px; }}
  .card-label {{ font-size:12px; color:var(--cinza); margin-bottom:6px; }}
  .card-valor {{ font-size:20px; font-weight:700; }}
  .figura {{ background:#fff; border:1px solid var(--borda); border-radius:10px;
             padding:10px; margin-bottom:20px; }}
  .figura img {{ width:100%; display:block; }}
  h2 {{ font-size:16px; color:var(--navy); margin:26px 0 10px; }}
  .tabela {{ width:100%; border-collapse:collapse; background:#fff;
             border:1px solid var(--borda); border-radius:10px; overflow:hidden; }}
  .tabela th, .tabela td {{ text-align:left; padding:8px 12px; font-size:13px;
                            border-bottom:1px solid #eef1f5; }}
  .tabela thead th {{ background:var(--navy); color:#fff; font-size:12px;
                      text-transform:uppercase; letter-spacing:.3px; }}
  .tabela tbody tr:nth-child(even) {{ background:#fafbfd; }}
  .tabela .num {{ text-align:right; font-variant-numeric:tabular-nums; }}
  .tabela .desc {{ color:var(--cinza); font-size:12px; }}
  .bolinha {{ display:inline-block; width:9px; height:9px; border-radius:50%;
              margin-right:7px; }}
  .nota {{ color:var(--cinza); font-size:12px; margin-top:18px;
           border-top:1px solid var(--borda); padding-top:12px; }}
  @media print {{ body {{ background:#fff; }} .capa {{ -webkit-print-color-adjust:exact;
                 print-color-adjust:exact; }} }}
</style>
</head>
<body>
  <div class="capa">
    {logo_html}
    <div>
      <h1>{_esc(titulo)}</h1>
      <div class="sub">Rota: {_esc(nome)} &nbsp;·&nbsp; Sentinela</div>
    </div>
    <div class="data">Gerado em<br>{agora}</div>
  </div>
  <main>
    {''.join(blocos)}
    <p class="nota">O “total de eventos” conta instantes de risco distintos: uma mesma
    leitura sinalizada por mais de um método é contada uma única vez, mas cada registro
    permanece na tabela <em>evento_risco</em> (Regra 9). O score é normalizado pela
    distância percorrida.</p>
  </main>
</body>
</html>
"""
    destino = os.path.abspath(caminho)
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, "w", encoding="utf-8") as arquivo:
        arquivo.write(html_final)
