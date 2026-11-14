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
        tk.Label(marca, text="Abra chamados, acompanhe o andamento\ne mantenha o histórico do atendimento.",
                 font=("Segoe UI", 11), justify="left", foreground="#c6d4e8", background="#172c4b").pack(anchor="w")
        direita = ttk.Frame(self, padding=(38, 30), width=440)
        direita.pack(side="right", fill="y")
        direita.pack_propagate(False)
        ttk.Label(direita, text="Acessar sua conta", style="Titulo.TLabel").pack(anchor="w", pady=(48, 8))
        ttk.Label(direita, text="Use o acesso fornecido pelo administrador.",
                  style="Discreto.TLabel").pack(anchor="w", pady=(0, 12))
        self.email = campo(direita, "E-mail")
        self.senha = campo(direita, "Senha", senha=True)
        self.mostrar = tk.BooleanVar()
        ttk.Checkbutton(direita, text="Mostrar senha", variable=self.mostrar,
                        command=lambda: self.senha.configure(show="" if self.mostrar.get() else "*")).pack(anchor="w", pady=10)
        self.botao = ttk.Button(direita, text="Entrar", style="Principal.TButton", command=self.entrar)
        self.botao.pack(fill="x", pady=(6, 20))
        ttk.Separator(direita).pack(fill="x", pady=8)
        ttk.Label(direita, text="Aplicação local\n\nOs dados ficam disponíveis enquanto\neste programa estiver aberto.",
                  style="Discreto.TLabel").pack(anchor="w", pady=12)
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
        def terminar():
            if self.winfo_exists():
                self.botao.configure(state="normal")
                self.senha.delete(0, "end")
        self.botao.configure(state="disabled")
        self.app.executar(lambda: self.app.servico.login(email, senha), self.app.mostrar_painel,
                          fim=terminar, mensagem="Entrando...")

    def destroy(self):
        super().destroy()
        # A variável do Tk precisa ser liberada na thread da interface.
        self.mostrar = None
