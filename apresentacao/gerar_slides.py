"""Gera os slides da apresentação (Parte 6) em formato PowerPoint (.pptx).

Tema único (dark/navy) em todos os slides, igual à capa e ao encerramento.
Domínio: telemetria veicular (OBD-II) e detecção de eventos de risco.

Executar:  python gerar_slides.py
Saída:     slides_pav.pptx
"""
import sys

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

# ---------------------------------------------------------------- paleta
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
    _shape(slide, MSO_SHAPE.RECTANGLE, 0, 0, 13.333, 7.5, fill=NAVY)
    _shape(slide, MSO_SHAPE.OVAL, 11.3, -2.6, 5.6, 5.6, fill=NAVY_2)
    if subtle:
        _shape(slide, MSO_SHAPE.OVAL, -2.5, 5.7, 4.4, 4.4, fill=NAVY_2)
    else:
        _shape(slide, MSO_SHAPE.OVAL, 11.0, 5.0, 4.6, 4.6, fill=NAVY_3)
        _shape(slide, MSO_SHAPE.OVAL, -2.0, 5.4, 5.0, 5.0, fill=NAVY_2)


def _footer(slide, page):
    _shape(slide, MSO_SHAPE.RECTANGLE, 0.6, 7.05, 12.13, 0.012, fill=NAVY_3)
    _text(slide, 0.6, 7.13, 8, 0.3, "Telemetria Veicular — Detecção de Eventos de Risco",
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


# ================================================================ 1. CAPA
slide = prs.slides.add_slide(BLANK)
_navy_bg(slide, subtle=False)
chip = _shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, 1.0, 1.35, 3.6, 0.55, fill=NAVY_3, radius=0.5)
_shape_text(chip, "TRABALHO PAV  •  PROGRAMAÇÃO DE APLICAÇÕES", size=11, color=CYAN, bold=True)
_text(slide, 1.0, 2.05, 11.3, 1.9, "Telemetria Veicular\n(OBD-II)",
      size=52, color=WHITE, bold=True)
_shape(slide, MSO_SHAPE.RECTANGLE, 1.05, 4.2, 2.6, 0.09, fill=CYAN)
_text(slide, 1.0, 4.55, 10.5, 1.0,
      "Detecção de eventos de risco na condução com padronização de parâmetros e Machine Learning",
      size=20, color=SOFT)
_shape(slide, MSO_SHAPE.OVAL, 1.0, 6.35, 0.42, 0.42, fill=BLUE)
_text(slide, 1.6, 6.42, 7, 0.35, "João Maurício Araújo Leitão", size=15, color=WHITE, bold=True)

# ================================================================ 2. CONTEXTO
s = _content_slide(1, "Contexto do Sistema", accent=BLUE, page=2)
_cards = [
    ("Receber", "Dados de telemetria veicular coletados pela interface OBD-II.", BLUE),
    ("Padronizar", "Normaliza nomes de colunas de fontes diferentes para parâmetros canônicos.", PURPLE),
    ("Armazenar", "Persistência em PostgreSQL (5 tabelas relacionadas).", TEAL),
    ("Analisar", "Detecção de eventos de risco com DBSCAN e RandomForest.", ORANGE),
]
x, y = 0.6, 1.75
for titulo, texto, cor in _cards:
    _card(s, x, y, 6.0, 1.05, titulo, texto, cor)
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
    ("Fontes heterogêneas", "Arquivos de ferramentas diferentes usam nomes distintos para a mesma grandeza.", ORANGE),
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
    ("veiculo", "identificador (único)\nmodelo", BLUE),
    ("parametro", "nome (canônico)\nunidade\nlimites", PURPLE),
    ("mapeamento_parametro", "nome bruto\n→ parâmetro", ORANGE),
    ("leitura", "velocidade, rpm\naccel_x/y/z\ndata_hora", TEAL),
    ("evento_risco", "força_g\ninstabilidade\nmétodo", RED),
]
x = 0.5
for nome, campos, cor in entidades:
    box = _shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x, 2.0, 2.35, 2.1, fill=CARD, radius=0.08)
    _shape(s, MSO_SHAPE.RECTANGLE, x, 2.0, 2.35, 0.5, fill=cor)
    _text(s, x, 2.06, 2.35, 0.4, nome, size=13, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    _text(s, x + 0.18, 2.66, 2.0, 1.4, campos, size=12, color=TEXT)
    x += 2.53
_text(s, 0.5, 4.5, 12.3, 0.6,
      "Parametro 1─N MapeamentoParametro   •   Veiculo 1─N Leitura 1─N EventoRisco",
      size=14, color=TEXT_DIM, align=PP_ALIGN.CENTER)
_card(s, 0.5, 5.5, 12.3, 1.2, "Padronização de parâmetros",
      "'Vehicle speed (km/h)' e 'Velocidade do veículo (km/h)' → ambos mapeados para 'velocidade'.",
      CYAN, title_size=14, body_size=14)

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
    ("LimiteDetector", "Força G > limiar", BLUE),
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
    ("features", "Força G resultante e instabilidade (janela de 3 s).", BLUE),
    ("AnaliseService", "Orquestra os detectores e registra os eventos.", ORANGE),
]
y = 4.6
for titulo, texto, cor in _cards2:
    _card(s, 0.6, y, 12.1, 0.75, titulo, texto, cor, title_size=13.5, body_size=12.5)
    y += 0.88

