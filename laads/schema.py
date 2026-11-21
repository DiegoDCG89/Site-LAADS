"""Descreve TUDO o que é editável no site.

O painel (/admin) e as abas da planilha são gerados a partir deste arquivo:
- `GROUPS`      -> textos/configurações soltas, guardados na aba `config` (chave | valor)
- `COLLECTIONS` -> listas (eventos, parceiros...), uma aba por coleção
- `INBOXES`     -> formulários recebidos (inscrições, mensagens)

Para criar um campo novo: adicione um `F(...)` aqui, use `site.cfg.<chave>` no template e pronto.
O valor padrão (`d=`) é o conteúdo do site original e vale enquanto a planilha não tiver o campo.
"""
from __future__ import annotations

from dataclasses import dataclass

from .legal_defaults import PRIVACY_DEFAULT, TERMS_DEFAULT

CONFIG_TAB = "config"
CONFIG_HEADERS = ["chave", "valor", "descricao"]


@dataclass(frozen=True)
class F:
    key: str
    label: str
    type: str = "text"  # text | textarea | url | bool | number | select | icon | image
    d: str = ""  # valor padrão
    help: str = ""
    required: bool = False
    maxlength: int = 200
    options: tuple[str, ...] = ()
    placeholder: str = ""


@dataclass(frozen=True)
class Group:
    id: str
    title: str
    icon: str
    desc: str
    fields: tuple[F, ...]


@dataclass(frozen=True)
class Collection:
    id: str  # também é o nome da aba na planilha
    title: str
    singular: str
    icon: str
    desc: str
    fields: tuple[F, ...]
    label_key: str  # campo usado como título na listagem
    meta_keys: tuple[str, ...] = ()  # campos exibidos em cinza abaixo do título
    image_key: str = ""  # campo de imagem exibido como miniatura na listagem
    kind: str = "list"  # list | inbox
    gender: str = "m"  # m/f: concordância nos textos do painel ("novo"/"nova")

    @property
    def headers(self) -> list[str]:
        if self.kind == "inbox":
            return ["id"] + [f.key for f in self.fields]
        return ["id", "ordem", "ativo"] + [f.key for f in self.fields]

    def field(self, key: str) -> F | None:
        return next((f for f in self.fields if f.key == key), None)


# --------------------------------------------------------------------------- #
# Textos e configurações (aba `config`)
# --------------------------------------------------------------------------- #

