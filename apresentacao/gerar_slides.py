"""Gera os slides da apresentação (Parte 6) em formato PowerPoint (.pptx).

Tema único (dark/navy). Domínio: telemetria veicular (OBD-II) e detecção de risco.

Executar:  python gerar_slides.py
Saída:     slides_pav.pptx
"""
import os
import sys

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMGS = os.path.join(BASE_DIR, "imgs")

LOGO = os.path.join(IMGS, "logo_sentinela.png")
WATERMARK = os.path.join(IMGS, "logo_watermark.png")

NAVY = RGBColor(0x0D, 0x1B, 0x2A)
NAVY_2 = RGBColor(0x17, 0x2A, 0x45)
NAVY_3 = RGBColor(0x1F, 0x3A, 0x5C)
CARD = RGBColor(0x14, 0x25, 0x3D)
CARD_2 = RGBColor(0x1B, 0x30, 0x4C)

BLUE = RGBColor(0x09, 0x84, 0xE3)
CYAN = RGBColor(0x00, 0xCE, 0xC9)
TEAL = RGBColor(0x00, 0xB8, 0x94)
PURPLE = RGBColor(0x6C, 0x5C, 0xE7)
ORANGE = RGBColor(0xE1, 0x70, 0x55)
RED = RGBColor(0xD6, 0x30, 0x31)
YELLOW = RGBColor(0xF3, 0x9C, 0x12)

WHITE = RGBColor(0xFF, 0xFF, 0xFF)
TEXT = RGBColor(0xDE, 0xE7, 0xF1)
TEXT_DIM = RGBColor(0x9B, 0xAD, 0xC4)
SOFT = RGBColor(0xC9, 0xDA, 0xEC)

FONT = "Segoe UI"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


def _shape(slide, kind, l, t, w, h, fill=None, line=None, radius=None):
    sp = slide.shapes.add_shape(kind, Inches(l), Inches(t), Inches(w), Inches(h))
    sp.shadow.inherit = False
    if fill is None:
        sp.fill.background()
    else:
        sp.fill.solid()
        sp.fill.fore_color.rgb = fill
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = line
        sp.line.width = Pt(1)
    if radius is not None and kind == MSO_SHAPE.ROUNDED_RECTANGLE:
        try:
            sp.adjustments[0] = radius
        except Exception:
            pass
    return sp


