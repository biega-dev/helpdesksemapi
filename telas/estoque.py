import tkinter as tk
from tkinter import messagebox, ttk

from telas.componentes import Formulario, campo, escolha, tabela, normalizar, data_formatada


class TelaEstoque(ttk.Frame):
    def __init__(self, pai, app):
        super().__init__(pai, padding=20)
        self.app = app
        self.equipamentos = []
        topo = ttk.Frame(self)
        topo.pack(fill='x', pady=(0, 16))
        ttk.Label(topo, text='Estoque de equipamentos', style='Titulo.TLabel').pack(side='left')
        ttk.Button(topo, text='+ Equipamento', style='Principal.TButton',
                   command=lambda: app.abrir_dialogo(CadastroEquipamento)).pack(side='right')
        filtros = ttk.Frame(self)
        filtros.pack(fill='x', pady=(0, 12))
        self.busca = tk.StringVar()
        ttk.Label(filtros, text='Buscar').pack(side='left', padx=(0, 8))
        ttk.Entry(filtros, textvariable=self.busca).pack(side='left', fill='x', expand=True)
        self.filtro = tk.StringVar(value='Ativos')
        ttk.Combobox(filtros, textvariable=self.filtro, values=['Ativos', 'Abaixo do mínimo', 'Baixados', 'Todos'],
                     state='readonly', width=20).pack(side='left', padx=10)
        ttk.Button(filtros, text='Atualizar', command=self.atualizar).pack(side='right')
        rodape = ttk.Frame(self)
        rodape.pack(side='bottom', fill='x', pady=(12, 0))
        self.informacao = tk.StringVar()
        ttk.Label(self, textvariable=self.informacao, style='Discreto.TLabel').pack(anchor='w', pady=(0, 10))
        self.tabela = tabela(self, [('codigo', 'Código', 100), ('descricao', 'Descrição', 260), ('tipo', 'Tipo', 150),
                                   ('saldo', 'Saldo (un.)', 90), ('minimo', 'Mínimo (un.)', 100), ('situacao', 'Situação', 150)])
        self.botoes = {}
        for chave, rotulo in [('editar', 'Editar'), ('entrada', 'Repor'), ('saida', 'Registrar saída'),
                              ('baixa', 'Dar baixa'), ('historico', 'Movimentações')]:
            botao = ttk.Button(rodape, text=rotulo, command=lambda acao=chave: self.abrir(acao), state='disabled')
            botao.pack(side='left', padx=(0, 8))
            self.botoes[chave] = botao
        self.tabela.bind('<<TreeviewSelect>>', lambda e: self.atualizar_botoes())
        self.tabela.bind('<Double-1>', lambda e: self.abrir('historico'))
        self.observadores = [(v, v.trace_add('write', lambda *a: self.filtrar())) for v in (self.busca, self.filtro)]

    def atualizar(self, silencioso=False):
        self.app.executar(lambda: self.app.servico.listar_equipamentos(False), self.receber, silencioso=silencioso)

    def receber(self, equipamentos):
        if self.winfo_exists():
            self.equipamentos = equipamentos
            self.filtrar()

    def filtrar(self):
        selecionado = self.tabela.selection()
        self.tabela.delete(*self.tabela.get_children())
        busca, filtro = normalizar(self.busca.get().strip()), self.filtro.get()
        for e in self.equipamentos:
            if busca not in normalizar(f"{e['codigo']} {e['descricao']} {e['tipo']}"):
                continue
            if filtro == 'Ativos' and not e['ativo'] or filtro == 'Baixados' and e['ativo']:
                continue
            if filtro == 'Abaixo do mínimo' and (not e['ativo'] or not e['abaixo_do_minimo']):
                continue
            situacao = 'Baixado' if not e['ativo'] else ('Abaixo do mínimo' if e['abaixo_do_minimo'] else 'Disponível')
            self.tabela.insert('', 'end', iid=e['codigo'], values=(e['codigo'], e['descricao'], e['tipo'],
                e['quantidade'], e['quantidade_minima'], situacao),
                tags=('inativo',) if not e['ativo'] else ('alerta',) if e['abaixo_do_minimo'] else ())
        if selecionado and self.tabela.exists(selecionado[0]):
            self.tabela.selection_set(selecionado[0])
        ativos = [e for e in self.equipamentos if e['ativo']]
        baixos = sum(e['abaixo_do_minimo'] for e in ativos)
        self.informacao.set(f"{len(self.tabela.get_children())} itens na lista • {len(ativos)} cadastros ativos • {baixos} abaixo do mínimo")
        self.atualizar_botoes()

    def selecionado(self):
        selecao = self.tabela.selection()
        return next((e for e in self.equipamentos if selecao and e['codigo'] == selecao[0]), None)

    def atualizar_botoes(self):
        e = self.selecionado()
        for acao, botao in self.botoes.items():
            habilitado = e and (acao == 'historico' or e['ativo'])
            botao.configure(state='normal' if habilitado else 'disabled')

    def abrir(self, acao):
        equipamento = self.selecionado()
        if not equipamento:
            return
        if acao == 'editar':
            self.app.abrir_dialogo(CadastroEquipamento, equipamento)
        elif acao == 'historico':
            self.app.abrir_dialogo(HistoricoEquipamento, equipamento)
        else:
            self.app.abrir_dialogo(MovimentarEquipamento, equipamento, acao)

    def destroy(self):
        for variavel, observador in self.observadores:
            variavel.trace_remove('write', observador)
        self.observadores.clear()
        super().destroy()
        self.busca = self.filtro = self.informacao = None


