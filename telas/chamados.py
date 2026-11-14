import tkinter as tk
from tkinter import messagebox, ttk

from telas.componentes import (
    CATEGORIAS, PRIORIDADES, STATUS, TIPOS, Formulario, campo, codigo,
    data_formatada, escolha, preencher_texto, texto,
)


class NovoChamado(Formulario):
    def __init__(self, app):
        super().__init__(app, "Abrir chamado", "620x640")
        ttk.Label(self.corpo, text="Conte o que aconteceu para que a equipe possa ajudar.",
                  style="Discreto.TLabel").pack(anchor="w")
        self.rodape(self.salvar, "Abrir chamado")
        self.titulo = campo(self.corpo, "Título")
        self.categoria = escolha(self.corpo, "Categoria", CATEGORIAS.values(), 1)
        self.prioridade = escolha(self.corpo, "Prioridade", PRIORIDADES.values(), 1)
        ttk.Label(self.corpo, text="Descrição do problema").pack(anchor="w", pady=(14, 0))
        ttk.Label(self.corpo, text="Informe a tela, a mensagem de erro e o que estava tentando fazer.",
                  style="Discreto.TLabel").pack(anchor="w", pady=(2, 4))
        self.descricao = texto(self.corpo, 6)
        self.titulo.focus_set()

    def salvar(self):
        titulo, descricao = self.titulo.get().strip(), self.descricao.get("1.0", "end-1c").strip()
        if not titulo or not descricao:
            messagebox.showwarning("Confira os campos", "Informe o título e a descrição do problema.", parent=self)
            return
        if len(titulo) > 150 or len(descricao) > 5000:
            messagebox.showwarning("Texto muito longo", "Use até 150 caracteres no título e 5.000 na descrição.", parent=self)
            return
        dados = {"titulo": titulo, "descricao": descricao, "categoria": codigo(CATEGORIAS, self.categoria.get()),
                 "prioridade": codigo(PRIORIDADES, self.prioridade.get())}
        def concluido(chamado):
            self.destroy()
            messagebox.showinfo("Chamado aberto", f"Seu chamado foi registrado com o número #{chamado['id']}.", parent=self.app)
            self.app.tela.atualizar()
        self.enviar(lambda: self.app.servico.abrir_chamado(dados), concluido)


