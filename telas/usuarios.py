from tkinter import messagebox, ttk

from telas.componentes import Formulario, PERFIS, campo, codigo, escolha


class CadastroUsuario(Formulario):
    def __init__(self, app, autocadastro=False):
        self.autocadastro = autocadastro
        super().__init__(app, "Criar minha conta" if autocadastro else "Cadastrar usuário", "560x690")
        self.minsize(510, 650)
        ttk.Label(self.corpo, text="Cadastro de usuário comum." if autocadastro else "Crie o acesso e informe as credenciais ao usuário.",
                  style="Discreto.TLabel").pack(anchor="w")
        self.rodape(self.salvar, "Cadastrar")
        self.nome = campo(self.corpo, "Nome completo")
        self.email = campo(self.corpo, "E-mail")
        self.perfil = escolha(self.corpo, "Perfil de acesso", ['Usuário Comum'] if autocadastro else PERFIS.values())
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
            if self.autocadastro:
                self.app.tela.email.delete(0, 'end')
                self.app.tela.email.insert(0, usuario['email'])
                self.app.tela.senha.focus_set()
            else:
                self.app.tela.atualizar()
        operacao = self.app.servico.cadastrar_conta if self.autocadastro else self.app.servico.cadastrar_usuario
        self.enviar(lambda: operacao(dados), concluido)


class EditarTecnico(Formulario):
    def __init__(self, app, usuario):
        super().__init__(app, "Editar técnico", "560x400")
        self.minsize(510, 380)
        self.usuario_id = usuario['id']
        self.nome = campo(self.corpo, "Nome completo")
        self.nome.insert(0, usuario['nome'])
        self.especialidade = campo(self.corpo, "Especialidade")
        self.especialidade.insert(0, usuario['especialidade'])
        ttk.Label(self.corpo, text=usuario['email'], style="Discreto.TLabel").pack(anchor="w", pady=16)
        self.rodape(self.salvar)

    def salvar(self):
        dados = dict(nome=self.nome.get().strip(), especialidade=self.especialidade.get().strip())
        self.enviar(lambda: self.app.servico.atualizar_tecnico(self.usuario_id, dados), self.concluido)


class AlterarSenha(Formulario):
    def __init__(self, app):
        super().__init__(app, "Alterar minha senha", "560x460")
        self.minsize(510, 440)
        self.atual = campo(self.corpo, "Senha atual", senha=True)
        self.nova = campo(self.corpo, "Nova senha (mínimo de 4 caracteres)", senha=True)
        self.confirmacao = campo(self.corpo, "Confirmar nova senha", senha=True)
        self.rodape(self.salvar)

    def salvar(self):
        atual, nova = self.atual.get(), self.nova.get()
        if nova != self.confirmacao.get() or len(nova) < 4:
            messagebox.showwarning("Confira a senha", "Confirme a nova senha, com pelo menos 4 caracteres.", parent=self)
            return
        def concluido(_):
            self.destroy()
            self.app.status.set("Senha alterada. Use a nova senha no próximo acesso.")
        self.enviar(lambda: self.app.servico.alterar_senha(atual, nova), concluido)