class CadastroEquipamento(Formulario):
    def __init__(self, app, equipamento=None):
        super().__init__(app, 'Editar equipamento' if equipamento else 'Cadastrar equipamento', '560x610')
        self.equipamento = equipamento
        dados = equipamento or dict(codigo='', descricao='', tipo='', quantidade=0, quantidade_minima=0)
        self.codigo = campo(self.corpo, 'Código')
        self.descricao = campo(self.corpo, 'Descrição')
        self.tipo = campo(self.corpo, 'Tipo de equipamento')
        self.quantidade = campo(self.corpo, 'Saldo atual (un.)' if equipamento else 'Quantidade inicial (un.)')
        self.minimo = campo(self.corpo, 'Quantidade mínima (un.)')
        for widget, chave in [(self.codigo, 'codigo'), (self.descricao, 'descricao'), (self.tipo, 'tipo'),
                               (self.quantidade, 'quantidade'), (self.minimo, 'quantidade_minima')]:
            widget.insert(0, str(dados[chave]))
        if equipamento:
            for widget in (self.codigo, self.tipo, self.quantidade):
                widget.configure(state='readonly')
            ttk.Label(self.corpo, text='Para alterar o saldo, registre uma reposição ou uma saída.',
                      style='Discreto.TLabel').pack(anchor='w', pady=12)
        self.rodape(self.salvar)

    def salvar(self):
        dados = dict(codigo=self.codigo.get().strip(), descricao=self.descricao.get().strip(), tipo=self.tipo.get().strip(),
                     quantidade=self.quantidade.get(), quantidade_minima=self.minimo.get())
        tarefa = (lambda: self.app.servico.atualizar_equipamento(self.equipamento['codigo'], dados)) if self.equipamento else (
            lambda: self.app.servico.cadastrar_equipamento(dados))
        self.enviar(tarefa, self.concluido)