def _text(slide, l, t, w, h, text, size=18, color=TEXT, bold=False,
          align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.bold = bold
    run.font.name = FONT
    return tf


def _shape_text(sp, text, size=16, color=WHITE, bold=True, align=PP_ALIGN.CENTER):
    tf = sp.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = Inches(0.08)
    tf.margin_right = Inches(0.08)
    tf.margin_top = Inches(0.03)
    tf.margin_bottom = Inches(0.03)
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.bold = bold
    run.font.name = FONT
    return tf


def _badge(slide, l, t, d, number, color=CYAN):
    sp = _shape(slide, MSO_SHAPE.OVAL, l, t, d, d, fill=color)
    _shape_text(sp, str(number), size=14, color=WHITE, bold=True)
    return sp


def _navy_bg(slide, subtle=True):
    _shape(slide, MSO_SHAPE.RECTANGLE, 0, 0, 13.333, 7.5, fill=NAVY)
    _shape(slide, MSO_SHAPE.OVAL, 11.3, -2.6, 5.6, 5.6, fill=NAVY_2)
    if subtle:
        _shape(slide, MSO_SHAPE.OVAL, -2.5, 5.7, 4.4, 4.4, fill=NAVY_2)
    else:
        _shape(slide, MSO_SHAPE.OVAL, 11.0, 5.0, 4.6, 4.6, fill=NAVY_3)
        _shape(slide, MSO_SHAPE.OVAL, -2.0, 5.4, 5.0, 5.0, fill=NAVY_2)


def _footer(slide, page):
    _shape(slide, MSO_SHAPE.RECTANGLE, 0.6, 7.05, 12.13, 0.012, fill=NAVY_3)
    _text(slide, 0.6, 7.13, 8, 0.3, "Sentinela — Telemetria e Segurança Veicular",
          size=10, color=TEXT_DIM)
    _text(slide, 11.6, 7.13, 1.13, 0.3, f"{page:02d}", size=11, color=TEXT_DIM,
          bold=True, align=PP_ALIGN.RIGHT)


def _watermark(slide, x=7.9, y=4.85, w=4.9):
    """Marca d'água discreta da logo, atrás do conteúdo."""
    try:
        slide.shapes.add_picture(WATERMARK, Inches(x), Inches(y), width=Inches(w))
    except Exception:
        pass


def _content_slide(number, title, accent=CYAN, page=None):
    slide = prs.slides.add_slide(BLANK)
    _navy_bg(slide)
    _watermark(slide)
    if number is not None:
        _badge(slide, 0.6, 0.45, 0.62, number, color=accent)
        _text(slide, 1.45, 0.5, 11, 0.7, title, size=30, color=WHITE, bold=True)
        line_x = 1.5
    else:
        _text(slide, 0.6, 0.5, 11, 0.7, title, size=30, color=WHITE, bold=True)
        line_x = 0.65
    _shape(slide, MSO_SHAPE.RECTANGLE, line_x, 1.32, 2.4, 0.06, fill=CYAN)
    if page is not None:
        _footer(slide, page)
    return slide


def _card(slide, l, t, w, h, title, body, accent, title_size=15, body_size=12.5):
    _shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h, fill=CARD, radius=0.08)
    _shape(slide, MSO_SHAPE.RECTANGLE, l, t, 0.09, h, fill=accent)
    if title:
        _text(slide, l + 0.28, t + 0.16, w - 0.5, 0.4, title, size=title_size,
              color=WHITE, bold=True)
    if body:
        _text(slide, l + 0.28, t + (0.55 if title else 0.2), w - 0.55, h - 0.7,
              body, size=body_size, color=TEXT)


def _shot(slide, path, x, y, w, cap):
    _shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x - 0.06, y - 0.06, w + 0.12, w * 0.64 + 0.12,
           fill=NAVY_3, line=NAVY_3, radius=0.04)
    slide.shapes.add_picture(path, Inches(x), Inches(y), width=Inches(w))
    _text(slide, x, y + w * 0.64 + 0.1, w, 0.4, cap, size=12, color=SOFT, bold=True,
          align=PP_ALIGN.CENTER)


# ================================================================ 1. CAPA
slide = prs.slides.add_slide(BLANK)
_navy_bg(slide, subtle=False)
# Logo (substitui o texto do título; já contém "Sentinela" e a tagline)
slide.shapes.add_picture(LOGO, Inches(0.9), Inches(0.95), width=Inches(9.6))
_shape(slide, MSO_SHAPE.RECTANGLE, 1.05, 4.15, 2.6, 0.09, fill=CYAN)
_text(slide, 1.0, 4.4, 10.8, 0.9,
      "Telemetria veicular OBD-II e detecção de eventos de risco na condução",
      size=19, color=SOFT)
# Tema do trabalho (explícito)
_shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, 1.0, 5.35, 10.9, 0.7, fill=CARD, radius=0.2)
_text(slide, 1.25, 5.5, 10.4, 0.45,
      "Tema: análise de dados de sensores IoT com classificação por Machine Learning",
      size=14, color=CYAN, bold=True)
_shape(slide, MSO_SHAPE.OVAL, 1.0, 6.55, 0.38, 0.38, fill=BLUE)
_text(slide, 1.55, 6.58, 10.8, 0.35,
      "João Maurício Araújo Leitão  •  Programação de Aplicações — Trabalho PAV (Parte 6)",
      size=13, color=WHITE, bold=True)