# ================================================================ 8. DETECÇÃO (extra)
s = _content_slide(None, "Detecção de Risco — 3 métodos", accent=RED, page=8)
metodos = [
    ("1", "LIMITE", "Força G resultante acima\ndo limiar físico de 0,5 g.", BLUE),
    ("2", "ESTATÍSTICO", "z-score (|z| > 3) da Força G\nem relação ao histórico\ndo veículo.", PURPLE),
    ("3", "MODELO_ML", "DBSCAN (pseudo-rótulos)\n+ RandomForest:\nclassifica eventos de risco.", TEAL),
]
x = 0.6
for num, nome, desc, cor in metodos:
    _shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x, 1.7, 3.9, 3.4, fill=CARD, radius=0.06)
    _badge(s, x + 0.25, 1.95, 0.6, num, color=cor)
    _text(s, x + 0.25, 2.75, 3.4, 0.6, nome, size=18, color=cor, bold=True)
    _text(s, x + 0.3, 3.4, 3.3, 1.6, desc, size=14, color=TEXT)
    x += 4.15
_text(s, 0.6, 5.45, 12.1, 0.9,
      "Força G resultante = √(ax² + ay² + az²) / 9,81   •   instabilidade = desvio padrão da aceleração (3 s).",
      size=15, color=TEXT_DIM, align=PP_ALIGN.CENTER)

# ================================================================ 9. ENDPOINTS
s = _content_slide(7, "Endpoints da API", accent=BLUE, page=9)
headers = ["Método", "Rota", "Descrição"]
rows = [
    ("GET / POST", "/telemetria/veiculos", "Listar / cadastrar veículos"),
    ("GET / PUT / DELETE", "/telemetria/veiculos/<id>", "Selecionar / editar / excluir"),
    ("GET", "/telemetria/veiculos/<id>/estatisticas", "Estatísticas de condução (regra 10)"),
    ("POST", "/telemetria/veiculos/<id>/analisar", "Detecção de eventos de risco (7, 8, 9)"),
    ("GET / POST", "/telemetria/parametros", "Listar / cadastrar parâmetros"),
    ("GET / POST", "/telemetria/mapeamentos", "Listar / cadastrar mapeamentos"),
    ("GET / POST", "/telemetria/leituras", "Listar / cadastrar leituras"),
    ("GET / POST", "/telemetria/eventos-risco", "Listar / cadastrar eventos"),
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
table.columns[0].width = Inches(2.4)
table.columns[1].width = Inches(4.5)
table.columns[2].width = Inches(5.2)

# ================================================================ 10. INTERFACE
s = _content_slide(8, "Interface Gráfica", accent=TEAL, page=10)
abas = [
    ("Veículos", "CRUD + estatísticas / analisar", BLUE),
    ("Parâmetros", "Catálogo canônico + limites", PURPLE),
    ("Mapeamentos", "Padronização de nomes", ORANGE),
    ("Leituras", "Frames de telemetria", TEAL),
    ("Eventos de Risco", "Consulta dos eventos detectados", RED),
]
x = 0.6
for i, (nome, desc, cor) in enumerate(abas):
    box = _shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x, 1.7, 2.35, 2.2, fill=CARD, radius=0.08)
    _shape(s, MSO_SHAPE.OVAL, x + 0.85, 1.95, 0.65, 0.65, fill=cor)
    _text(s, x + 0.15, 2.8, 2.05, 0.6, nome, size=14, color=WHITE, bold=True, align=PP_ALIGN.CENTER)
    _text(s, x + 0.15, 3.35, 2.05, 0.6, desc, size=10.5, color=TEXT_DIM, align=PP_ALIGN.CENTER)
    x += 2.48
_text(s, 0.6, 4.35, 12.1, 0.6,
      "Tkinter — projeto separado da API (roda fora do container).",
      size=15, color=TEXT, align=PP_ALIGN.CENTER)
_card(s, 0.6, 5.2, 12.1, 1.5, "Operações disponíveis por tela",
      "Cadastro  •  Busca  •  Edição  •  Exclusão  •  Listagem em tabela\n"
      "Botões especiais: Detectar Riscos e Estatísticas (na aba Veículos)",
      CYAN, title_size=14, body_size=14)

# ================================================================ 11. DEMONSTRAÇÃO
s = _content_slide(9, "Demonstração do Funcionamento", accent=ORANGE, page=11)
demos = [
    ("Importação real", "18.943 leituras de 4 veículos, padronizadas a partir dos CSVs.", BLUE),
    ("CRUD completo", "Cadastro, consulta, edição e exclusão em cada entidade.", PURPLE),
    ("Regras de negócio", "Ex.: veículo duplicado, leitura de veículo inexistente, frame duplicado.", TEAL),
    ("Análise", "532 eventos de risco detectados pelos 3 métodos.", ORANGE),
    ("Persistência", "Dados gravados no PostgreSQL (dentro do container).", RED),
]
y = 1.7
for titulo, texto, cor in demos:
    _card(s, 0.6, y, 12.1, 0.82, titulo, texto, cor, title_size=14, body_size=13.5)
    y += 1.02

# ================================================================ 12. DIFICULDADES
s = _content_slide(10, "Principais Dificuldades", accent=RED, page=12)
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
_text(slide, 0.6, 2.5, 12.1, 1.5, "Obrigado!", size=58, color=WHITE, bold=True,
      align=PP_ALIGN.CENTER)
_shape(slide, MSO_SHAPE.RECTANGLE, 5.66, 4.15, 2.0, 0.08, fill=CYAN)
_text(slide, 0.6, 4.55, 12.1, 0.8, "Perguntas?", size=24, color=SOFT, align=PP_ALIGN.CENTER)
_text(slide, 0.6, 6.6, 12.1, 0.5, "Telemetria Veicular (OBD-II)  •  João Maurício Araújo Leitão",
      size=13, color=TEXT_DIM, align=PP_ALIGN.CENTER)

nome_saida = sys.argv[1] if len(sys.argv) > 1 else "slides_pav.pptx"
prs.save(nome_saida)
print(f"Slides gerados: {nome_saida}")
