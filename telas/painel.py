import tkinter as tk
from time import monotonic
from tkinter import ttk

from telas.lista_chamados import ListaChamados
from telas.usuarios import AlterarSenha


class TelaPainel(ttk.Frame):
    def __init__(self, pai, app):
        super().__init__(pai)
        self.app = app
        usuario = app.servico.usuario
        cabecalho = tk.Frame(self, background='#172c4b', padx=22, pady=14)
        cabecalho.pack(fill='x')
        titulo = 'Painel Administrativo' if usuario['perfil'] == 'Administrador' else 'Aplicativo Principal'
        tk.Label(cabecalho, text=f'HELP DESK  /  {titulo}', background='#172c4b', foreground='white',
                 font=('Segoe UI', 15, 'bold')).pack(side='left')
        ttk.Button(cabecalho, text='Sair da conta', command=app.sair).pack(side='right')
        ttk.Button(cabecalho, text='Minha senha', command=lambda: app.abrir_dialogo(AlterarSenha)).pack(side='right', padx=8)
        faixa = ttk.Frame(self, padding=(20, 8))
        faixa.pack(fill='x')
        ttk.Label(faixa, text=f"{usuario['nome']} • {usuario['perfil']}", style='Discreto.TLabel').pack(anchor='w')
        self.abas = ttk.Notebook(self)
        self.abas.pack(fill='both', expand=True, padx=12, pady=(0, 8))
        self.paginas = {'Chamados': ListaChamados(self.abas, app)}
        if usuario['perfil'] == 'Técnico de TI':
            from telas.estoque import TelaEstoque
            self.paginas['Estoque'] = TelaEstoque(self.abas, app)
        elif usuario['perfil'] == 'Administrador':
            from telas.administracao import TelaUsuarios, TelaEquipe
            self.paginas['Usuários'] = TelaUsuarios(self.abas, app)
            self.paginas['Equipe'] = TelaEquipe(self.abas, app)
        for nome, pagina in self.paginas.items():
            self.abas.add(pagina, text=nome)
        self.agendamento = None
        self.atualizacao_pendente = False
        self.ultima_atualizacao = monotonic()
        self.abas.bind('<<NotebookTabChanged>>', lambda e: self.atualizar())
        self.agendar()

    def atualizar(self, silencioso=False):
        if self.app.ocupado:
            self.atualizacao_pendente = True
            return
        self.atualizacao_pendente = False
        self.ultima_atualizacao = monotonic()
        atual = self.abas.select()
        for pagina in self.paginas.values():
            if str(pagina) == atual:
                pagina.atualizar(silencioso=silencioso)
                break

    def agendar(self):
        self.agendamento = self.after(250, self.verificar_atualizacao)

    def verificar_atualizacao(self):
        dialogo_aberto = self.app.dialogo and self.app.dialogo.winfo_exists()
        automatica = not self.app.modo_local and monotonic() - self.ultima_atualizacao >= 10
        if not dialogo_aberto and not self.app.ocupado and (self.atualizacao_pendente or automatica):
            self.atualizar(silencioso=True)
        self.agendar()

    def destroy(self):
        if self.agendamento:
            self.after_cancel(self.agendamento)
        super().destroy()
        self.paginas.clear()