# ================================================================ 2. CONTEXTO
s = _content_slide(1, "Contexto do Sistema", accent=BLUE, page=2)
_cards = [
    ("Receber", "Dados de telemetria coletados pela interface OBD-II do veículo.", BLUE),
    ("Padronizar", "Normaliza nomes de colunas de fontes diferentes para parâmetros canônicos.", PURPLE),
    ("Armazenar", "Persistência em PostgreSQL (3 tabelas relacionadas).", TEAL),
    ("Analisar", "Detecção de eventos de risco com DBSCAN e RandomForest.", ORANGE),
]
y = 1.75
for titulo, texto, cor in _cards:
    _card(s, 0.6, y, 6.0, 1.05, titulo, texto, cor)
    y += 1.22
_text(s, 7.0, 1.85, 5.7, 5.0,
      "Parâmetros monitorados\n\n"
      "• Velocidade\n"
      "• Rotação do motor (RPM)\n"
      "• Aceleração triaxial (X, Y, Z)\n"
      "• Posição do acelerador\n"
      "• Localização (GPS)",
      size=16, color=TEXT)

# ================================================================ 3. PROBLEMA
s = _content_slide(2, "Problema que o Sistema Resolve", accent=PURPLE, page=3)
_problemas = [
    ("Volume de dados", "O OBD-II gera milhares de leituras por viagem — análise manual é inviável.", BLUE),
    ("Riscos silenciosos", "Frenagens bruscas e curvas fechadas podem passar despercebidas.", RED),
    ("Fontes heterogêneas", "Ferramentas diferentes nomeiam a mesma grandeza de formas distintas.", ORANGE),
]
x = 0.6
for titulo, texto, cor in _problemas:
    _card(s, x, 1.7, 3.9, 1.7, titulo, texto, cor, title_size=16)
    x += 4.15
arr = _shape(s, MSO_SHAPE.DOWN_ARROW, 6.05, 3.7, 1.2, 1.2, fill=TEAL)
_text(s, 0.6, 5.3, 12.1, 1.3,
      "Solução: padroniza os dados, caracteriza o perfil do condutor e\n"
      "detecta automaticamente os eventos de condução de risco.",
      size=18, color=WHITE, bold=True, align=PP_ALIGN.CENTER)

# ================================================================ 4. REQUISITOS
s = _content_slide(3, "Requisitos Principais — 10 regras de negócio", accent=RED, page=4)
_regras = [
    ("Cada sensor possui um identificador único.", BLUE),
    ("Leitura exige sensor, valor e data/hora.", PURPLE),
    ("Leitura apenas para sensor cadastrado.", TEAL),
    ("Valores numéricos e compatíveis com o tipo.", ORANGE),
    ("Sem leituras duplicadas (sensor + valor + instante).", RED),
    ("Limites mínimo/máximo por tipo de sensor.", YELLOW),
    ("Anomalia: fora dos limites ou desvio do histórico.", RED),
    ("Classificação pelo modelo de ML.", PURPLE),
    ("Registro da anomalia (sensor, valor, data/hora, método).", TEAL),
    ("Análise histórica (padrões estatísticos).", BLUE),
]
for i, (regra, cor) in enumerate(_regras):
    col = i // 5
    row = i % 5
    x = 0.6 + col * 6.2
    y = 1.6 + row * 1.02
    _shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, 5.9, 0.82, fill=CARD, radius=0.16)
    _badge(s, x + 0.18, y + 0.16, 0.5, i + 1, color=cor)
    _text(s, x + 0.85, y + 0.21, 4.9, 0.5, regra, size=13.5, color=TEXT)

