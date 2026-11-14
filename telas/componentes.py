import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk


STATUS = {"ABERTO": "Aberto", "EM_ATENDIMENTO": "Em atendimento",
          "PENDENTE": "Pendente", "RESOLVIDO": "Resolvido", "CANCELADO": "Cancelado"}
CATEGORIAS = {"HARDWARE": "Hardware", "SOFTWARE": "Software", "REDE": "Rede",
              "ACESSO": "Acesso", "OUTROS": "Outros"}
PRIORIDADES = {"BAIXA": "Baixa", "MEDIA": "Média", "ALTA": "Alta", "CRITICA": "Crítica"}
TIPOS = {"DIAGNOSTICO": "Diagnóstico", "SOLUCAO": "Solução", "OBSERVACAO": "Observação"}
PERFIS = {"comum": "Usuário Comum", "tecnico": "Técnico de TI", "administrador": "Administrador"}


def codigo(opcoes, texto):
    return next(chave for chave, valor in opcoes.items() if valor == texto)


def data_formatada(valor):
    if not valor:
        return "—"
    try:
        return datetime.fromisoformat(valor).strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return valor


def campo(pai, rotulo, senha=False):
    ttk.Label(pai, text=rotulo).pack(anchor="w", pady=(10, 4))
    entrada = ttk.Entry(pai, show="*" if senha else "")
    entrada.pack(fill="x", ipady=3)
    return entrada


def escolha(pai, rotulo, valores, inicial=0):
    ttk.Label(pai, text=rotulo).pack(anchor="w", pady=(10, 4))
    entrada = ttk.Combobox(pai, values=list(valores), state="readonly")
    entrada.current(inicial)
    entrada.pack(fill="x", ipady=3)
    return entrada


def texto(pai, altura=5):
    quadro = ttk.Frame(pai)
    quadro.pack(fill="both", expand=True, pady=(4, 8))
    entrada = tk.Text(quadro, height=altura, wrap="word", font=("Segoe UI", 10),
                      relief="solid", borderwidth=1, padx=10, pady=8, undo=True)
    barra = ttk.Scrollbar(quadro, command=entrada.yview)
    entrada.configure(yscrollcommand=barra.set)
    barra.pack(side="right", fill="y")
    entrada.pack(side="left", fill="both", expand=True)
    return entrada


def preencher_texto(entrada, conteudo):
    posicao = entrada.yview()[0]
    entrada.configure(state="normal")
    entrada.delete("1.0", "end")
    entrada.insert("1.0", conteudo)
    entrada.configure(state="disabled")
    entrada.yview_moveto(posicao)


class Formulario(tk.Toplevel):
    def __init__(self, app, titulo, tamanho="560x610"):
        super().__init__(app)
        self.app = app
        self.enviando = False
        self.title(titulo)
        self.geometry(tamanho)
        self.minsize(510, 520)
        self.transient(app)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.fechar)
        self.bind("<Escape>", lambda evento: self.fechar())
        self.corpo = ttk.Frame(self, padding=24)
        self.corpo.pack(fill="both", expand=True)
        ttk.Label(self.corpo, text=titulo, style="Titulo.TLabel").pack(anchor="w", pady=(0, 8))

    def fechar(self):
        if self.enviando:
            messagebox.showinfo("Aguarde", "Aguarde o retorno do envio antes de fechar esta janela.", parent=self)
            return
        self.destroy()

    def rodape(self, comando, rotulo="Salvar"):
        linha = ttk.Frame(self.corpo)
        linha.pack(side="bottom", fill="x", pady=(16, 0))
        ttk.Button(linha, text="Fechar", command=self.fechar).pack(side="right")
        self.botao_salvar = ttk.Button(linha, text=rotulo, command=comando, style="Principal.TButton")
        self.botao_salvar.pack(side="right", padx=(0, 8))

    def enviar(self, tarefa, sucesso):
        if self.enviando:
            return
        def terminar():
            if self.winfo_exists():
                self.enviando = False
                self.botao_salvar.configure(state="normal")
        if self.app.executar(tarefa, sucesso, fim=terminar):
            self.enviando = True
            self.botao_salvar.configure(state="disabled")
