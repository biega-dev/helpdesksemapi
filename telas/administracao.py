import tkinter as tk
from tkinter import messagebox, ttk

from telas.componentes import PERFIS, STATUS, tabela, normalizar
from telas.usuarios import CadastroUsuario, EditarTecnico


class TelaUsuarios(ttk.Frame):
    def __init__(self, pai, app):
        super().__init__(pai, padding=20)
        self.app, self.usuarios = app, []
        topo = ttk.Frame(self)
        topo.pack(fill='x', pady=(0, 16))
        ttk.Label(topo, text='Usuários e acessos', style='Titulo.TLabel').pack(side='left')
        ttk.Button(topo, text='+ Cadastrar usuário', style='Principal.TButton',
                   command=lambda: app.abrir_dialogo(CadastroUsuario)).pack(side='right')
        filtros = ttk.Frame(self)
        filtros.pack(fill='x', pady=(0, 12))
        self.busca = tk.StringVar()
        ttk.Label(filtros, text='Buscar').pack(side='left', padx=(0, 8))
        ttk.Entry(filtros, textvariable=self.busca).pack(side='left', fill='x', expand=True)
        self.perfil = tk.StringVar(value='Todos os perfis')
        self.situacao = tk.StringVar(value='Todos')
        ttk.Combobox(filtros, textvariable=self.perfil, state='readonly', width=21,
                     values=['Todos os perfis', *PERFIS.values()]).pack(side='left', padx=8)
        ttk.Combobox(filtros, textvariable=self.situacao, state='readonly', width=12,
                     values=['Todos', 'Ativos', 'Bloqueados']).pack(side='left', padx=(0, 8))
        ttk.Button(filtros, text='Atualizar', command=self.atualizar).pack(side='right')
        rodape = ttk.Frame(self)
        rodape.pack(side='bottom', fill='x', pady=(12, 0))
        self.informacao = tk.StringVar()
        ttk.Label(self, textvariable=self.informacao, style='Discreto.TLabel').pack(anchor='w', pady=(0, 8))
        self.tabela = tabela(self, [('id', 'Nº', 40), ('nome', 'Nome', 170), ('email', 'E-mail', 190),
            ('perfil', 'Perfil', 150), ('complemento', 'Detalhe do perfil', 170), ('situacao', 'Situação', 90)])
        self.botoes = {}
        for chave, rotulo, comando in [('editar', 'Editar técnico', self.editar), ('bloquear', 'Bloquear / desbloquear', self.bloquear),
                                       ('excluir', 'Excluir técnico', self.excluir), ('desativar', 'Desativar administrador', self.desativar)]:
            botao = ttk.Button(rodape, text=rotulo, command=comando, state='disabled')
            botao.pack(side='left', padx=(0, 8))
            self.botoes[chave] = botao
        self.tabela.bind('<<TreeviewSelect>>', lambda e: self.atualizar_botoes())
        self.tabela.bind('<Double-1>', lambda e: self.editar())
        self.observadores = [(v, v.trace_add('write', lambda *a: self.filtrar())) for v in (self.busca, self.perfil, self.situacao)]

    def atualizar(self, silencioso=False):
        self.app.executar(self.app.servico.listar_usuarios, self.receber, silencioso=silencioso)

    def receber(self, usuarios):
        if self.winfo_exists():
            self.usuarios = usuarios
            self.filtrar()

    def filtrar(self):
        selecao = self.tabela.selection()
        self.tabela.delete(*self.tabela.get_children())
        busca = normalizar(self.busca.get().strip())
        for u in self.usuarios:
            complemento = u['especialidade'] or u['setor'] or u['cargo']
            if busca not in normalizar(f"{u['nome']} {u['email']} {complemento}"):
                continue
            if self.perfil.get() != 'Todos os perfis' and self.perfil.get() != u['perfil']:
                continue
            if self.situacao.get() == 'Ativos' and not u['ativo'] or self.situacao.get() == 'Bloqueados' and u['ativo']:
                continue
            self.tabela.insert('', 'end', iid=str(u['id']), values=(u['id'], u['nome'], u['email'], u['perfil'],
                complemento, 'Ativo' if u['ativo'] else 'Bloqueado'), tags=() if u['ativo'] else ('inativo',))
        if selecao and self.tabela.exists(selecao[0]):
            self.tabela.selection_set(selecao[0])
        self.informacao.set(f'{len(self.tabela.get_children())} de {len(self.usuarios)} usuários • Selecione uma pessoa para gerenciar o acesso.')
        self.atualizar_botoes()

    def selecionado(self):
        selecao = self.tabela.selection()
        return next((u for u in self.usuarios if selecao and str(u['id']) == selecao[0]), None)

    def atualizar_botoes(self):
        usuario = self.selecionado()
        for acao, botao in self.botoes.items():
            habilitado = bool(usuario)
            if acao in ('editar', 'excluir'):
                habilitado = usuario and usuario['perfil'] == 'Técnico de TI'
            elif acao == 'desativar':
                habilitado = usuario and usuario['perfil'] == 'Administrador' and usuario['ativo']
            botao.configure(state='normal' if habilitado else 'disabled')
        self.botoes['bloquear'].configure(text='Desbloquear' if usuario and not usuario['ativo'] else 'Bloquear')

    def editar(self):
        usuario = self.selecionado()
        if usuario and usuario['perfil'] == 'Técnico de TI':
            self.app.abrir_dialogo(EditarTecnico, usuario)

    def concluido(self, usuario=None):
        if usuario and usuario['id'] == self.app.servico.usuario['id'] and not usuario['ativo']:
            self.app.mostrar_login()
            self.app.status.set('Seu acesso foi desativado. Entre com uma conta ativa.')
        else:
            self.atualizar()

    def bloquear(self):
        usuario = self.selecionado()
        if not usuario:
            return
        acao = 'Bloquear' if usuario['ativo'] else 'Desbloquear'
        if messagebox.askyesno(acao, f"{acao} o acesso de {usuario['nome']}?", parent=self):
            self.app.executar(lambda: self.app.servico.alterar_bloqueio(usuario['id'], usuario['ativo']), self.concluido)

    def excluir(self):
        usuario = self.selecionado()
        if usuario and usuario['perfil'] == 'Técnico de TI' and messagebox.askyesno('Excluir técnico',
                f"Excluir {usuario['nome']}? Os registros antigos serão preservados. Chamados em atendimento impedem a exclusão.", parent=self):
            self.app.executar(lambda: self.app.servico.excluir_tecnico(usuario['id']), self.concluido)

    def desativar(self):
        usuario = self.selecionado()
        if usuario and messagebox.askyesno('Desativar administrador', f"Desativar o acesso de {usuario['nome']}?", parent=self):
            self.app.executar(lambda: self.app.servico.desativar_administrador(usuario['id']), self.concluido)

    def destroy(self):
        for variavel, observador in self.observadores:
            variavel.trace_remove('write', observador)
        self.observadores.clear()
        super().destroy()
        self.busca = self.perfil = self.situacao = self.informacao = None