# ================================================================ 5. MODELO DE DADOS
s = _content_slide(4, "Modelo do Banco de Dados", accent=TEAL, page=5)
entidades = [
    ("rota", "nome\narquivo de origem\ndata de importação", BLUE),
    ("leitura", "velocidade, rpm\naccel_x/y/z\nacelerador, GPS", TEAL),
    ("evento_risco", "canal, valor\nforça_g\nclassificação, método", RED),
]
x = 1.0
for nome, campos, cor in entidades:
    box = _shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x, 2.0, 3.0, 2.3, fill=CARD, radius=0.08)
    _shape(s, MSO_SHAPE.RECTANGLE, x, 2.0, 3.0, 0.5, fill=cor)
    _text(s, x, 2.06, 3.0, 0.4, nome, size=13, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    _text(s, x + 0.2, 2.66, 2.6, 1.6, campos, size=11.5, color=TEXT)
    if nome != "evento_risco":
        _text(s, x + 3.0, 2.95, 0.7, 0.4, "1 ⟶ N", size=13, color=TEXT_DIM, bold=True,
              align=PP_ALIGN.CENTER)
    x += 3.7
_card(s, 0.7, 4.7, 12, 1.15, "Limiares e catálogo de sensores (JSON)",
      "config/limiares.json — fonte única dos limiares de risco e da faixa (min/max) de cada sensor.",
      CYAN, title_size=14, body_size=13.5)
_card(s, 0.7, 5.9, 12, 1.0, "Padronização de parâmetros (back-end)",
      "'Vehicle speed (km/h)' e 'Velocidade do veículo (km/h)' → mapeados para o parâmetro canônico 'velocidade'.",
      CYAN, title_size=14, body_size=12.5)

# ================================================================ 6. ARQUITETURA
s = _content_slide(5, "Arquitetura da Aplicação", accent=BLUE, page=6)
camadas = [
    ("entities", "Classes que mapeiam as tabelas (SQLAlchemy)", BLUE),
    ("repositories", "Operações no banco: SELECT / INSERT / UPDATE / DELETE", PURPLE),
    ("services", "Regras de negócio + importação + análise", TEAL),
    ("controllers", "Recebem as requisições HTTP (Flask-RESTful)", ORANGE),
    ("routes", "Mapeamento das URLs", RED),
]
x = 0.5
for nome, desc, cor in camadas:
    sp = _shape(s, MSO_SHAPE.CHEVRON, x, 2.15, 2.75, 1.6, fill=cor)
    _shape_text(sp, nome, size=15, color=WHITE, bold=True)
    _text(s, x + 0.25, 3.85, 2.35, 1.0, desc, size=11.5, color=TEXT_DIM, align=PP_ALIGN.CENTER)
    x += 2.55
_card(s, 0.5, 5.7, 12.3, 0.9, "Fluxo de uma requisição",
      "HTTP → routes → controllers → services → repositories → entities → banco de dados",
      CYAN, title_size=13.5, body_size=14)

# ================================================================ 7. CLASSES
s = _content_slide(6, "Principais Classes", accent=PURPLE, page=7)
_text(s, 0.6, 1.5, 12, 0.5, "Herança e polimorfismo na detecção de risco:",
      size=16, color=WHITE, bold=True)
base = _shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 4.45, 1.95, 4.4, 0.7, fill=NAVY_3, radius=0.18)
_shape_text(base, "DetectorAnomalia  (classe abstrata)", size=14)
_shape(s, MSO_SHAPE.RECTANGLE, 6.62, 2.65, 0.06, 0.22, fill=TEXT_DIM)
_shape(s, MSO_SHAPE.RECTANGLE, 2.05, 2.85, 9.2, 0.05, fill=TEXT_DIM)
detectores = [
    ("LimiteDetector", "limites do CTB", BLUE),
    ("EstatisticoDetector", "z-score do histórico", PURPLE),
    ("ModeloMLDetector", "DBSCAN + RandomForest", TEAL),
]
xs = [0.7, 4.35, 8.0]
for (nome, desc, cor), x in zip(detectores, xs):
    _shape(s, MSO_SHAPE.RECTANGLE, x + 1.42, 2.9, 0.05, 0.22, fill=TEXT_DIM)
    box = _shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x, 3.12, 2.9, 0.7, fill=cor, radius=0.14)
    _shape_text(box, nome, size=13.5)
    _text(s, x + 0.1, 3.92, 2.7, 0.4, desc, size=11, color=TEXT_DIM, align=PP_ALIGN.CENTER)
