from tkinter import messagebox, ttk

from telas.componentes import Formulario, PERFIS, campo, codigo, escolha


class CadastroUsuario(Formulario):
    def __init__(self, app):
        super().__init__(app, "Cadastrar usuário", "560x690")
        self.minsize(510, 650)
        ttk.Label(self.corpo, text="Crie o acesso e informe as credenciais ao usuário.",
                  style="Discreto.TLabel").pack(anchor="w")
        self.rodape(self.salvar, "Cadastrar")
        self.nome = campo(self.corpo, "Nome completo")
        self.email = campo(self.corpo, "E-mail")
        self.perfil = escolha(self.corpo, "Perfil de acesso", PERFIS.values())
        self.rotulo_complemento = ttk.Label(self.corpo, text="Setor")
        self.rotulo_complemento.pack(anchor="w", pady=(10, 4))
        self.complemento = ttk.Entry(self.corpo)
        self.complemento.pack(fill="x", ipady=3)
        self.senha = campo(self.corpo, "Senha (mínimo de 4 caracteres)", senha=True)
        self.confirmacao = campo(self.corpo, "Confirmar senha", senha=True)
        self.perfil.bind("<<ComboboxSelected>>", lambda evento: self.atualizar_perfil())
        self.nome.focus_set()

    def atualizar_perfil(self):
        rotulo = {"comum": "Setor", "tecnico": "Especialidade", "administrador": "Cargo"}
        self.rotulo_complemento.configure(text=rotulo[codigo(PERFIS, self.perfil.get())])

    def salvar(self):
        nome, email = self.nome.get().strip(), self.email.get().strip()
        complemento, senha = self.complemento.get().strip(), self.senha.get()
        if not nome or not email or not complemento or not senha:
            messagebox.showwarning("Confira os campos", "Preencha todos os campos do cadastro.", parent=self)
            return
        if "@" not in email or "." not in email.split("@")[-1] or " " in email:
            messagebox.showwarning("Confira o e-mail", "Informe um e-mail válido.", parent=self)
            return
        if len(senha) < 4:
            messagebox.showwarning("Confira a senha", "A senha deve ter pelo menos 4 caracteres.", parent=self)
            return
        if senha != self.confirmacao.get():
            messagebox.showwarning("Confira a senha", "As senhas informadas não são iguais.", parent=self)
            return
        perfil = codigo(PERFIS, self.perfil.get())
        atributo = {"comum": "setor", "tecnico": "especialidade", "administrador": "cargo"}[perfil]
        dados = {"nome": nome, "email": email, "senha": senha, "perfil": perfil, atributo: complemento}
        def concluido(usuario):
            self.destroy()
            messagebox.showinfo("Usuário cadastrado", f"{usuario['nome']} já pode entrar com o e-mail {usuario['email']}.", parent=self.app)
        self.enviar(lambda: self.app.servico.cadastrar_usuario(dados), concluido)