class MovimentarEquipamento(Formulario):
    def __init__(self, app, equipamento, operacao):
        titulos = {'entrada': 'Repor equipamento', 'saida': 'Registrar saída', 'baixa': 'Dar baixa em equipamento'}
        super().__init__(app, titulos[operacao], '620x520')
        self.equipamento, self.operacao = equipamento, operacao
        self.chamados = []
        ttk.Label(self.corpo, text=f"{equipamento['codigo']} • {equipamento['descricao']}\nSaldo: {equipamento['quantidade']} unidades",
                  wraplength=540).pack(anchor='w', pady=(6, 12))
        if operacao != 'baixa':
            self.quantidade = campo(self.corpo, 'Quantidade (un.)')
            self.quantidade.insert(0, '1')
        if operacao == 'saida':
            self.chamado = escolha(self.corpo, 'Chamado atendido por você', ['Carregando...'])
            ttk.Label(self.corpo, text='A saída também será registrada no histórico do chamado.',
                      style='Discreto.TLabel').pack(anchor='w', pady=12)
        else:
            self.motivo = campo(self.corpo, 'Motivo da baixa' if operacao == 'baixa' else 'Motivo da reposição')
        self.rodape(self.salvar, 'Confirmar baixa' if operacao == 'baixa' else 'Registrar')
        if operacao == 'saida':
            self.botao_salvar.configure(state='disabled')
            app.executar(app.servico.listar_chamados, self.receber_chamados)

    def receber_chamados(self, chamados):
        if not self.winfo_exists():
            return
        self.chamados = [c for c in chamados if c['status'] in ('EM_ATENDIMENTO', 'PENDENTE')
                          and (c['responsavel'] or {}).get('id') == self.app.servico.usuario['id']]
        self.chamado.configure(values=[f"#{c['id']} • {c['titulo']}" for c in self.chamados] or ['Nenhum chamado elegível'])
        self.chamado.current(0)
        self.botao_salvar.configure(state='normal' if self.chamados else 'disabled')

    def salvar(self):
        codigo = self.equipamento['codigo']
        if self.operacao == 'entrada':
            quantidade, motivo = self.quantidade.get(), self.motivo.get()
            tarefa = lambda: self.app.servico.repor_equipamento(codigo, quantidade, motivo)
        elif self.operacao == 'saida':
            if not self.chamados:
                return
            chamado_id = self.chamados[self.chamado.current()]['id']
            quantidade = self.quantidade.get()
            tarefa = lambda: self.app.servico.registrar_saida_equipamento(codigo, quantidade, chamado_id)
        else:
            motivo = self.motivo.get().strip()
            if not motivo:
                messagebox.showwarning('Informe o motivo', 'Descreva o motivo da baixa.', parent=self)
                return
            if not messagebox.askyesno('Confirmar baixa', 'Este cadastro ficará inativo e não poderá mais ser movimentado. Continuar?', parent=self):
                return
            tarefa = lambda: self.app.servico.dar_baixa_equipamento(codigo, motivo)
        self.enviar(tarefa, self.concluido)


class HistoricoEquipamento(Formulario):
    def __init__(self, app, equipamento):
        super().__init__(app, 'Movimentações do equipamento', '940x530')
        self.minsize(760, 420)
        ttk.Label(self.corpo, text=f"{equipamento['codigo']} • {equipamento['descricao']}").pack(anchor='w', pady=10)
        ttk.Button(self.corpo, text='Fechar', command=self.fechar).pack(side='bottom', anchor='e', pady=(10, 0))
        self.info = tk.StringVar(value='Carregando movimentações...')
        ttk.Label(self.corpo, textvariable=self.info, style='Discreto.TLabel').pack(anchor='w', pady=(0, 8))
        self.tabela = tabela(self.corpo, [('data', 'Data', 135), ('tipo', 'Operação', 90), ('quantidade', 'Unidades', 80),
            ('responsavel', 'Responsável', 150), ('chamado', 'Chamado', 80), ('motivo', 'Motivo', 240)])
        app.executar(lambda: app.servico.listar_movimentacoes(equipamento['codigo']), self.receber)

    def receber(self, movimentos):
        if not self.winfo_exists():
            return
        for m in movimentos:
            self.tabela.insert('', 'end', values=(data_formatada(m['data_hora']),
                {'ENTRADA': 'Entrada', 'SAIDA': 'Saída', 'BAIXA': 'Baixa'}[m['tipo']], m['quantidade'],
                m['responsavel']['nome'], f"#{m['chamado_id']}" if m['chamado_id'] else '—', m['motivo']))
        self.info.set(f'{len(movimentos)} movimentações. A quantidade da baixa indica o saldo inativado.' if movimentos
                      else 'Sem movimentações. O saldo inicial foi informado no cadastro.')

    def destroy(self):
        super().destroy()
        self.info = None