_cards2 = [
    ("ImportadorService", "Padroniza os nomes de colunas na importação dos CSVs.", TEAL),
    ("features", "Força G resultante, aceleração longitudinal e instabilidade.", BLUE),
    ("AnaliseService", "Orquestra os detectores e registra os eventos.", ORANGE),
]
y = 4.6
for titulo, texto, cor in _cards2:
    _card(s, 0.6, y, 12.1, 0.75, titulo, texto, cor, title_size=13.5, body_size=12.5)
    y += 0.88

# ================================================================ 8. DETECÇÃO (extra)
s = _content_slide(None, "Detecção de Risco — 3 métodos", accent=RED, page=8)
metodos = [
    ("1", "LIMITE", "Aceleração longitudinal\nfora dos limites do CTB\n(+2,5 / -3,0 m/s²).", BLUE),
    ("2", "ESTATÍSTICO", "z-score (|z| > 3) da Força G\nem relação ao histórico\nda rota.", PURPLE),
    ("3", "MODELO_ML", "DBSCAN (pseudo-rótulos)\n+ RandomForest:\nclassifica eventos de risco.", TEAL),
]
x = 0.6
for num, nome, desc, cor in metodos:
    _shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x, 1.7, 3.9, 3.4, fill=CARD, radius=0.06)
    _badge(s, x + 0.25, 1.95, 0.6, num, color=cor)
    _text(s, x + 0.25, 2.75, 3.4, 0.6, nome, size=18, color=cor, bold=True)
    _text(s, x + 0.3, 3.4, 3.3, 1.6, desc, size=14, color=TEXT)
    x += 4.15
_text(s, 0.6, 5.35, 12.1, 1.3,
      "Força G resultante = √(ax² + ay²)   •   instabilidade = desvio padrão da aceleração (janela de 3 s).\n"
      "6 classificações: frenagem brusca · aceleração brusca · curva em alta velocidade · excesso de velocidade · RPM excessivo · acelerador brusco.",
      size=13.5, color=TEXT_DIM, align=PP_ALIGN.CENTER)

# ================================================================ 9. ENDPOINTS
s = _content_slide(7, "Endpoints da API", accent=BLUE, page=9)
headers = ["Método", "Rota", "Descrição"]
rows = [
    ("GET / POST", "/telemetria/rotas", "Listar / cadastrar rotas"),
    ("POST", "/telemetria/rotas/importar", "Importar CSV como rota"),
    ("GET / PUT / DELETE", "/telemetria/rotas/<id>", "Selecionar / editar / excluir"),
    ("POST", "/telemetria/rotas/<id>/analisar", "Detecção de eventos de risco"),
    ("GET", "/telemetria/rotas/<id>/grafico", "Dados para o gráfico (e análise por sensor)"),
    ("GET", "/telemetria/rotas/<id>/resumo", "Dashboard: score + estatísticas"),
    ("POST", "/telemetria/rotas/comparar", "Comparar resumos de rotas"),
    ("GET / POST", "/telemetria/leituras", "Listar / cadastrar leituras"),
    ("GET / PUT / DELETE", "/telemetria/leituras/<id>", "Selecionar / editar / excluir leitura"),
    ("GET / POST", "/telemetria/eventos-risco", "Listar (filtros) / cadastrar eventos"),
    ("GET / PUT / DELETE", "/telemetria/eventos-risco/<id>", "Selecionar / editar / excluir evento"),
    ("GET", "/telemetria/limiares", "Ler os limiares (somente leitura)"),
    ("GET", "/telemetria/sensores", "Catálogo de sensores/canais"),
]
n_rows = len(rows) + 1
gf = s.shapes.add_table(n_rows, 3, Inches(0.6), Inches(1.55), Inches(12.1), Inches(5.3))
table = gf.table
for j, h in enumerate(headers):
    c = table.cell(0, j)
    c.text = h
    c.fill.solid()
    c.fill.fore_color.rgb = BLUE
    for p in c.text_frame.paragraphs:
        p.alignment = PP_ALIGN.CENTER
        for r in p.runs:
            r.font.bold = True
            r.font.size = Pt(14)
            r.font.color.rgb = WHITE
            r.font.name = FONT
