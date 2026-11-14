import tkinter as tk
from tkinter import messagebox, ttk

from telas.componentes import campo


class TelaLogin(ttk.Frame):
    def __init__(self, pai, app):
        super().__init__(pai)
        self.app = app
        esquerda = tk.Frame(self, background="#172c4b", width=350)
        esquerda.pack(side="left", fill="both", expand=True)
        marca = tk.Frame(esquerda, background="#172c4b")
        marca.place(relx=0.12, rely=0.32, relwidth=0.8)
        tk.Label(marca, text="HELP DESK", font=("Segoe UI", 12, "bold"),
                 foreground="#8fb5ff", background="#172c4b").pack(anchor="w")
        tk.Label(marca, text="Seu suporte,\nem um só lugar.", font=("Segoe UI", 30, "bold"),
                 justify="left", foreground="white", background="#172c4b").pack(anchor="w", pady=20)
        tk.Label(marca, text="Chamados, atendimentos e equipamentos.\nCada perfil com seu espaço de trabalho.",
                 font=("Segoe UI", 11), justify="left", foreground="#c6d4e8", background="#172c4b").pack(anchor="w")
        direita = ttk.Frame(self, padding=(32, 20), width=470)
        direita.pack(side="right", fill="y")
        direita.pack_propagate(False)
        ttk.Label(direita, text="Acessar sua conta", style="Titulo.TLabel").pack(anchor="w", pady=(16, 8))
        self.acesso = tk.StringVar(value=app.acesso)
        ttk.Radiobutton(direita, text='Aplicativo Principal • usuários e técnicos', value='principal',
                        variable=self.acesso, command=self.alterar_acesso).pack(anchor='w', pady=4)
        ttk.Radiobutton(direita, text='Painel Administrativo • administradores', value='administrativo',
                        variable=self.acesso, command=self.alterar_acesso).pack(anchor='w', pady=4)
        if not app.modo_local:
            self.servidor = campo(direita, 'Endereço do servidor')
            self.servidor.insert(0, app.servico.url)
        self.email = campo(direita, "E-mail")
        self.senha = campo(direita, "Senha", senha=True)
        self.mostrar = tk.BooleanVar()
        ttk.Checkbutton(direita, text="Mostrar senha", variable=self.mostrar,
                        command=lambda: self.senha.configure(show="" if self.mostrar.get() else "*")).pack(anchor="w", pady=10)
        self.botao = ttk.Button(direita, text="Entrar", style="Principal.TButton", command=self.entrar)
        self.botao.pack(fill="x", pady=(6, 10))
        self.botao_cadastro = ttk.Button(direita, text='Criar minha conta', command=self.cadastrar_conta)
        self.botao_cadastro.pack(fill='x', pady=(0, 10))
        ttk.Separator(direita).pack(fill="x", pady=8)
        aviso = ('Dados em memória durante esta execução.\nSair da conta preserva os dados; fechar apaga.' if app.modo_local
                 else 'Dados compartilhados pelo servidor.\nO reinício do servidor limpa os dados em memória.')
        ttk.Label(direita, text=aviso, style="Discreto.TLabel").pack(anchor="w", pady=8)
        self.alterar_acesso()
        self.email.bind("<Return>", lambda evento: self.senha.focus_set())
        self.senha.bind("<Return>", lambda evento: self.entrar())
        self.email.focus_set()

    def entrar(self):
        if self.app.ocupado:
            return
        email, senha = self.email.get().strip(), self.senha.get()
        if not email or not senha:
            messagebox.showwarning("Confira os campos", "Informe seu e-mail e sua senha.", parent=self)
            return
        if not self.preparar_acesso():
            return
        def terminar():
            if self.winfo_exists():
                self.botao.configure(state="normal")
                self.senha.delete(0, "end")
        self.botao.configure(state="disabled")
        acesso = self.acesso.get()
        self.app.executar(lambda: self.app.servico.login(email, senha, acesso), self.app.mostrar_painel,
                          fim=terminar, mensagem="Entrando...")

    def alterar_acesso(self):
        self.app.acesso = self.acesso.get()
        self.botao_cadastro.configure(state='normal' if self.acesso.get() == 'principal' else 'disabled')

    def preparar_acesso(self):
        self.app.acesso = self.acesso.get()
        try:
            self.app.configurar_servidor(self.servidor.get() if not self.app.modo_local else None)
        except ValueError as erro:
            messagebox.showwarning('Confira o servidor', str(erro), parent=self)
            return False
        return True

    def cadastrar_conta(self):
        from telas.usuarios import CadastroUsuario
        if not self.app.ocupado and self.acesso.get() == 'principal' and self.preparar_acesso():
            self.app.abrir_dialogo(CadastroUsuario, True)

    def destroy(self):
        super().destroy()
        # A variável do Tk precisa ser liberada na thread da interface.
        self.mostrar = self.acesso = None
