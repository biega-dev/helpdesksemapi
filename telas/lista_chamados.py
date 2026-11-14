import tkinter as tk
import unicodedata
from datetime import datetime
from tkinter import messagebox, ttk

from telas.componentes import PRIORIDADES, STATUS, data_formatada


def normalizar(texto):
    return "".join(letra for letra in unicodedata.normalize("NFD", texto.casefold())
                   if not unicodedata.combining(letra))


class ListaChamados(ttk.Frame):
    def __init__(self, pai, app):
        super().__init__(pai)
        self.app = app
        self.chamados = []
        self.usuario = app.servico.usuario.copy()
        corpo = ttk.Frame(self, padding=(24, 18))
        corpo.pack(fill="both", expand=True)
        linha = ttk.Frame(corpo)
        linha.pack(fill="x")
        titulo = "Meus chamados" if self.usuario['perfil'] == "Usuário Comum" else "Central de chamados"
        ttk.Label(linha, text=titulo, style="Titulo.TLabel").pack(side="left")
        if self.usuario['perfil'] == "Usuário Comum":
            from telas.chamados import NovoChamado
            ttk.Button(linha, text="+ Novo chamado", style="Principal.TButton",
                       command=lambda: app.abrir_dialogo(NovoChamado)).pack(side="right")
        elif self.usuario['perfil'] == "Administrador":
            from telas.usuarios import CadastroUsuario
            ttk.Button(linha, text="+ Cadastrar usuário", style="Principal.TButton",
                       command=lambda: app.abrir_dialogo(CadastroUsuario)).pack(side="right")
        orientacao = {
            "Usuário Comum": "Acompanhe suas solicitações e consulte o histórico de cada atendimento.",
            "Técnico de TI": "Confira a fila de chamados abertos e os atendimentos sob sua responsabilidade.",
            "Administrador": "Acompanhe os chamados da equipe e cadastre as contas de acesso.",
        }
        ttk.Label(corpo, text=orientacao.get(self.usuario['perfil'], ""),
                  style="Discreto.TLabel").pack(anchor="w", pady=(6, 18))
        resumo = ttk.Frame(corpo)
        resumo.pack(fill="x", pady=(0, 20))
        self.contadores = {}
        for coluna, (chave, rotulo, cor) in enumerate([
            ("total", "Total de chamados", "#172c4b"), ("ABERTO", "Abertos", "#2457c5"),
            ("andamento", "Em atendimento / pendentes", "#956018"), ("RESOLVIDO", "Resolvidos", "#21775b")]):
            resumo.columnconfigure(coluna, weight=1, uniform="cartoes")
            cartao = tk.Frame(resumo, background="white", padx=16, pady=12)
            cartao.grid(row=0, column=coluna, sticky="nsew", padx=(0, 8 if coluna < 3 else 0))
            valor = tk.StringVar(value="—")
            self.contadores[chave] = valor
            tk.Label(cartao, textvariable=valor, font=("Segoe UI", 24, "bold"),
                     foreground=cor, background="white").pack(anchor="w")
            tk.Label(cartao, text=rotulo, font=("Segoe UI", 9),
                     foreground="#526277", background="white").pack(anchor="w")
        filtros = ttk.Frame(corpo)
        filtros.pack(fill="x", pady=(0, 12))
        filtros.columnconfigure(0, weight=1)
        ttk.Label(filtros, text="Buscar por número, título ou pessoa").grid(row=0, column=0, sticky="w")
        self.busca = tk.StringVar()
        ttk.Entry(filtros, textvariable=self.busca).grid(row=1, column=0, sticky="ew", padx=(0, 12))
        self.filtro_status = tk.StringVar(value="Todos")
        self.filtro_prioridade = tk.StringVar(value="Todas")
        for coluna, (rotulo, variavel, valores) in enumerate([
            ("Status", self.filtro_status, ["Todos", *STATUS.values()]),
            ("Prioridade", self.filtro_prioridade, ["Todas", *PRIORIDADES.values()])], 1):
            ttk.Label(filtros, text=rotulo).grid(row=0, column=coluna, sticky="w")
            ttk.Combobox(filtros, textvariable=variavel, values=valores, state="readonly",
                         width=17).grid(row=1, column=coluna, sticky="ew", padx=(0, 12))
        ttk.Button(filtros, text="Atualizar", command=self.atualizar).grid(row=1, column=3)
        self.somente_meus = tk.BooleanVar()
        if self.usuario['perfil'] == "Técnico de TI":
            ttk.Checkbutton(corpo, text="Somente os chamados que assumi", variable=self.somente_meus,
                            command=self.filtrar).pack(anchor="w", pady=(0, 8))
        grade = ttk.Frame(corpo)
        grade.pack(fill="both", expand=True)
        grade.columnconfigure(0, weight=1)
        grade.rowconfigure(0, weight=1)
        colunas = [("id", "Nº", 55), ("titulo", "Título", 270), ("status", "Status", 135),
                   ("prioridade", "Prioridade", 90), ("solicitante", "Solicitante", 140),
                   ("responsavel", "Responsável", 140), ("data", "Abertura", 135)]
        self.tabela = ttk.Treeview(grade, columns=[c[0] for c in colunas], show="headings", selectmode="browse")
        for chave, nome, largura in colunas:
            self.tabela.heading(chave, text=nome)
            self.tabela.column(chave, width=largura, minwidth=largura if chave != "titulo" else 190,
                               stretch=chave == "titulo", anchor="w")
        self.tabela.tag_configure("alternada", background="#f5f8fc")
        self.tabela.grid(row=0, column=0, sticky="nsew")
        vertical = ttk.Scrollbar(grade, command=self.tabela.yview)
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal = ttk.Scrollbar(grade, orient="horizontal", command=self.tabela.xview)
        horizontal.grid(row=1, column=0, sticky="ew")
        self.tabela.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        self.tabela.bind("<Double-1>", lambda evento: self.abrir_selecionado())
        self.tabela.bind("<Return>", lambda evento: self.abrir_selecionado())
        rodape = ttk.Frame(corpo)
        rodape.pack(side='bottom', fill="x", pady=(12, 0), before=grade)
        self.informacao = tk.StringVar(value="Carregando chamados...")
        ttk.Label(rodape, textvariable=self.informacao, style="Discreto.TLabel").pack(side="left")
        ttk.Button(rodape, text="Ver chamado", command=self.abrir_selecionado).pack(side="right")
        self.observadores = []
        for variavel in (self.busca, self.filtro_status, self.filtro_prioridade):
            identificador = variavel.trace_add("write", lambda *args: self.filtrar())
            self.observadores.append((variavel, identificador))
        self.ultima_atualizacao = ""

    def atualizar(self, silencioso=False):
        return self.app.executar(self.app.servico.listar_chamados, self.receber_chamados, silencioso=silencioso)

    def receber_chamados(self, chamados):
        if not self.winfo_exists():
            return
        self.chamados = chamados
        self.ultima_atualizacao = datetime.now().strftime("%H:%M:%S")
        self.contadores['total'].set(len(chamados))
        self.contadores['ABERTO'].set(sum(c['status'] == 'ABERTO' for c in chamados))
        self.contadores['andamento'].set(sum(c['status'] in ('EM_ATENDIMENTO', 'PENDENTE') for c in chamados))
        self.contadores['RESOLVIDO'].set(sum(c['status'] == 'RESOLVIDO' for c in chamados))
        self.filtrar()

    def filtrar(self):
        busca = normalizar(self.busca.get().strip())
        selecao = self.tabela.selection()
        posicao = self.tabela.yview()[0]
        self.tabela.delete(*self.tabela.get_children())
        for chamado in sorted(self.chamados, key=lambda item: item['id'], reverse=True):
            responsavel = chamado['responsavel'] or {}
            conteudo = f"{chamado['id']} {chamado['titulo']} {chamado['solicitante']['nome']} {responsavel.get('nome', '')}"
            if busca not in normalizar(conteudo):
                continue
            if self.filtro_status.get() != "Todos" and STATUS[chamado['status']] != self.filtro_status.get():
                continue
            if self.filtro_prioridade.get() != "Todas" and PRIORIDADES[chamado['prioridade']] != self.filtro_prioridade.get():
                continue
            if self.somente_meus.get() and responsavel.get('id') != self.usuario['id']:
                continue
            indice = len(self.tabela.get_children())
            self.tabela.insert("", "end", iid=str(chamado['id']), values=(
                chamado['id'], chamado['titulo'], STATUS[chamado['status']], PRIORIDADES[chamado['prioridade']],
                chamado['solicitante']['nome'], responsavel.get('nome', 'Não atribuído'), data_formatada(chamado['data_abertura'])),
                tags=("alternada",) if indice % 2 else ())
        if selecao and self.tabela.exists(selecao[0]):
            self.tabela.selection_set(selecao[0])
        self.tabela.yview_moveto(posicao)
        quantidade = len(self.tabela.get_children())
        if not quantidade:
            self.informacao.set("Nenhum chamado encontrado para estes filtros.")
        else:
            self.informacao.set(f"{quantidade} de {len(self.chamados)} chamados  •  Atualizado às {self.ultima_atualizacao}")

    def abrir_selecionado(self):
        from telas.chamados import DetalheChamado
        selecao = self.tabela.selection()
        if not selecao:
            messagebox.showinfo("Selecione um chamado", "Selecione uma linha para ver os detalhes.", parent=self)
            return
        self.app.abrir_dialogo(DetalheChamado, int(selecao[0]))

    def destroy(self):
        for variavel, identificador in self.observadores:
            variavel.trace_remove("write", identificador)
        self.observadores.clear()
        super().destroy()
        self.contadores.clear()
        self.busca = self.filtro_status = self.filtro_prioridade = None
        self.somente_meus = self.informacao = None