for i, row in enumerate(rows, start=1):
    for j, val in enumerate(row):
        c = table.cell(i, j)
        c.text = val
        c.fill.solid()
        c.fill.fore_color.rgb = CARD if i % 2 == 1 else CARD_2
        for p in c.text_frame.paragraphs:
            for r in p.runs:
                r.font.size = Pt(12.5)
                r.font.color.rgb = TEXT
                r.font.name = FONT
table.columns[0].width = Inches(2.4)
table.columns[1].width = Inches(4.4)
table.columns[2].width = Inches(5.3)

# ================================================================ 10. INTERFACE
s = _content_slide(8, "Interface Gráfica", accent=TEAL, page=10)
passos = [
    ("1. Dados", "CRUD de rotas, leituras e eventos", BLUE),
    ("2. Cadastrar", "CSV vira uma rota nomeada", PURPLE),
    ("3. Análise", "Automática — sem botão", ORANGE),
    ("4. Explorar", "Visão Geral, gráfico, sensores e comparação", RED),
]
x = 0.6
for titulo, desc, cor in passos:
    box = _shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x, 1.7, 2.9, 2.2, fill=CARD, radius=0.08)
    _shape(s, MSO_SHAPE.OVAL, x + 1.1, 1.95, 0.7, 0.7, fill=cor)
    _text(s, x + 0.15, 2.85, 2.6, 0.6, titulo, size=15, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    _text(s, x + 0.15, 3.4, 2.6, 0.6, desc, size=11.5, color=TEXT_DIM, align=PP_ALIGN.CENTER)
    x += 3.08
_text(s, 0.6, 4.35, 12.1, 0.6,
      "Navegação lateral: Dados (Rotas · Leituras · Eventos) · Visão Geral · Gráfico · Sensores · Comparar.",
      size=14, color=TEXT, align=PP_ALIGN.CENTER)
_card(s, 0.6, 5.2, 12.1, 1.5, "Sem expor IDs",
      "A seleção é feita por combobox/listas (o ID fica interno).\n"
      "Cadastro em lote via CSV, análise automática e CRUD completo nas três tabelas.",
      CYAN, title_size=14, body_size=14)

# ================================================================ telas (capturas)
s = prs.slides.add_slide(BLANK)
_navy_bg(s)
_watermark(s)
_text(s, 0.6, 0.4, 12, 0.7, "Dados (CRUD) e Visão Geral", size=28, color=WHITE, bold=True)
_shape(s, MSO_SHAPE.RECTANGLE, 0.65, 1.15, 2.2, 0.06, fill=CYAN)
_shot(s, os.path.join(IMGS, "rotas.png"), 0.9, 2.1, 3.4, "Rotas (cadastrar / editar / excluir)")
_shot(s, os.path.join(IMGS, "dashboard.png"), 4.9, 1.4, 7.8, "Visão Geral: score + estatísticas")
_footer(s, 11)

s = prs.slides.add_slide(BLANK)
_navy_bg(s)
_watermark(s)
_text(s, 0.6, 0.4, 12, 0.7, "Leituras e Eventos de Risco", size=28, color=WHITE, bold=True)
_shape(s, MSO_SHAPE.RECTANGLE, 0.65, 1.15, 2.2, 0.06, fill=CYAN)
_shot(s, os.path.join(IMGS, "leituras.png"), 0.55, 1.5, 5.9, "Leituras (frames de telemetria)")
_shot(s, os.path.join(IMGS, "eventos.png"), 6.9, 1.5, 5.9, "Eventos de risco (filtro por tipo)")
_footer(s, 12)

s = prs.slides.add_slide(BLANK)
_navy_bg(s)
_watermark(s)
_text(s, 0.6, 0.4, 12, 0.7, "Sensores e Gráfico", size=28, color=WHITE, bold=True)
_shape(s, MSO_SHAPE.RECTANGLE, 0.65, 1.15, 2.2, 0.06, fill=CYAN)
_shot(s, os.path.join(IMGS, "sensores.png"), 0.55, 1.5, 5.9, "Análise por sensor (% fora do limiar)")
_shot(s, os.path.join(IMGS, "grafico.png"), 6.9, 1.5, 5.9, "Gráfico em painel (velocidade, Força G, RPM)")
_footer(s, 13)

# ================================================================ 11. DEMONSTRAÇÃO
s = _content_slide(9, "Demonstração do Funcionamento", accent=ORANGE, page=14)
demos = [
    ("Cadastro em lote", "Arquivos CSV importados e padronizados como rotas.", BLUE),
    ("CRUD completo", "Criar/ler/editar/excluir rotas, leituras e eventos.", PURPLE),
    ("Regras de negócio", "Ex.: leitura de rota inexistente, leitura duplicada.", TEAL),
    ("Análise + classificações", "6 tipos de evento detectados pelos 3 métodos.", ORANGE),
    ("Dashboard, sensores e score", "Score 0–100, gráfico, análise por sensor e comparação.", RED),
]
y = 1.7
for titulo, texto, cor in demos:
    _card(s, 0.6, y, 12.1, 0.82, titulo, texto, cor, title_size=14, body_size=13.5)
    y += 1.02

# ================================================================ 12. DIFICULDADES
s = _content_slide(10, "Principais Dificuldades", accent=RED, page=15)
difs = [
    ("Padronização de parâmetros", "Fontes diferentes nomeiam a mesma grandeza de formas distintas.", BLUE),
    ("Performance na análise", "Commit por evento expirava os objetos do SQLAlchemy — resolvido com commit em lote.", PURPLE),
    ("Compatibilidade de versões", "flask-apispec é incompatível com marshmallow 4.x.", TEAL),
    ("Modelo de ML", "DBSCAN + RandomForest exigem quantidade mínima de amostras no histórico.", ORANGE),
]
y = 1.7
for titulo, texto, cor in difs:
    _card(s, 0.6, y, 12.1, 1.05, titulo, texto, cor, title_size=14.5, body_size=13)
    y += 1.25

# ================================================================ 13. OBRIGADO
slide = prs.slides.add_slide(BLANK)
_navy_bg(slide, subtle=False)
_watermark(slide, x=7.9, y=4.85, w=4.9)
_text(slide, 0.6, 2.5, 12.1, 1.5, "Obrigado!", size=58, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
_shape(slide, MSO_SHAPE.RECTANGLE, 5.66, 4.15, 2.0, 0.08, fill=CYAN)
_text(slide, 0.6, 4.55, 12.1, 0.8, "Perguntas?", size=24, color=SOFT, align=PP_ALIGN.CENTER)
_text(slide, 0.6, 6.6, 12.1, 0.5, "Sentinela — Telemetria e Segurança Veicular  •  João Maurício Araújo Leitão",
      size=13, color=TEXT_DIM, align=PP_ALIGN.CENTER)

nome_saida = sys.argv[1] if len(sys.argv) > 1 else "slides_pav.pptx"
prs.save(nome_saida)
print(f"Slides gerados: {nome_saida}")
