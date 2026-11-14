from helpdesk.enums import Categoria, Permissao, Prioridade, StatusChamado, TipoAtendimento
from helpdesk.helpdesk import HelpDesk
from helpdesk.usuarios import Administrador


class ErroSistema(Exception):
    def __init__(self, mensagem, motivo=None):
        super().__init__(mensagem)
        self.motivo = motivo


class SistemaLocal:
    def __init__(self):
        admin = Administrador("Marina Souza", "marina@empresa.com", "admin123", "Gerente de TI")
        self.sistema = HelpDesk("Help Desk", admin)
        self._usuario_logado = None
        self.usuario = None

    def limpar_sessao(self):
        self._usuario_logado = None
        self.usuario = None

    def login(self, email, senha):
        self.limpar_sessao()
        usuario = self.sistema.autenticar(email, senha, Permissao.ACESSAR_APLICATIVO)
        if usuario is None:
            usuario = self.sistema.autenticar(email, senha, Permissao.ACESSAR_PAINEL_ADMIN)
        if usuario is None:
            raise ErroSistema("E-mail ou senha inválidos.", "acesso")
        self._usuario_logado = usuario
        self.usuario = self.dados_usuario(usuario)
        return self.usuario

    def logout(self):
        self.limpar_sessao()

    def usuario_atual(self):
        if self._usuario_logado is None or not self._usuario_logado.esta_ativo():
            self.limpar_sessao()
            raise ErroSistema("Entre novamente para continuar.", "acesso")
        return self._usuario_logado

    def cadastrar_usuario(self, dados):
        admin = self.usuario_atual()
        if not admin.possui_permissao(Permissao.GERENCIAR_USUARIOS):
            raise ErroSistema("Somente administradores podem cadastrar usuários.")
        nome, email, senha = dados['nome'], dados['email'], dados['senha']
        if dados['perfil'] == 'comum':
            usuario = self.sistema.cadastrar_usuario_comum(nome, email, senha, dados['setor'])
        elif dados['perfil'] == 'tecnico':
            usuario = self.sistema.cadastrar_tecnico(admin, nome, email, senha, dados['especialidade'])
        elif dados['perfil'] == 'administrador':
            usuario = self.sistema.cadastrar_administrador(admin, nome, email, senha, dados['cargo'])
        else:
            raise ErroSistema("Perfil de usuário inválido.")
        return self.dados_usuario(usuario)

    def listar_chamados(self):
        return [self.dados_chamado(chamado) for chamado in self.sistema.listar_chamados(self.usuario_atual())]

    def abrir_chamado(self, dados):
        chamado = self.sistema.abrir_chamado(
            self.usuario_atual(), dados['titulo'], dados['descricao'],
            Categoria[dados['categoria']], Prioridade[dados['prioridade']],
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
            raise ErroSistema("Somente técnicos podem assumir chamados.")
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
        status = StatusChamado[dados['novo_status']] if dados.get('novo_status') else None
        chamado.registrar_atendimento(self.usuario_atual(), TipoAtendimento[dados['tipo']], dados['descricao'], status)
        return self.dados_chamado(chamado)

    def dados_usuario(self, usuario):
        return {"id": usuario.id, "nome": usuario.nome, "email": usuario.email, "perfil": usuario.obter_perfil()}

    def dados_chamado(self, chamado):
        # As telas recebem somente os campos que precisam exibir.
        return {"id": chamado.id, "titulo": chamado.titulo, "descricao": chamado.descricao,
                "categoria": chamado.categoria.name, "prioridade": chamado.prioridade.name,
                "status": chamado.status.name, "solicitante": self.dados_usuario(chamado.solicitante),
                "responsavel": self.dados_usuario(chamado.responsavel) if chamado.responsavel else None,
                "data_abertura": chamado.data_abertura.isoformat(),
                "data_encerramento": chamado.data_encerramento.isoformat() if chamado.data_encerramento else None}