GROUPS: tuple[Group, ...] = (
    Group(
        "geral", "Geral e SEO", "settings",
        "Marca, título da aba do navegador, descrição para o Google e textos fixos das laterais do site.",
        (
            F("brand_prefix", "Logo: parte branca", d="LA", maxlength=12, required=True,
              help="Aparece no canto superior esquerdo. Ex.: LA"),
            F("brand_suffix", "Logo: parte colorida", d="ADS", maxlength=12, required=True,
              help="Parte com degradê do logo. Ex.: ADS"),
            F("site_title", "Título da página", d="LaADS — Liga Acadêmica de Análise e Desenvolvimento de Sistemas",
              maxlength=90, help="Aparece na aba do navegador e nos resultados do Google."),
            F("site_description", "Descrição para buscadores e redes sociais", "textarea",
              d="Eventos, mentoria, projetos e parcerias para quem constrói o futuro em código.", maxlength=200),
            F("og_image", "Imagem de compartilhamento", "image",
              help="Prévia ao compartilhar o link no WhatsApp, Instagram e LinkedIn. Ideal: 1200×630 px. "
                   "Em branco, usa a imagem do topo do site."),
            F("nav_status", "Status no menu", d="online", maxlength=20),
            F("rail_left", "Lateral esquerda (texto vertical)", d="laads://liga-academica", maxlength=40,
              help="Visível em telas largas."),
            F("rail_status", "Lateral direita: status", d="sistema online", maxlength=30),
            F("rail_version", "Lateral direita: versão", d="v.2026.11", maxlength=20),
            F("fx_boot", "Animação de abertura (boot)", "bool", d="SIM",
              help="Tela rápida de carregamento estilo terminal ao abrir o site."),
        ),
    ),
    Group(
        "menu", "Menu e seções", "menu",
        "Renomeie os itens do menu e escolha quais seções aparecem no site. Seção desligada some do menu e da página.",
        (
            F("nav_eventos", "Menu: Eventos", d="Eventos", maxlength=24),
            F("sec_eventos", "Mostrar seção Eventos", "bool", d="SIM"),
            F("nav_facaparte", "Menu: Faça parte", d="Faça parte", maxlength=24),
            F("sec_facaparte", "Mostrar seção Faça parte", "bool", d="SIM"),
            F("nav_quemsomos", "Menu: Quem somos", d="Quem Somos", maxlength=24),
            F("sec_quemsomos", "Mostrar seção Quem somos", "bool", d="SIM"),
            F("nav_parcerias", "Menu: Parcerias", d="Parcerias", maxlength=24),
            F("sec_parcerias", "Mostrar seção Parcerias", "bool", d="SIM"),
            F("nav_contato", "Menu: Contato", d="Contato", maxlength=24),
            F("sec_contato", "Mostrar seção Contato", "bool", d="SIM"),
        ),
    ),
    Group(
        "hero", "Topo do site", "rocket",
        "A primeira tela: título, texto de apoio, botões e imagem de fundo.",
        (
            F("hero_image", "Imagem de fundo", "image",
              help="Ideal: 1920×1080 px, tons escuros (o site aplica uma camada escura por cima). "
                   "Em branco, usa a imagem original."),
            F("hero_chip", "Selo", d="turma 2026 · aberto", maxlength=40),
            F("hero_typing", "Texto digitando ao lado do selo", d="sistema.iniciar( turma )", maxlength=50),
            F("hero_line1", "Título, linha 1 (com efeito glitch)", d="CONSTRUA", maxlength=30, required=True),
            F("hero_line2", "Título, linha 2", d="O FUTURO", maxlength=30),
            F("hero_line3", "Título, linha 3", d="EM CÓDIGO.", maxlength=30),
            F("hero_text", "Texto de apoio", "textarea", maxlength=320,
              d="Liga Acadêmica de Análise e Desenvolvimento de Sistemas. Projetos reais, mentoria e conexão "
                "direta com o mercado — construído por estudantes, para estudantes."),
            F("hero_cta1_label", "Botão principal: texto", d="Quero fazer parte", maxlength=30),
            F("hero_cta1_link", "Botão principal: link", "url", d="#faca-parte",
              help="Use #eventos, #contato... para rolar a página, ou um endereço https://."),
            F("hero_cta2_label", "Botão secundário: texto", d="Ver próximos eventos", maxlength=30),
            F("hero_cta2_link", "Botão secundário: link", "url", d="#eventos"),
        ),
    ),
    Group(
        "eventos", "Textos da seção Eventos", "calendar",
        "Cabeçalho da seção. Os eventos em si ficam em Eventos > Lista de eventos.",
        (
            F("ev_eyebrow", "Linha pequena acima do título", d="eventos.listar()", maxlength=40),
            F("ev_title", "Título", d="Próximos eventos", maxlength=60, required=True),
            F("ev_desc", "Descrição", "textarea", maxlength=240,
              d="Encontros, workshops, palestras e maratonas de código criados por estudantes e para estudantes."),
            F("ev_cta", "Texto do link em cada evento", d="inscrever →", maxlength=24),
            F("ev_empty", "Mensagem quando não há eventos", d="Nenhum evento agendado por enquanto. Volte em breve!",
              maxlength=120),
        ),
    ),
    Group(
        "facaparte", "Textos da seção Faça parte", "users",
        "Cabeçalho, aviso e formulário de inscrição. Benefícios e squads ficam nas listas abaixo.",
        (
            F("fp_eyebrow", "Linha pequena acima do título", d="liga.inscrever( voce )", maxlength=40),
            F("fp_title", "Título", d="Faça parte da LaADS", maxlength=60, required=True),
            F("fp_desc", "Descrição", d="Aqui, todo mundo tem espaço para aprender.", maxlength=240),
            F("fp_notice", "Aviso destacado", d="Sem taxa de inscrição. Vagas abertas para todos os períodos de ADS.",
              maxlength=160),
            F("fp_form_eyebrow", "Formulário: linha pequena", d="liga.formulario_de_inscricao()", maxlength=50),
            F("fp_form_title", "Formulário: título", d="Inscreva-se agora", maxlength=60),
            F("fp_form_button", "Formulário: texto do botão", d="Enviar inscrição", maxlength=30),
            F("fp_success", "Mensagem de sucesso", d="enviado com sucesso. Entraremos em contato!", maxlength=120),
        ),
    ),
    Group(
        "quemsomos", "Textos da seção Quem somos", "heart",
        "Texto institucional. Números e Missão/Visão/Valores ficam nas listas abaixo.",
        (
            F("qs_eyebrow", "Linha pequena acima do título", d="liga.sobre()", maxlength=40),
            F("qs_title", "Título", d="Quem somos", maxlength=60, required=True),
            F("qs_desc", "Descrição", d="De estudantes para estudantes.", maxlength=240),
            F("qs_text", "Texto", "textarea", maxlength=1500,
              help="Separe os parágrafos com uma linha em branco.",
              d="A LaADS nasceu da vontade de transformar o aprendizado em algo que vai além da sala de aula: "
                "aprender fazendo, construindo projetos e enfrentando desafios reais.\n\n"
                "Hoje, somos uma comunidade que conecta academia, mercado e prática, transformando ideias em "
                "projetos que geram impacto dentro e fora da faculdade."),
        ),
    ),
    Group(
        "parcerias", "Textos da seção Parcerias", "handshake",
        "Cabeçalho e chamada para novos parceiros. Os logos ficam em Parcerias > Parceiros.",
        (
            F("pc_eyebrow", "Linha pequena acima do título", d="parcerias.conectar()", maxlength=40),
            F("pc_title", "Título", d="Parcerias", maxlength=60, required=True),
            F("pc_desc", "Descrição", maxlength=240),
            F("pc_cta_title", "Chamada: título", d="Quer apoiar a próxima geração de desenvolvedores?", maxlength=100),
            F("pc_cta_text", "Chamada: texto", d="Fale com a coordenação sobre formatos de parceria e patrocínio.",
              maxlength=200),
            F("pc_cta_label", "Chamada: texto do botão", d="Ser parceiro", maxlength=30),
            F("pc_cta_link", "Chamada: link do botão", "url", d="#contato"),
        ),
    ),
    Group(
        "contato", "Textos da seção Contato", "mail",
        "Cabeçalho e formulário de contato. Os canais (e-mail, Instagram...) ficam na lista abaixo.",
        (
            F("ct_eyebrow", "Linha pequena acima do título", d="contato.enviar()", maxlength=40),
            F("ct_title", "Título", d="Fale com a gente", maxlength=60, required=True),
            F("ct_desc", "Descrição", d="Dúvidas sobre inscrição, eventos ou parcerias? Use um dos canais abaixo.",
              maxlength=240),
            F("ct_form_eyebrow", "Formulário: linha pequena", d="mensagem.nova()", maxlength=50),
            F("ct_form_title", "Formulário: título", d="Envie uma mensagem", maxlength=60),
            F("ct_form_button", "Formulário: texto do botão", d="Enviar mensagem", maxlength=30),
            F("ct_success", "Mensagem de sucesso", d="enviado com sucesso. Entraremos em contato!", maxlength=120),
        ),
    ),
    Group(
        "legal", "Privacidade e Termos", "shield-check",
        "Textos das páginas /privacidade e /termos (LGPD). Os marcadores {entidade} e {email} são trocados pelos "
        "dados abaixo. Formatação: ## Título, listas com - item, **negrito**, [texto](link). "
        "Modelo genérico: peça revisão jurídica da sua instituição.",
        (
            F("legal_entity", "Nome da entidade responsável", d="LaADS — Liga Acadêmica de Análise e Desenvolvimento de Sistemas",
              maxlength=140, required=True, help="Vira o {entidade} nos textos."),
            F("legal_email", "E-mail para assuntos de privacidade", d="contato@laads.edu.br", maxlength=120,
              required=True, help="Vira o {email} nos textos. É o canal para o titular exercer seus direitos."),
            F("legal_updated", "Data da última atualização", d="21 de novembro de 2026", maxlength=40,
              help="Atualize sempre que alterar os textos."),
            F("privacy_text", "Política de Privacidade", "textarea", d=PRIVACY_DEFAULT, maxlength=20000),
            F("terms_text", "Termos de Uso", "textarea", d=TERMS_DEFAULT, maxlength=20000),
        ),
    ),
    Group(
        "rodape", "Rodapé", "layout-dashboard",
        "Os três textos da base do site.",
        (
            F("footer_left", "Texto da esquerda",
              d="LaADS © 2026 · Liga Acadêmica de Análise e Desenvolvimento de Sistemas", maxlength=140),
            F("footer_mid", "Texto do centro", d="feito por estudantes, para estudantes.", maxlength=80),
            F("footer_top", "Link de voltar ao topo", d="voltar ao topo", maxlength=30),
        ),
    ),
)