class DetalheChamado(Formulario):
    def __init__(self, app, chamado_id):
        super().__init__(app, f"Chamado #{chamado_id}", "850x720")
        self.minsize(740, 640)
        self.chamado_id = chamado_id
        self.chamado = None
        self.indisponivel = False
        self.usuario = app.servico.usuario.copy()
        self.resumo = tk.StringVar(value="Carregando os dados do chamado...")
        ttk.Label(self.corpo, textvariable=self.resumo, wraplength=740, justify="left").pack(anchor="w", pady=(0, 12))
        rodape = ttk.Frame(self.corpo)
        rodape.pack(side="bottom", fill="x", pady=(14, 0))
        self.botao_assumir = ttk.Button(rodape, text="Assumir chamado", style="Principal.TButton", command=self.assumir)
        self.botao_cancelar = ttk.Button(rodape, text="Cancelar chamado", command=self.cancelar)
        if self.usuario['perfil'] == "Técnico de TI":
            self.botao_assumir.pack(side="left")
        elif self.usuario['perfil'] == "Usuário Comum":
            self.botao_cancelar.pack(side="left")
        ttk.Button(rodape, text="Fechar", command=self.fechar).pack(side="right")
        ttk.Button(rodape, text="Atualizar", command=self.atualizar).pack(side="right", padx=8)
        self.abas = ttk.Notebook(self.corpo)
        self.abas.pack(fill="both", expand=True)
        detalhes = ttk.Frame(self.abas, padding=14)
        historico = ttk.Frame(self.abas, padding=14)
        self.aba_atendimento = ttk.Frame(self.abas, padding=14)
        self.abas.add(detalhes, text="Descrição")
        self.abas.add(historico, text="Histórico")
        ttk.Label(detalhes, text="Problema informado", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.texto_descricao = texto(detalhes)
        self.texto_descricao.configure(state="disabled")
        ttk.Label(historico, text="Registros do atendimento", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.texto_historico = texto(historico)
        self.texto_historico.configure(state="disabled")
        if self.usuario['perfil'] == "Técnico de TI":
            self.abas.add(self.aba_atendimento, text="Registrar atendimento", state="disabled")
        self.aba_equipamentos = ttk.Frame(self.abas, padding=14)
        self.equipamentos = []
        self.selecao_equipamento_iniciada = False
        self.equipamento = escolha(self.aba_equipamentos, 'Equipamento disponível', ['Carregando...'])
        self.equipamento.bind('<<ComboboxSelected>>', lambda e: self.atualizar_botoes())
        self.quantidade_saida = campo(self.aba_equipamentos, 'Quantidade para este chamado (un.)')
        self.quantidade_saida.insert(0, '1')
        ttk.Label(self.aba_equipamentos, text='A saída reduz o saldo e registra a entrega no histórico do chamado.',
                  style='Discreto.TLabel', wraplength=650).pack(anchor='w', pady=16)
        self.botao_saida = ttk.Button(self.aba_equipamentos, text='Registrar saída de equipamento',
                                     style='Principal.TButton', command=self.registrar_saida)
        self.botao_saida.pack(anchor='e', pady=8)
        if self.usuario['perfil'] == 'Técnico de TI':
            self.abas.add(self.aba_equipamentos, text='Equipamentos', state='disabled')
        linha = ttk.Frame(self.aba_atendimento)
        linha.pack(fill="x")
        esquerda = ttk.Frame(linha)
        esquerda.pack(side="left", fill="x", expand=True, padx=(0, 12))
        direita = ttk.Frame(linha)
        direita.pack(side="right", fill="x", expand=True)
        self.tipo = escolha(esquerda, "Tipo de registro", TIPOS.values())
        self.novo_status = escolha(direita, "Situação após o registro", ["Manter status", "Em atendimento", "Pendente", "Resolvido"])
        ttk.Label(self.aba_atendimento, text="Descrição do atendimento").pack(anchor="w", pady=(12, 0))
        self.descricao = texto(self.aba_atendimento, 4)
        self.botao_salvar = ttk.Button(self.aba_atendimento, text="Registrar atendimento", style="Principal.TButton", command=self.registrar)
        self.botao_salvar.pack(anchor="e", pady=(4, 0))
        self.atualizar_botoes()
        self.agendamento = self.after(10000, self.atualizar_automaticamente)
        self.atualizar()

    def atualizar(self, silencioso=False):
        def buscar():
            chamado = self.app.servico.consultar_chamado(self.chamado_id)
            historico = self.app.servico.listar_atendimentos(self.chamado_id)
            equipamentos = self.app.servico.listar_equipamentos() if self.usuario['perfil'] == 'Técnico de TI' else []
            return chamado, historico, equipamentos
        self.app.executar(buscar, self.receber_dados, silencioso=silencioso, falha=self.verificar_acesso)

    def verificar_acesso(self, erro):
        if self.winfo_exists() and getattr(erro, "motivo", None) == "nao_encontrado":
            self.indisponivel = True
            self.chamado = None
            self.resumo.set("Este chamado não está mais disponível para sua conta. Atualize a lista de chamados.")
            preencher_texto(self.texto_descricao, "")
            preencher_texto(self.texto_historico, "")
            self.atualizar_botoes()

    def receber_dados(self, dados):
        if not self.winfo_exists():
            return
        self.chamado, historico, equipamentos = dados
        indice_anterior = self.equipamento.current()
        codigo_anterior = (self.equipamentos[indice_anterior]['codigo']
                           if 0 <= indice_anterior < len(self.equipamentos) else None)
        self.equipamentos = equipamentos
        opcoes = [f"{e['codigo']} • {e['descricao']} • {e['quantidade']} un. em estoque" for e in equipamentos]
        self.equipamento.configure(values=opcoes or ['Nenhum equipamento ativo'])
        codigos = [e['codigo'] for e in equipamentos]
        if codigo_anterior in codigos:
            self.equipamento.current(codigos.index(codigo_anterior))
        elif opcoes and not self.selecao_equipamento_iniciada:
            self.equipamento.current(0)
        else:
            self.equipamento.set('Selecione um equipamento' if opcoes else 'Nenhum equipamento ativo')
        self.selecao_equipamento_iniciada = True
        self.indisponivel = False
        self.exibir_chamado()
        registros = []
        for item in historico:
            registros.append(
                f"{data_formatada(item['data_hora'])}  |  {item['autor']['nome']}  |  {TIPOS[item['tipo']]}\n"
                f"{STATUS[item['status_anterior']]} → {STATUS[item['status_novo']]}\n{item['descricao']}"
            )
        preencher_texto(self.texto_historico, "\n\n──────────────────────────────\n\n".join(registros)
                        or "Ainda não há registros de atendimento neste chamado.")

    def exibir_chamado(self):
        chamado = self.chamado
        responsavel = chamado['responsavel'] or {}
        self.resumo.set(
            f"{chamado['titulo']}\n\n"
            f"{STATUS[chamado['status']]}  •  Prioridade {PRIORIDADES[chamado['prioridade']].lower()}  •  {CATEGORIAS[chamado['categoria']]}\n"
            f"Solicitante: {chamado['solicitante']['nome']}  |  Responsável: {responsavel.get('nome', 'Não atribuído')}\n"
            f"Abertura: {data_formatada(chamado['data_abertura'])}  |  Encerramento: {data_formatada(chamado['data_encerramento'])}"
        )
        preencher_texto(self.texto_descricao, chamado['descricao'])
        self.atualizar_botoes()

    def atualizar_botoes(self):
        chamado = self.chamado or {}
        responsavel = chamado.get('responsavel') or {}
        aberto = chamado.get('status') == 'ABERTO' and not self.enviando
        atender = (self.usuario['perfil'] == 'Técnico de TI' and responsavel.get('id') == self.usuario['id']
                   and chamado.get('status') in ('EM_ATENDIMENTO', 'PENDENTE') and not self.enviando)
        cancelar = aberto and chamado.get('solicitante', {}).get('id') == self.usuario['id']
        self.botao_assumir.configure(state="normal" if aberto else "disabled")
        self.botao_cancelar.configure(state="normal" if cancelar else "disabled")
        self.botao_salvar.configure(state="normal" if atender else "disabled")
        self.botao_saida.configure(state='normal' if atender and self.equipamentos and self.equipamento.current() >= 0 else 'disabled')
        if self.usuario['perfil'] == "Técnico de TI":
            if not atender and self.abas.select() in (str(self.aba_atendimento), str(self.aba_equipamentos)):
                self.abas.select(0)
            self.abas.tab(self.aba_atendimento, state="normal" if atender else "disabled")
            self.abas.tab(self.aba_equipamentos, state='normal' if atender else 'disabled')

    def executar_acao(self, tarefa, mensagem, limpar=False):
        if self.enviando:
            return
        def terminar():
            if self.winfo_exists():
                self.enviando = False
                self.atualizar_botoes()
        def concluido(chamado):
            if not self.winfo_exists():
                return
            self.chamado = chamado
            if limpar:
                self.descricao.delete("1.0", "end")
                self.novo_status.set("Manter status")
            self.exibir_chamado()
            self.app.status.set(mensagem)
            self.atualizar()
        if self.app.executar(tarefa, concluido, fim=terminar, falha=self.verificar_acesso):
            self.enviando = True
            self.atualizar_botoes()

    def assumir(self):
        if self.chamado and messagebox.askyesno("Assumir chamado", "Deseja assumir este atendimento?", parent=self):
            self.executar_acao(lambda: self.app.servico.assumir_chamado(self.chamado_id), "Chamado assumido.")

    def cancelar(self):
        if self.chamado and messagebox.askyesno("Cancelar chamado", "Deseja cancelar este chamado? Essa ação encerra a solicitação.", parent=self):
            self.executar_acao(lambda: self.app.servico.cancelar_chamado(self.chamado_id), "Chamado cancelado.")

    def registrar(self):
        descricao = self.descricao.get("1.0", "end-1c").strip()
        if not descricao:
            messagebox.showwarning("Confira os campos", "Descreva o atendimento realizado.", parent=self)
            return
        if len(descricao) > 5000:
            messagebox.showwarning("Texto muito longo", "Use até 5.000 caracteres na descrição.", parent=self)
            return
        dados = {"tipo": codigo(TIPOS, self.tipo.get()), "descricao": descricao}
        if self.novo_status.get() != "Manter status":
            dados['novo_status'] = codigo(STATUS, self.novo_status.get())
        if dados.get('novo_status') == 'RESOLVIDO':
            if not messagebox.askyesno("Resolver chamado", "Deseja registrar o atendimento e encerrar o chamado como resolvido?", parent=self):
                return
        self.executar_acao(lambda: self.app.servico.registrar_atendimento(self.chamado_id, dados),
                           "Atendimento registrado.", limpar=True)

    def registrar_saida(self):
        indice = self.equipamento.current()
        if indice < 0 or indice >= len(self.equipamentos):
            return
        codigo = self.equipamentos[indice]['codigo']
        quantidade = self.quantidade_saida.get()
        def registrar():
            self.app.servico.registrar_saida_equipamento(codigo, quantidade, self.chamado_id)
            return self.app.servico.consultar_chamado(self.chamado_id)
        self.executar_acao(registrar, 'Saída registrada no estoque e no histórico do chamado.')

    def atualizar_automaticamente(self):
        if not self.app.modo_local and not self.indisponivel:
            self.atualizar(silencioso=True)
        self.agendamento = self.after(10000, self.atualizar_automaticamente)

    def fechar(self):
        if self.enviando:
            super().fechar()
            return
        self.destroy()
        self.app.tela.atualizar(silencioso=True)

    def destroy(self):
        self.after_cancel(self.agendamento)
        super().destroy()
        self.resumo = None
