from helpdesk.enums import Categoria, Permissao, Prioridade, StatusChamado, TipoAtendimento
from helpdesk.helpdesk import HelpDesk
from helpdesk.usuarios import Administrador, Tecnico


def texto_obrigatorio(valor, nome):
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(f"Informe {nome}.")
    return valor.strip()


def inteiro(valor, nome, minimo=0):
    # Não truncar decimais: estoque representa uma quantidade inteira de equipamentos.
    if isinstance(valor, bool) or not isinstance(valor, (int, str)):
        raise ValueError(f"{nome}: informe um número inteiro.")
    try:
        numero = int(valor)
    except ValueError:
        raise ValueError(f"{nome}: informe um número inteiro.") from None
    if numero < minimo:
        raise ValueError(f"{nome}: o mínimo é {minimo}.")
    return numero


def opcao(tipo, valor):
    try:
        return tipo[valor]
    except (KeyError, TypeError):
        raise ValueError(f"Selecione um valor válido para {tipo.__name__}.") from None


class ErroSistema(Exception):
    def __init__(self, mensagem, motivo=None):
        super().__init__(mensagem)
        self.motivo = motivo


class SistemaLocal:
    def __init__(self, sistema=None, usuario=None):
        if sistema is None:
            admin = Administrador("Marina Souza", "marina@empresa.com", "admin123", "Gerente de TI")
            sistema = HelpDesk("Help Desk", admin)
        self.sistema = sistema
        self._usuario_logado = usuario
        self.usuario = self.dados_usuario(usuario) if usuario else None

    def limpar_sessao(self):
        self._usuario_logado = None
        self.usuario = None

    def login(self, email, senha, acesso=None):
        self.limpar_sessao()
        areas = {"principal": Permissao.ACESSAR_APLICATIVO,
                 "administrativo": Permissao.ACESSAR_PAINEL_ADMIN}
        if acesso is not None and (not isinstance(acesso, str) or acesso not in areas):
            raise ValueError("Área de acesso inválida.")
        permissoes = [areas[acesso]] if acesso else list(areas.values())
        email = texto_obrigatorio(email, "e-mail")
        if not isinstance(senha, str) or not senha:
            raise ValueError("Informe a senha.")
        usuario = None
        for permissao in permissoes:
            usuario = self.sistema.autenticar(email, senha, permissao)
            if usuario:
                break
        if usuario is None:
            raise ErroSistema("E-mail, senha ou área de acesso incorretos.", "acesso")
        self._usuario_logado = usuario
        self.usuario = self.dados_usuario(usuario)
        return self.usuario

    def logout(self):
        self.limpar_sessao()

    def usuario_atual(self):
        if (self._usuario_logado is None or not self._usuario_logado.esta_ativo()
                or self._usuario_logado not in self.sistema.usuarios):
            self.limpar_sessao()
            raise ErroSistema("Entre novamente para continuar.", "acesso")
        return self._usuario_logado

    def exigir_permissao(self, permissao):
        usuario = self.usuario_atual()
        if not usuario.possui_permissao(permissao):
            raise ErroSistema("Seu perfil não tem permissão para esta operação.", "permissao")
        return usuario

    def cadastrar_conta(self, dados):
        if dados.get('perfil', 'comum') != 'comum':
            raise ErroSistema("O autocadastro cria somente contas de usuário comum.", "permissao")
        return self.dados_usuario(self.sistema.cadastrar_usuario_comum(
            texto_obrigatorio(dados.get('nome'), 'nome'), texto_obrigatorio(dados.get('email'), 'e-mail'),
            self.senha_informada(dados), texto_obrigatorio(dados.get('setor'), 'setor')))

    def senha_informada(self, dados):
        senha = dados.get('senha')
        if not isinstance(senha, str):
            raise ValueError("Informe a senha.")
        return senha

    def cadastrar_usuario(self, dados):
        admin = self.usuario_atual()
        if not admin.possui_permissao(Permissao.GERENCIAR_USUARIOS):
            raise ErroSistema("Somente administradores podem cadastrar usuários.", "permissao")
        nome = texto_obrigatorio(dados.get('nome'), 'nome')
        email = texto_obrigatorio(dados.get('email'), 'e-mail')
        senha = self.senha_informada(dados)
        if dados.get('perfil') not in ('comum', 'tecnico', 'administrador'):
            raise ValueError("Selecione o perfil de acesso.")
        if dados['perfil'] == 'comum':
            usuario = self.sistema.cadastrar_usuario_comum(nome, email, senha, texto_obrigatorio(dados.get('setor'), 'setor'))
        elif dados['perfil'] == 'tecnico':
            usuario = self.sistema.cadastrar_tecnico(admin, nome, email, senha, texto_obrigatorio(dados.get('especialidade'), 'especialidade'))
        elif dados['perfil'] == 'administrador':
            usuario = self.sistema.cadastrar_administrador(admin, nome, email, senha, texto_obrigatorio(dados.get('cargo'), 'cargo'))
        else:
            raise ErroSistema("Perfil de usuário inválido.")
        return self.dados_usuario(usuario)

    def listar_usuarios(self):
        self.exigir_permissao(Permissao.GERENCIAR_USUARIOS)
        return [self.dados_usuario(u) for u in self.sistema.usuarios]

    def buscar_usuario(self, usuario_id):
        self.exigir_permissao(Permissao.GERENCIAR_USUARIOS)
        for usuario in self.sistema.usuarios:
            if usuario.id == usuario_id:
                return usuario
        raise ErroSistema("Usuário não encontrado.", "nao_encontrado")

    def buscar_tecnico(self, usuario_id):
        usuario = self.buscar_usuario(usuario_id)
        if not isinstance(usuario, Tecnico):
            raise ValueError("Selecione uma conta de técnico.")
        return usuario

    def atualizar_tecnico(self, usuario_id, dados):
        tecnico = self.buscar_tecnico(usuario_id)
        nome = texto_obrigatorio(dados.get('nome'), 'nome')
        especialidade = texto_obrigatorio(dados.get('especialidade'), 'especialidade')
        self.sistema.atualizar_tecnico(self.usuario_atual(), tecnico, nome, especialidade)
        return self.dados_usuario(tecnico)

    def excluir_tecnico(self, usuario_id):
        self.sistema.excluir_tecnico(self.usuario_atual(), self.buscar_tecnico(usuario_id))

    def alterar_bloqueio(self, usuario_id, bloquear):
        if not isinstance(bloquear, bool):
            raise ValueError("Informe se deseja bloquear ou desbloquear.")
        alvo = self.buscar_usuario(usuario_id)
        self.sistema.alterar_bloqueio(self.usuario_atual(), alvo, bloquear)
        return self.dados_usuario(alvo)

    def desativar_administrador(self, usuario_id):
        alvo = self.buscar_usuario(usuario_id)
        self.sistema.desativar_administrador(self.usuario_atual(), alvo)
        return self.dados_usuario(alvo)

    def listar_atividades(self):
        self.exigir_permissao(Permissao.ACESSAR_PAINEL_ADMIN)
        # IDs mantêm separados dois técnicos com o mesmo nome.
        return [dict(self.dados_usuario(t), em_atendimento=t.contar_em_atendimento(),
                     limite=t.limite_chamados,
                     chamados=[self.dados_chamado(c) for c in t.chamados_atribuidos])
                for t in self.sistema.listar_tecnicos()]

    def alterar_senha(self, atual, nova):
        if not isinstance(atual, str) or not isinstance(nova, str):
            raise ValueError("Informe a senha atual e a nova senha.")
        self.usuario_atual().alterar_senha(atual, nova)

    def listar_chamados(self):
        return [self.dados_chamado(chamado) for chamado in self.sistema.listar_chamados(self.usuario_atual())]

    def abrir_chamado(self, dados):
        chamado = self.sistema.abrir_chamado(
            self.usuario_atual(), texto_obrigatorio(dados.get('titulo'), 'título'),
            texto_obrigatorio(dados.get('descricao'), 'descrição'),
            opcao(Categoria, dados.get('categoria')), opcao(Prioridade, dados.get('prioridade')),
        )
        return self.dados_chamado(chamado)

    def buscar_chamado(self, chamado_id):
        for chamado in self.sistema.listar_chamados(self.usuario_atual()):
            if chamado.id == chamado_id:
                return chamado
        raise ErroSistema("Chamado não encontrado para sua conta.", "nao_encontrado")

    def consultar_chamado(self, chamado_id):
        return self.dados_chamado(self.buscar_chamado(chamado_id))

    def assumir_chamado(self, chamado_id):
        usuario = self.usuario_atual()
        if not usuario.possui_permissao(Permissao.ATENDER_CHAMADO):
            raise ErroSistema("Somente técnicos podem assumir chamados.", "permissao")
        chamado = self.buscar_chamado(chamado_id)
        usuario.assumir_chamado(chamado)
        return self.dados_chamado(chamado)

    def cancelar_chamado(self, chamado_id):
        chamado = self.buscar_chamado(chamado_id)
        chamado.cancelar(self.usuario_atual())
        return self.dados_chamado(chamado)

    def listar_atendimentos(self, chamado_id):
        return [{"autor": self.dados_usuario(registro.autor), "tipo": registro.tipo.name,
                 "descricao": registro.descricao, "data_hora": registro.data_hora.isoformat(),
                 "status_anterior": registro.status_anterior.name, "status_novo": registro.status_novo.name}
                for registro in self.buscar_chamado(chamado_id).listar_historico()]

    def registrar_atendimento(self, chamado_id, dados):
        chamado = self.buscar_chamado(chamado_id)
        status = opcao(StatusChamado, dados['novo_status']) if dados.get('novo_status') else None
        chamado.registrar_atendimento(self.usuario_atual(), opcao(TipoAtendimento, dados.get('tipo')),
                                     texto_obrigatorio(dados.get('descricao'), 'descrição'), status)
        return self.dados_chamado(chamado)

    def listar_equipamentos(self, apenas_ativos=True):
        return [self.dados_equipamento(e) for e in self.sistema.listar_equipamentos(self.usuario_atual(), apenas_ativos)]

    def buscar_equipamento(self, codigo):
        for equipamento in self.sistema.listar_equipamentos(self.usuario_atual(), False):
            if equipamento.codigo == codigo:
                return equipamento
        raise ErroSistema("Equipamento não encontrado.", "nao_encontrado")

    def cadastrar_equipamento(self, dados):
        equipamento = self.sistema.cadastrar_equipamento(
            self.usuario_atual(), texto_obrigatorio(dados.get('codigo'), 'código'),
            texto_obrigatorio(dados.get('descricao'), 'descrição'), texto_obrigatorio(dados.get('tipo'), 'tipo'),
            inteiro(dados.get('quantidade', 0), 'Quantidade inicial'),
            inteiro(dados.get('quantidade_minima', 0), 'Quantidade mínima'))
        return self.dados_equipamento(equipamento)

    def atualizar_equipamento(self, codigo, dados):
        self.sistema.atualizar_equipamento(self.usuario_atual(), codigo,
            texto_obrigatorio(dados.get('descricao'), 'descrição'),
            inteiro(dados.get('quantidade_minima'), 'Quantidade mínima'))
        return self.dados_equipamento(self.buscar_equipamento(codigo))

    def repor_equipamento(self, codigo, quantidade, motivo):
        self.sistema.repor_equipamento(self.usuario_atual(), codigo, inteiro(quantidade, 'Quantidade', 1),
                                      texto_obrigatorio(motivo, 'motivo da reposição'))
        return self.dados_equipamento(self.buscar_equipamento(codigo))

    def registrar_saida_equipamento(self, codigo, quantidade, chamado_id):
        quantidade = inteiro(quantidade, 'Quantidade', 1)
        chamado = self.buscar_chamado(chamado_id)
        self.sistema.registrar_saida_equipamento(self.usuario_atual(), codigo, quantidade, chamado)
        return self.dados_equipamento(self.buscar_equipamento(codigo))

    def dar_baixa_equipamento(self, codigo, motivo):
        self.sistema.dar_baixa_equipamento(self.usuario_atual(), codigo, texto_obrigatorio(motivo, 'motivo da baixa'))
        return self.dados_equipamento(self.buscar_equipamento(codigo))

    def listar_movimentacoes(self, codigo):
        return [dict(data_hora=m.data_hora.isoformat(), tipo=m.tipo.name, quantidade=m.quantidade,
                     motivo=m.motivo, responsavel=self.dados_usuario(m.responsavel),
                     chamado_id=m.chamado.id if m.chamado else None)
                for m in self.buscar_equipamento(codigo).listar_movimentacoes()]

    def dados_equipamento(self, e):
        return dict(codigo=e.codigo, descricao=e.descricao, tipo=e.tipo, quantidade=e.quantidade,
                    quantidade_minima=e.quantidade_minima, ativo=e.ativo, abaixo_do_minimo=e.abaixo_do_minimo())

    def dados_usuario(self, usuario):
        return {"id": usuario.id, "nome": usuario.nome, "email": usuario.email, "perfil": usuario.obter_perfil(),
                "ativo": usuario.esta_ativo(), "setor": getattr(usuario, 'setor', ''),
                "especialidade": getattr(usuario, 'especialidade', ''), "cargo": getattr(usuario, 'cargo', '')}

    def dados_chamado(self, chamado):
        # As telas recebem somente os campos que precisam exibir.
        return {"id": chamado.id, "titulo": chamado.titulo, "descricao": chamado.descricao,
                "categoria": chamado.categoria.name, "prioridade": chamado.prioridade.name,
                "status": chamado.status.name, "solicitante": self.dados_usuario(chamado.solicitante),
                "responsavel": self.dados_usuario(chamado.responsavel) if chamado.responsavel else None,
                "data_abertura": chamado.data_abertura.isoformat(),
                "data_encerramento": chamado.data_encerramento.isoformat() if chamado.data_encerramento else None}