class TelaEquipe(ttk.Frame):
    def __init__(self, pai, app):
        super().__init__(pai, padding=20)
        self.app, self.atividades = app, []
        topo = ttk.Frame(self)
        topo.pack(fill='x', pady=(0, 12))
        ttk.Label(topo, text='Atividades dos técnicos', style='Titulo.TLabel').pack(side='left')
        ttk.Button(topo, text='Atualizar', command=self.atualizar).pack(side='right')
        ttk.Label(self, text='Pendentes não ocupam o limite de cinco chamados em atendimento.',
                  style='Discreto.TLabel').pack(anchor='w', pady=(0, 12))
        acoes = ttk.Frame(self)
        acoes.pack(side='bottom', fill='x', pady=(12, 0))
        ttk.Button(acoes, text='Ver chamado selecionado', command=self.abrir_chamado).pack(side='right')
        miolo = ttk.Frame(self)
        miolo.pack(fill='both', expand=True)
        miolo.columnconfigure(0, weight=1)
        miolo.rowconfigure(0, weight=1, uniform='tabelas')
        miolo.rowconfigure(1, weight=1, uniform='tabelas')
        superior, inferior = ttk.Frame(miolo), ttk.Frame(miolo)
        superior.grid(row=0, column=0, sticky='nsew')
        inferior.grid(row=1, column=0, sticky='nsew')
        self.tabela = tabela(superior, [('nome', 'Técnico', 190), ('email', 'E-mail', 210), ('especialidade', 'Especialidade', 150),
            ('carga', 'Em atendimento / limite', 170), ('pendentes', 'Pendentes', 90), ('resolvidos', 'Resolvidos', 90),
            ('ativo', 'Acesso', 100)], altura=5)
        self.info = tk.StringVar(value='Selecione um técnico para consultar seus chamados.')
        ttk.Label(inferior, textvariable=self.info).pack(anchor='w', pady=8)
        self.chamados = tabela(inferior, [('id', 'Nº', 60), ('titulo', 'Chamado', 370), ('status', 'Situação', 150),
                                     ('solicitante', 'Solicitante', 200)], altura=5)
        self.tabela.bind('<<TreeviewSelect>>', lambda e: self.mostrar_chamados())
        self.chamados.bind('<Double-1>', lambda e: self.abrir_chamado())

    def atualizar(self, silencioso=False):
        self.app.executar(self.app.servico.listar_atividades, self.receber, silencioso=silencioso)

    def receber(self, atividades):
        if not self.winfo_exists():
            return
        selecao = self.tabela.selection()
        self.atividades = atividades
        self.tabela.delete(*self.tabela.get_children())
        for t in atividades:
            self.tabela.insert('', 'end', iid=str(t['id']), values=(t['nome'], t['email'], t['especialidade'],
                f"{t['em_atendimento']} / {t['limite']}", sum(c['status'] == 'PENDENTE' for c in t['chamados']),
                sum(c['status'] == 'RESOLVIDO' for c in t['chamados']), 'Ativo' if t['ativo'] else 'Bloqueado'))
        if selecao and self.tabela.exists(selecao[0]):
            self.tabela.selection_set(selecao[0])
        self.mostrar_chamados()

    def mostrar_chamados(self):
        selecao = self.tabela.selection()
        tecnico = next((t for t in self.atividades if selecao and str(t['id']) == selecao[0]), None)
        self.chamados.delete(*self.chamados.get_children())
        if tecnico:
            for c in tecnico['chamados']:
                self.chamados.insert('', 'end', iid=str(c['id']), values=(c['id'], c['titulo'], STATUS[c['status']], c['solicitante']['nome']))
            self.info.set(f"{tecnico['nome']} • {len(tecnico['chamados'])} chamados atribuídos")
        else:
            self.info.set('Selecione um técnico para consultar seus chamados.' if self.atividades else 'Nenhum técnico cadastrado.')

    def abrir_chamado(self):
        from telas.chamados import DetalheChamado
        selecao = self.chamados.selection()
        if selecao:
            self.app.abrir_dialogo(DetalheChamado, int(selecao[0]))

    def destroy(self):
        super().destroy()
        self.info = None