# --------------------------------------------------------------------------- #
# Listas (uma aba por coleção)
# --------------------------------------------------------------------------- #

COLLECTIONS: tuple[Collection, ...] = (
    Collection(
        "eventos", "Lista de eventos", "evento", "calendar-days",
        "Cada evento vira um card na seção Eventos. A ordem aqui é a ordem no site.",
        (
            F("data", "Data (como aparece no card)", required=True, maxlength=14, placeholder="05 DEZ"),
            F("tipo", "Tipo", maxlength=24, placeholder="Workshop"),
            F("titulo", "Título", required=True, maxlength=120),
            F("local", "Local e horário", maxlength=80, placeholder="Lab 3 · 19h"),
            F("vagas", "Vagas", maxlength=30, placeholder="32 vagas"),
            F("link", "Link do botão de inscrição", "url", maxlength=300,
              help="Em branco, leva para o formulário de inscrição da própria página."),
            F("imagem", "Imagem de capa (opcional)", "image", help="Aparece no topo do card. Ideal: 1200×675 px."),
        ),
        label_key="titulo", meta_keys=("data", "tipo", "local"), image_key="imagem",
    ),
    Collection(
        "stats_hero", "Números do topo", "número", "chart-no-axes-column",
        "Os três números abaixo dos botões do topo. Ex.: 180+ membros.",
        (
            F("valor", "Número", required=True, maxlength=12, placeholder="180+"),
            F("rotulo", "Legenda", required=True, maxlength=24, placeholder="membros"),
        ),
        label_key="valor", meta_keys=("rotulo",),
    ),
    Collection(
        "ticker", "Faixa de palavras", "palavra", "radio",
        "A faixa de palavras que rola na base do topo.",
        (F("texto", "Palavra ou expressão", required=True, maxlength=30, placeholder="front-end"),),
        label_key="texto", gender="f",
    ),
    Collection(
        "beneficios", "Benefícios", "benefício", "award",
        "Os cartões numerados ao lado do formulário de inscrição.",
        (
            F("icone", "Ícone", "icon", d="code-xml"),
            F("texto", "Texto", "textarea", required=True, maxlength=200),
        ),
        label_key="texto", meta_keys=("icone",),
    ),
    Collection(
        "squads", "Squads", "squad", "users",
        "Opções do campo “squad” no formulário de inscrição.",
        (F("nome", "Nome do squad", required=True, maxlength=40, placeholder="Front-end"),),
        label_key="nome",
    ),
    Collection(
        "pilares", "Missão, Visão e Valores", "cartão", "target",
        "Os cartões de destaque abaixo do texto institucional.",
        (
            F("icone", "Ícone", "icon", d="target"),
            F("titulo", "Título", required=True, maxlength=40),
            F("texto", "Texto", "textarea", required=True, maxlength=300),
        ),
        label_key="titulo", meta_keys=("icone",),
    ),
    Collection(
        "parceiros", "Parceiros", "parceiro", "building-2",
        "Logos exibidos na seção Parcerias. Sem parceiros cadastrados, a grade não aparece.",
        (
            F("nome", "Nome", required=True, maxlength=60),
            F("logo", "Logo", "image", required=True,
              help="PNG com fundo transparente funciona melhor. Ideal: largura entre 300 e 600 px."),
            F("link", "Site do parceiro", "url", maxlength=300),
        ),
        label_key="nome", meta_keys=("link",), image_key="logo",
    ),
    Collection(
        "contatos", "Canais de contato", "canal", "phone",
        "Os cartões de contato (e-mail, Instagram, endereço...).",
        (
            F("icone", "Ícone", "icon", d="mail"),
            F("rotulo", "Rótulo", required=True, maxlength=24, placeholder="e-mail"),
            F("valor", "Texto exibido", required=True, maxlength=100, placeholder="contato@laads.edu.br"),
            F("link", "Link (opcional)", "url", maxlength=300,
              help="Ex.: mailto:contato@laads.edu.br, https://instagram.com/la.ads, https://wa.me/55..."),
        ),
        label_key="valor", meta_keys=("rotulo",),
    ),
)

