import tkinter as tk
import traceback
from tkinter import messagebox, ttk

from helpdesk.excecoes import HelpDeskError
from sistema_local import ErroSistema, SistemaLocal


class Aplicacao(tk.Tk):
    def __init__(self, acesso='principal'):
        super().__init__()
        self.title("Help Desk | Aplicação local")
        self.geometry("1120x740")
        self.minsize(940, 650)
        self.servico = SistemaLocal()
        self.modo_local = True
        self.acesso = acesso
        self.ocupado = False
        self.tarefa_pendente = None
        self.tela = None
        self.dialogo = None
        self.configurar_estilo()
        self.conteudo = ttk.Frame(self)
        rodape = ttk.Frame(self, padding=(18, 8))
        rodape.pack(side='bottom', fill="x")
        self.conteudo.pack(fill="both", expand=True)
        self.status = tk.StringVar(value="Versão local • Dados mantidos durante esta execução.")
        ttk.Label(rodape, textvariable=self.status, style="Discreto.TLabel").pack(side="left")
        self.protocol("WM_DELETE_WINDOW", self.fechar)
        self.mostrar_login()

    def configurar_estilo(self):
        estilo = ttk.Style(self)
        estilo.theme_use("clam")
        self.configure(background="#f3f5f8")
        estilo.configure(".", font=("Segoe UI", 10), background="#f3f5f8", foreground="#1e293b")
        estilo.configure("TFrame", background="#f3f5f8")
        estilo.configure("TLabel", background="#f3f5f8")
        estilo.configure("Titulo.TLabel", font=("Segoe UI", 20, "bold"))
        estilo.configure("Discreto.TLabel", foreground="#526277", font=("Segoe UI", 9))
        estilo.configure("TButton", padding=(14, 8))
        estilo.configure("Principal.TButton", background="#2457c5", foreground="white")
        estilo.map("Principal.TButton", background=[("disabled", "#b3c2df"), ("active", "#1d469f")])
        estilo.configure("TEntry", fieldbackground="white", padding=5)
        estilo.configure("TCombobox", padding=5)
        estilo.configure("Treeview", rowheight=34, fieldbackground="white", background="white", borderwidth=0)
        estilo.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), padding=(8, 10))
        estilo.map("Treeview", background=[("selected", "#dce8ff")], foreground=[("selected", "#16366f")])
        estilo.configure("TNotebook.Tab", padding=(16, 8))
        estilo.configure('TNotebook', borderwidth=0)
        estilo.map('TNotebook.Tab', background=[('selected', '#ffffff')], foreground=[('selected', '#2457c5')])

    def trocar_tela(self, nova_tela):
        if self.dialogo and self.dialogo.winfo_exists():
            self.dialogo.destroy()
        self.dialogo = None
        if self.tela:
            self.tela.destroy()
        self.tela = nova_tela(self.conteudo, self)
        self.tela.pack(fill="both", expand=True)

    def mostrar_login(self):
        from telas.login import TelaLogin
        self.servico.limpar_sessao()
        self.trocar_tela(TelaLogin)

    def mostrar_painel(self, usuario=None):
        from telas.painel import TelaPainel
        self.trocar_tela(TelaPainel)
        self.tela.atualizar()

    def configurar_servidor(self, endereco=None):
        # A interface é compartilhada com a versão API; aqui tudo permanece local.
        pass

    def abrir_dialogo(self, classe, *args):
        if self.dialogo and self.dialogo.winfo_exists():
            self.dialogo.lift()
            return
        if self.ocupado:
            return
        self.dialogo = classe(self, *args)

    def executar(self, tarefa, sucesso, fim=None, silencioso=False, mensagem="Processando...", falha=None):
        if self.ocupado:
            return False
        self.ocupado = True
        self.status.set(mensagem)
        def concluir():
            self.tarefa_pendente = None
            try:
                resultado, erro = tarefa(), None
            except Exception as excecao:
                resultado, erro = None, excecao
            self.ocupado = False
            if fim:
                fim()
            if erro:
                if falha:
                    falha(erro)
                self.tratar_erro(erro, silencioso)
            else:
                self.status.set("Versão local • Dados mantidos durante esta execução.")
                sucesso(resultado)
        # Todas as operações usam os objetos locais, na própria thread do Tkinter.
        self.tarefa_pendente = self.after(1, concluir)
        return True

    def tratar_erro(self, erro, silencioso=False):
        if isinstance(erro, ErroSistema) and erro.motivo == "acesso":
            self.mostrar_login()
            self.status.set(str(erro))
            messagebox.showwarning("Acesso", str(erro), parent=self)
            return
        esperado = isinstance(erro, (ErroSistema, HelpDeskError, ValueError))
        mensagem = str(erro) if esperado else "Ocorreu um erro inesperado. Tente novamente."
        if not esperado:
            traceback.print_exception(type(erro), erro, erro.__traceback__)
        self.status.set(mensagem)
        if not silencioso:
            pai = self.dialogo if self.dialogo and self.dialogo.winfo_exists() else self
            messagebox.showerror("Não foi possível concluir", mensagem, parent=pai)

    def sair(self):
        if self.ocupado:
            return
        if messagebox.askyesno("Sair", "Deseja sair da sua conta?", parent=self):
            self.servico.logout()
            self.mostrar_login()
            self.status.set("Conta encerrada. Os dados continuam disponíveis nesta execução.")

    def fechar(self):
        if messagebox.askyesno("Fechar programa", "Os dados desta execução serão apagados ao fechar. Deseja continuar?", parent=self):
            self.destroy()

    def destroy(self):
        if self.tarefa_pendente:
            self.after_cancel(self.tarefa_pendente)
        super().destroy()
        self.status = None
