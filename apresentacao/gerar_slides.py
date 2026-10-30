"""Gera os slides da apresentação (Parte 6) em formato PowerPoint (.pptx).

Tema único (dark/navy) em todos os slides, igual à capa e ao encerramento.

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

# ---------------------------------------------------------------- paleta
NAVY = RGBColor(0x0D, 0x1B, 0x2A)      # fundo principal
NAVY_2 = RGBColor(0x17, 0x2A, 0x45)    # círculo decorativo / tom mais claro
NAVY_3 = RGBColor(0x1F, 0x3A, 0x5C)    # círculo decorativo / tom claro
CARD = RGBColor(0x14, 0x25, 0x3D)      # fundo dos cards
CARD_2 = RGBColor(0x1B, 0x30, 0x4C)    # fundo alternativo dos cards/tabela

BLUE = RGBColor(0x09, 0x84, 0xE3)
CYAN = RGBColor(0x00, 0xCE, 0xC9)
TEAL = RGBColor(0x00, 0xB8, 0x94)
PURPLE = RGBColor(0x6C, 0x5C, 0xE7)
ORANGE = RGBColor(0xE1, 0x70, 0x55)
RED = RGBColor(0xD6, 0x30, 0x31)
YELLOW = RGBColor(0xF3, 0x9C, 0x12)

WHITE = RGBColor(0xFF, 0xFF, 0xFF)
TEXT = RGBColor(0xDE, 0xE7, 0xF1)      # texto claro
TEXT_DIM = RGBColor(0x9B, 0xAD, 0xC4)  # texto secundário
SOFT = RGBColor(0xC9, 0xDA, 0xEC)      # subtítulo claro

FONT = "Segoe UI"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


# ---------------------------------------------------------------- helpers
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
    """Fundo navy com círculos decorativos (identidade da capa/encerramento)."""
    _shape(slide, MSO_SHAPE.RECTANGLE, 0, 0, 13.333, 7.5, fill=NAVY)
    _shape(slide, MSO_SHAPE.OVAL, 11.3, -2.6, 5.6, 5.6, fill=NAVY_2)
    if subtle:
        _shape(slide, MSO_SHAPE.OVAL, -2.5, 5.7, 4.4, 4.4, fill=NAVY_2)
    else:
        _shape(slide, MSO_SHAPE.OVAL, 11.0, 5.0, 4.6, 4.6, fill=NAVY_3)
        _shape(slide, MSO_SHAPE.OVAL, -2.0, 5.4, 5.0, 5.0, fill=NAVY_2)


def _footer(slide, page):
    _shape(slide, MSO_SHAPE.RECTANGLE, 0.6, 7.05, 12.13, 0.012, fill=NAVY_3)
    _text(slide, 0.6, 7.13, 8, 0.3, "Análise de Dados de Sensores IoT",
          size=10, color=TEXT_DIM)
    _text(slide, 11.6, 7.13, 1.13, 0.3, f"{page:02d}", size=11, color=TEXT_DIM,
          bold=True, align=PP_ALIGN.RIGHT)


def _content_slide(number, title, accent=CYAN, page=None):
    slide = prs.slides.add_slide(BLANK)
    _navy_bg(slide)
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


def _screenshot_slide(title, img1, cap1, img2, cap2, accent, page):
    slide = prs.slides.add_slide(BLANK)
    _navy_bg(slide)
    _text(slide, 0.6, 0.35, 12, 0.7, title, size=28, color=WHITE, bold=True)
    _shape(slide, MSO_SHAPE.RECTANGLE, 0.65, 1.12, 2.2, 0.06, fill=CYAN)

    for img, cap, x in [(img1, cap1, 0.55), (img2, cap2, 6.95)]:
        _shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x - 0.09, 1.42, 5.96, 3.92,
               fill=NAVY_3, line=NAVY_3, radius=0.03)
        slide.shapes.add_picture(img, Inches(x), Inches(1.5), width=Inches(5.78))
        _text(slide, x, 5.55, 5.78, 0.5, cap, size=13, color=SOFT, bold=True,
              align=PP_ALIGN.CENTER)
    _footer(slide, page)
    return slide


# ================================================================ 1. CAPA
slide = prs.slides.add_slide(BLANK)
_navy_bg(slide, subtle=False)

chip = _shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, 1.0, 1.35, 3.6, 0.55, fill=NAVY_3, radius=0.5)
_shape_text(chip, "TRABALHO PAV  •  PROGRAMAÇÃO DE APLICAÇÕES", size=11, color=CYAN, bold=True)

_text(slide, 1.0, 2.15, 11.3, 1.9, "Análise de Dados\nde Sensores IoT",
      size=54, color=WHITE, bold=True)
_shape(slide, MSO_SHAPE.RECTANGLE, 1.05, 4.35, 2.6, 0.09, fill=CYAN)
_text(slide, 1.0, 4.7, 10.5, 1.0,
      "Detecção de valores anormais com regras de negócio e Machine Learning",
      size=21, color=SOFT)

_shape(slide, MSO_SHAPE.OVAL, 1.0, 6.35, 0.42, 0.42, fill=BLUE)
_text(slide, 1.6, 6.42, 6, 0.35, "João Maurício Araújo Leitão",
      size=15, color=WHITE, bold=True)

# ================================================================ 2. CONTEXTO
s = _content_slide(1, "Contexto do Sistema", accent=BLUE, page=2)
_cards = [
    ("Receber", "Dados produzidos por sensores IoT chegam ao sistema para serem processados.", BLUE),
    ("Armazenar", "Persistência organizada em banco de dados PostgreSQL (4 tabelas relacionadas).", PURPLE),
    ("Consultar", "Leituras e anomalias podem ser consultadas via API REST e interface gráfica.", TEAL),
    ("Analisar", "Tratamento dos dados para identificar valores anormais (detecção de anomalias).", ORANGE),
]
x, y = 0.6, 1.75
for titulo, texto, cor in _cards:
    _card(s, x, y, 6.0, 1.05, titulo, texto, cor)
    y += 1.22
_text(s, 7.0, 1.85, 5.7, 5.0,
      "Aplicação completa em Python\n\n"
      "• Modalidade individual\n"
      "• Programação estruturada e orientada a objetos\n"
      "• Banco de dados PostgreSQL\n"
      "• API REST (Flask-RESTful)\n"
      "• Interface gráfica (Tkinter)\n"
      "• Machine Learning (scikit-learn)\n"
      "• Docker (containers)",
      size=16, color=TEXT)

# ================================================================ 3. PROBLEMA
s = _content_slide(2, "Problema que o Sistema Resolve", accent=PURPLE, page=3)
_problemas = [
    ("Volume de dados", "Sensores geram medições continuamente — é impossível analisar tudo manualmente.", BLUE),
    ("Falhas silenciosas", "Um sensor com defeito ou fora do padrão pode passar despercebido.", RED),
    ("Decisão lenta", "Sem automação, a identificação de anomalias é demorada e propensa a erros.", ORANGE),
]
x = 0.6
for titulo, texto, cor in _problemas:
    _card(s, x, 1.7, 3.9, 1.7, titulo, texto, cor, title_size=16)
    x += 4.15
arr = _shape(s, MSO_SHAPE.DOWN_ARROW, 6.05, 3.7, 1.2, 1.2, fill=TEAL)
_text(s, 0.6, 5.3, 12.1, 1.3,
      "Solução: o sistema automatiza a validação, o armazenamento, a análise estatística\n"
      "do histórico e a classificação por Machine Learning.",
      size=18, color=WHITE, bold=True, align=PP_ALIGN.CENTER)

# ================================================================ 4. REQUISITOS
s = _content_slide(3, "Requisitos Principais — 10 regras de negócio", accent=RED, page=4)
_regras = [
    ("Sensor com identificador único.", BLUE),
    ("Leitura exige sensor, valor e data/hora.", PURPLE),
    ("Leitura apenas para sensor cadastrado.", TEAL),
    ("Valor numérico e finito.", ORANGE),
    ("Sem leituras duplicadas.", RED),
    ("Limites mínimo/máximo por sensor.", YELLOW),
    ("Anomalia: fora dos limites ou desvio do histórico.", RED),
    ("Classificação pelo modelo de Machine Learning.", PURPLE),
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
    ("tipo_sensor", "nome (único)\nunidade\ndescrição", BLUE),
    ("sensor", "identificador (único)\ntipo_sensor_id\nlimite_min / max", PURPLE),
    ("leitura", "sensor_id\nvalor\ndata_hora\nclassificação", TEAL),
    ("anomalia", "leitura_id\nsensor_id\nvalor, data_hora\nmétodo", RED),
]
x = 0.7
for nome, campos, cor in entidades:
    box = _shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x, 2.0, 2.55, 2.3, fill=CARD, radius=0.08)
    _shape(s, MSO_SHAPE.RECTANGLE, x, 2.0, 2.55, 0.55, fill=cor)
    _text(s, x, 2.08, 2.55, 0.4, nome, size=14, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    _text(s, x + 0.2, 2.72, 2.15, 1.5, campos, size=12.5, color=TEXT)
    x += 2.55
    if nome != "anomalia":
        _text(s, x + 0.02, 2.95, 0.5, 0.4, "1 ⟶ N", size=13, color=TEXT_DIM, bold=True,
              align=PP_ALIGN.CENTER)
        x += 0.54
_text(s, 0.7, 4.75, 12, 0.6,
      "Relacionamentos: TipoSensor 1 ── N Sensor 1 ── N Leitura 1 ── N Anomalia",
      size=14, color=TEXT_DIM, align=PP_ALIGN.CENTER)
_card(s, 0.7, 5.55, 12, 1.1, "Restrições de integridade",
      "UNIQUE(identificador)  •  UNIQUE(sensor_id, valor, data_hora)  •  UNIQUE(leitura_id, método)",
      CYAN, title_size=14, body_size=14)

# ================================================================ 6. ARQUITETURA
s = _content_slide(5, "Arquitetura da Aplicação", accent=BLUE, page=6)
camadas = [
    ("entities", "Classes que mapeiam as tabelas (SQLAlchemy)", BLUE),
    ("repositories", "Operações no banco: SELECT / INSERT / UPDATE / DELETE", PURPLE),
    ("services", "Regras de negócio e análise (detecção + ML)", TEAL),
    ("controllers", "Recebem as requisições HTTP (Flask-RESTful)", ORANGE),
    ("routes", "Mapeamento das URLs", RED),
]
x = 0.5
for nome, desc, cor in camadas:
    sp = _shape(s, MSO_SHAPE.CHEVRON, x, 2.15, 2.75, 1.6, fill=cor)
    _shape_text(sp, nome, size=15, color=WHITE, bold=True)
    _text(s, x + 0.25, 3.85, 2.35, 1.0, desc, size=11.5, color=TEXT_DIM, align=PP_ALIGN.CENTER)
    x += 2.55
_text(s, 0.5, 5.15, 12.3, 0.6,
      "Separação de responsabilidades em camadas — cada pacote tem um papel bem definido.",
      size=15, color=TEXT_DIM, align=PP_ALIGN.CENTER)
_card(s, 0.5, 5.85, 12.3, 0.9, "Fluxo de uma requisição",
      "HTTP → routes → controllers → services → repositories → entities → banco de dados",
      CYAN, title_size=13.5, body_size=14)

# ================================================================ 7. CLASSES
s = _content_slide(6, "Principais Classes", accent=PURPLE, page=7)
_text(s, 0.6, 1.5, 12, 0.5, "Herança e polimorfismo na detecção de anomalias:",
      size=16, color=WHITE, bold=True)

base = _shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 4.45, 1.95, 4.4, 0.7, fill=NAVY_3, radius=0.18)
_shape_text(base, "DetectorAnomalia  (classe abstrata)", size=14)
_shape(s, MSO_SHAPE.RECTANGLE, 6.62, 2.65, 0.06, 0.22, fill=TEXT_DIM)
_shape(s, MSO_SHAPE.RECTANGLE, 2.05, 2.85, 9.2, 0.05, fill=TEXT_DIM)

detectores = [
    ("LimiteDetector", "fora dos limites", BLUE),
    ("EstatisticoDetector", "z-score do histórico", PURPLE),
    ("ModeloMLDetector", "IsolationForest (ML)", TEAL),
]
xs = [0.7, 4.35, 8.0]
for (nome, desc, cor), x in zip(detectores, xs):
    _shape(s, MSO_SHAPE.RECTANGLE, x + 1.42, 2.9, 0.05, 0.22, fill=TEXT_DIM)
    box = _shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x, 3.12, 2.9, 0.7, fill=cor, radius=0.14)
    _shape_text(box, nome, size=13.5)
    _text(s, x + 0.1, 3.92, 2.7, 0.4, desc, size=11, color=TEXT_DIM, align=PP_ALIGN.CENTER)

_cards2 = [
    ("AnaliseService", "Orquestra a detecção, a classificação e as estatísticas.", TEAL),
    ("Entidades (ORM)", "TipoSensor, Sensor, Leitura e Anomalia.", BLUE),
    ("Services / Repositories", "Regras de negócio e persistência (encapsulamento).", ORANGE),
]
y = 4.6
for titulo, texto, cor in _cards2:
    _card(s, 0.6, y, 12.1, 0.75, titulo, texto, cor, title_size=13.5, body_size=12.5)
    y += 0.88

# ================================================================ 8. DETECÇÃO (extra)
s = _content_slide(None, "Detecção de Anomalias — 3 métodos", accent=RED, page=8)
metodos = [
    ("1", "LIMITE", "Valor fora dos limites\nmínimo e máximo\nde referência do sensor.", BLUE),
    ("2", "ESTATÍSTICO", "z-score (|z| > 3) em relação\nà média e ao desvio padrão\ndo histórico do sensor.", PURPLE),
    ("3", "MODELO_ML", "IsolationForest (scikit-learn)\ntreinado com o histórico:\nclassifica normal ou anômalo.", TEAL),
]
x = 0.6
for num, nome, desc, cor in metodos:
    _shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x, 1.7, 3.9, 3.4, fill=CARD, radius=0.06)
    _badge(s, x + 0.25, 1.95, 0.6, num, color=cor)
    _text(s, x + 0.25, 2.75, 3.4, 0.6, nome, size=18, color=cor, bold=True)
    _text(s, x + 0.3, 3.35, 3.3, 1.6, desc, size=14, color=TEXT)
    x += 4.15
_text(s, 0.6, 5.5, 12.1, 0.8,
      "Cada método gera um registro em 'anomalia' indicando o método utilizado na identificação.",
      size=15, color=TEXT_DIM, align=PP_ALIGN.CENTER)

# ================================================================ 9. ENDPOINTS
s = _content_slide(7, "Endpoints da API", accent=BLUE, page=9)
headers = ["Método", "Rota", "Descrição"]
rows = [
    ("GET / POST", "/iot/tipos-sensor", "Listar / cadastrar tipos de sensor"),
    ("GET / PUT / DELETE", "/iot/tipos-sensor/<id>", "Selecionar / editar / excluir"),
    ("GET / POST", "/iot/sensores", "Listar / cadastrar sensores"),
    ("GET / PUT / DELETE", "/iot/sensores/<id>", "Selecionar / editar / excluir"),
    ("GET", "/iot/sensores/<id>/estatisticas", "Análise histórica (regra 10)"),
    ("GET / POST", "/iot/leituras", "Listar / cadastrar leituras"),
    ("POST", "/iot/leituras/<id>/analisar", "Detecção de anomalias (regras 7 e 9)"),
    ("POST", "/iot/leituras/<id>/classificar", "Classificação por ML (regra 8)"),
    ("GET / POST", "/iot/anomalias", "Listar / cadastrar anomalias"),
]
n_rows = len(rows) + 1
gf = s.shapes.add_table(n_rows, 3, Inches(0.6), Inches(1.6), Inches(12.1), Inches(5.2))
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
table.columns[0].width = Inches(2.5)
table.columns[1].width = Inches(4.3)
table.columns[2].width = Inches(5.3)

# ================================================================ 10. INTERFACE
s = _content_slide(8, "Interface Gráfica", accent=TEAL, page=10)
abas = [
    ("Tipos de Sensor", "CRUD de tipos e unidades", BLUE),
    ("Sensores", "CRUD + estatísticas", PURPLE),
    ("Leituras", "CRUD + detectar / classificar", TEAL),
    ("Anomalias", "Consulta dos registros de anomalia", RED),
]
x = 0.6
for nome, desc, cor in abas:
    box = _shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x, 1.7, 2.9, 2.2, fill=CARD, radius=0.08)
    _shape(s, MSO_SHAPE.OVAL, x + 1.1, 1.95, 0.7, 0.7, fill=cor)
    _text(s, x + 0.15, 2.85, 2.6, 0.6, nome, size=15, color=WHITE, bold=True,
          align=PP_ALIGN.CENTER)
    _text(s, x + 0.15, 3.4, 2.6, 0.5, desc, size=11.5, color=TEXT_DIM, align=PP_ALIGN.CENTER)
    x += 3.08
_text(s, 0.6, 4.35, 12.1, 0.6,
      "Tkinter — projeto separado da API (roda fora do container).",
      size=15, color=TEXT, align=PP_ALIGN.CENTER)
_card(s, 0.6, 5.15, 12.1, 1.5, "Operações disponíveis por tela",
      "Cadastro  •  Busca  •  Edição  •  Exclusão  •  Listagem em tabela\n"
      "Tratamento de erros com mensagens claras (validação e comunicação com a API)",
      CYAN, title_size=14, body_size=14)

# ================================================================ telas (capturas)
_screenshot_slide("Telas do Sistema (1/2)",
                  os.path.join(IMGS, "tipos_sensor.png"), "Tela de Tipos de Sensor",
                  os.path.join(IMGS, "sensores.png"), "Tela de Sensores",
                  accent=TEAL, page=11)

_screenshot_slide("Telas do Sistema (2/2)",
                  os.path.join(IMGS, "leituras.png"), "Tela de Leituras",
                  os.path.join(IMGS, "anomalias.png"), "Tela de Anomalias",
                  accent=TEAL, page=12)

# ================================================================ 11. DEMONSTRAÇÃO
s = _content_slide(9, "Demonstração do Funcionamento", accent=ORANGE, page=13)
demos = [
    ("CRUD completo", "Cadastro, consulta, edição e exclusão em cada entidade.", BLUE),
    ("Regras de negócio", "Pelo menos 3 regras em ação (ex.: duplicidade, sensor inexistente).", PURPLE),
    ("Integração", "Comunicação entre interface gráfica e API REST.", TEAL),
    ("Persistência", "Dados gravados no PostgreSQL (dentro do container).", ORANGE),
    ("Análise", "Detecção de anomalias e classificação por Machine Learning.", RED),
]
y = 1.7
for titulo, texto, cor in demos:
    _card(s, 0.6, y, 12.1, 0.82, titulo, texto, cor, title_size=14, body_size=13.5)
    y += 1.02

# ================================================================ 12. DIFICULDADES
s = _content_slide(10, "Principais Dificuldades", accent=RED, page=14)
difs = [
    ("Compatibilidade de versões", "flask-apispec é incompatível com marshmallow 4.x — foi preciso fixar a versão 3.x.", BLUE),
    ("webargs 8", "O parâmetro 'location' deve ser string, não tupla — corrigido após os primeiros testes.", PURPLE),
    ("Configuração do ambiente", "Instalação do PostgreSQL e do Docker Desktop no Windows (WSL2).", TEAL),
    ("Modelo de ML", "O IsolationForest exige uma quantidade mínima de amostras no histórico.", ORANGE),
]
y = 1.7
for titulo, texto, cor in difs:
    _card(s, 0.6, y, 12.1, 1.05, titulo, texto, cor, title_size=14.5, body_size=13)
    y += 1.25

# ================================================================ 13. OBRIGADO
slide = prs.slides.add_slide(BLANK)
_navy_bg(slide, subtle=False)
_text(slide, 0.6, 2.5, 12.1, 1.5, "Obrigado!", size=58, color=WHITE, bold=True,
      align=PP_ALIGN.CENTER)
_shape(slide, MSO_SHAPE.RECTANGLE, 5.66, 4.15, 2.0, 0.08, fill=CYAN)
_text(slide, 0.6, 4.55, 12.1, 0.8, "Perguntas?", size=24, color=SOFT,
      align=PP_ALIGN.CENTER)
_text(slide, 0.6, 6.6, 12.1, 0.5, "Análise de Dados de Sensores IoT  •  João Maurício Araújo Leitão",
      size=13, color=TEXT_DIM, align=PP_ALIGN.CENTER)

nome_saida = sys.argv[1] if len(sys.argv) > 1 else "slides_pav.pptx"
prs.save(nome_saida)
print(f"Slides gerados: {nome_saida}")