# --------------------------------------------------------------------------- #
# Caixas de entrada (formulários do site)
# --------------------------------------------------------------------------- #

INBOXES: tuple[Collection, ...] = (
    Collection(
        "inscricoes", "Inscrições", "inscrição", "send",
        "Pessoas que preencheram o formulário “Faça parte”.",
        (
            F("data_hora", "Recebido em"),
            F("nome", "Nome"),
            F("periodo", "Período"),
            F("telefone", "Telefone"),
            F("email", "E-mail"),
            F("squad", "Squad"),
            F("mensagem", "Mensagem"),
            F("status", "Status"),
        ),
        label_key="nome", kind="inbox", gender="f",
    ),
    Collection(
        "mensagens", "Mensagens", "mensagem", "message-circle",
        "Mensagens enviadas pelo formulário de contato.",
        (
            F("data_hora", "Recebido em"),
            F("nome", "Nome"),
            F("email", "E-mail"),
            F("mensagem", "Mensagem"),
            F("status", "Status"),
        ),
        label_key="nome", kind="inbox", gender="f",
    ),
)

# --------------------------------------------------------------------------- #
# Menu lateral do painel: (título da seção, [(tipo, id, rótulo)])
# --------------------------------------------------------------------------- #

ADMIN_MENU: tuple[tuple[str, tuple[tuple[str, str, str], ...]], ...] = (
    ("Site", (("group", "geral", "Geral e SEO"), ("group", "menu", "Menu e seções"))),
    ("Topo", (
        ("group", "hero", "Textos e imagem"),
        ("list", "stats_hero", "Números"),
        ("list", "ticker", "Faixa de palavras"),
    )),
    ("Eventos", (("group", "eventos", "Textos da seção"), ("list", "eventos", "Lista de eventos"))),
    ("Faça parte", (
        ("group", "facaparte", "Textos e formulário"),
        ("list", "beneficios", "Benefícios"),
        ("list", "squads", "Squads"),
    )),
    ("Quem somos", (
        ("group", "quemsomos", "Textos"),
        ("list", "pilares", "Missão, Visão, Valores"),
    )),
    ("Parcerias", (("group", "parcerias", "Textos e chamada"), ("list", "parceiros", "Parceiros"))),
    ("Contato", (("group", "contato", "Textos e formulário"), ("list", "contatos", "Canais"))),
    ("Rodapé e páginas legais", (("group", "rodape", "Textos do rodapé"), ("group", "legal", "Privacidade e Termos"))),
    ("Recebidos", (("inbox", "inscricoes", "Inscrições"), ("inbox", "mensagens", "Mensagens"))),
    ("Arquivos", (("media", "midia", "Biblioteca de imagens"),)),
)

GROUP_BY_ID = {g.id: g for g in GROUPS}
COLLECTION_BY_ID = {c.id: c for c in COLLECTIONS}
INBOX_BY_ID = {c.id: c for c in INBOXES}
ALL_FIELDS = {f.key: f for g in GROUPS for f in g.fields}

ALL_TABS = [CONFIG_TAB] + [c.id for c in COLLECTIONS] + [c.id for c in INBOXES]

TRUE_WORDS = {"sim", "true", "1", "yes", "y", "verdadeiro", "x", "s", "on"}
FALSE_WORDS = {"não", "nao", "false", "0", "no", "n", "falso", "off"}


def to_bool(value: object, default: bool = True) -> bool:
    """Interpreta células de planilha como booleano. Vazio/desconhecido = `default`."""
    v = str(value if value is not None else "").strip().lower()
    if v in TRUE_WORDS:
        return True
    if v in FALSE_WORDS:
        return False
    return default
