from tests import test_interface_local as ambiente
from telas.estoque import CadastroEquipamento, MovimentarEquipamento, HistoricoEquipamento
from telas.usuarios import CadastroUsuario, EditarTecnico


class TestInterfaceGestao(ambiente.TestInterfaceLocal):
    # Reutiliza o ambiente gráfico com sockets bloqueados, sem executar novamente os testes herdados.
    test_fluxo_pelas_telas_com_troca_de_perfil_sem_internet = None
    test_cancelamento_na_tela_encerra_chamado = None

    def login(self, email, senha='teste123'):
        self.app.tela.acesso.set('administrativo' if email == 'marina@empresa.com' else 'principal')
        super().login(email, senha)

    def preparar(self):
        self.login('marina@empresa.com', 'admin123')
        for nome, perfil, atributo in [('ana', 'comum', 'setor'), ('carlos', 'tecnico', 'especialidade')]:
            self.app.servico.cadastrar_usuario(dict(nome=nome, email=f'{nome}@teste.com', senha='teste123',
                                                    perfil=perfil, **{atributo: 'TI'}))

    def pagina(self, nome):
        painel = self.app.tela
        painel.abas.select(painel.paginas[nome])
        self.app.update()
        self.aguardar()
        return painel.paginas[nome]

    def test_autocadastro_na_tela_nao_oferece_perfil_privilegiado(self):
        self.app.tela.cadastrar_conta()
        form = self.app.dialogo
        self.assertTrue(form.autocadastro)
        self.assertEqual(tuple(form.perfil['values']), ('Usuário Comum',))
        for campo, valor in [(form.nome, 'Ana'), (form.email, 'ana@teste.com'), (form.senha, 'teste123'),
                              (form.confirmacao, 'teste123'), (form.complemento, 'Compras')]:
            self.preencher(campo, valor)
        form.salvar()
        self.aguardar()
        self.login('ana@teste.com')
        self.assertEqual(set(self.app.tela.paginas), {'Chamados'})
        self.assertEqual(self.erros, [])

    def test_estoque_pelas_telas_e_saida_integrada_ao_chamado(self):
        from telas.chamados import DetalheChamado
        self.preparar()
        self.app.sair()
        self.login('ana@teste.com')
        chamado = self.app.servico.abrir_chamado(dict(titulo='Mouse parou', descricao='Trocar o mouse.',
                                                    categoria='HARDWARE', prioridade='MEDIA'))
        self.app.sair()
        self.login('carlos@teste.com')
        estoque = self.pagina('Estoque')
        self.app.abrir_dialogo(CadastroEquipamento)
        form = self.app.dialogo
        for widget, valor in [(form.codigo, 'MOU-1'), (form.descricao, 'Mouse USB'), (form.tipo, 'Periférico'),
                              (form.quantidade, '2'), (form.minimo, '2')]:
            self.preencher(widget, valor)
        form.salvar()
        self.aguardar()
        self.assertEqual(len(estoque.tabela.get_children()), 1)
        equipamento = estoque.equipamentos[0]
        self.app.abrir_dialogo(MovimentarEquipamento, equipamento, 'entrada')
        form = self.app.dialogo
        self.preencher(form.quantidade, '3')
        self.preencher(form.motivo, 'Compra')
        form.salvar()
        self.aguardar()
        self.app.abrir_dialogo(DetalheChamado, chamado['id'])
        self.aguardar()
        detalhe = self.app.dialogo
        detalhe.assumir()
        self.aguardar()
        detalhe.equipamento.current(0)
        self.preencher(detalhe.quantidade_saida, '4')
        detalhe.registrar_saida()
        self.aguardar()
        self.assertIn('Saída de 4 un.', detalhe.texto_historico.get('1.0', 'end'))
        detalhe.fechar()
        self.aguardar()
        self.assertEqual(estoque.equipamentos[0]['quantidade'], 1)
        estoque.filtro.set('Abaixo do mínimo')
        self.assertEqual(len(estoque.tabela.get_children()), 1)
        self.app.abrir_dialogo(HistoricoEquipamento, estoque.equipamentos[0])
        self.aguardar()
        self.assertEqual(len(self.app.dialogo.tabela.get_children()), 2)
        self.app.dialogo.fechar()
        self.app.abrir_dialogo(MovimentarEquipamento, estoque.equipamentos[0], 'baixa')
        self.preencher(self.app.dialogo.motivo, 'Item danificado')
        self.app.dialogo.salvar()
        self.aguardar()
        self.assertEqual(estoque.tabela.get_children(), ())
        estoque.filtro.set('Baixados')
        self.assertEqual(len(estoque.tabela.get_children()), 1)
        self.assertEqual(self.erros, [])

    def test_administracao_edicao_bloqueio_e_equipe(self):
        self.preparar()
        usuarios = self.pagina('Usuários')
        self.assertNotIn('Estoque', self.app.tela.paginas)
        tecnico = next(u for u in usuarios.usuarios if u['perfil'] == 'Técnico de TI')
        self.app.abrir_dialogo(EditarTecnico, tecnico)
        self.preencher(self.app.dialogo.nome, 'Carlos Silva')
        self.preencher(self.app.dialogo.especialidade, 'Redes')
        self.app.dialogo.salvar()
        self.aguardar()
        linha = usuarios.tabela.item(str(tecnico['id']))['values']
        self.assertIn('Carlos Silva', linha)
        usuarios.tabela.selection_set(str(tecnico['id']))
        usuarios.bloquear()
        self.aguardar()
        self.assertIn('Bloqueado', usuarios.tabela.item(str(tecnico['id']))['values'])
        usuarios.bloquear()
        self.aguardar()
        equipe = self.pagina('Equipe')
        self.assertEqual(len(equipe.tabela.get_children()), 1)
        self.assertEqual(self.erros, [])

    def test_acoes_visiveis_no_tamanho_minimo(self):
        self.preparar()
        self.app.deiconify()
        self.app.geometry('940x650')
        for nome in ('Usuários', 'Equipe', 'Chamados'):
            pagina = self.pagina(nome)
            self.app.update_idletasks()
            def verificar(widget):
                for filho in widget.winfo_children():
                    if filho.winfo_class() == 'TButton':
                        self.assertTrue(filho.winfo_ismapped(), filho.cget('text'))
                        self.assertLessEqual(filho.winfo_rooty() + filho.winfo_height(), self.app.winfo_rooty() + self.app.winfo_height(), filho.cget('text'))
                        self.assertLessEqual(filho.winfo_rootx() + filho.winfo_width(), self.app.winfo_rootx() + self.app.winfo_width(), filho.cget('text'))
                    verificar(filho)
            verificar(pagina)
        self.assertEqual(self.erros, [])

    def test_saida_preserva_equipamento_por_codigo_e_nao_escolhe_outro_apos_baixa(self):
        from telas.chamados import DetalheChamado
        self.preparar()
        self.app.sair()
        self.aguardar()
        self.login('ana@teste.com')
        c = self.app.servico.abrir_chamado(dict(titulo='Troca', descricao='Trocar periféricos.', categoria='HARDWARE', prioridade='MEDIA'))
        self.app.sair()
        self.aguardar()
        self.login('carlos@teste.com')
        self.app.servico.assumir_chamado(c['id'])
        for codigo in ('A', 'B'):
            self.app.servico.cadastrar_equipamento(dict(codigo=codigo, descricao=codigo, tipo='Periférico', quantidade=3, quantidade_minima=1))
        self.app.abrir_dialogo(DetalheChamado, c['id'])
        self.aguardar()
        detalhe = self.app.dialogo
        detalhe.equipamento.current(1)
        detalhe.registrar_saida()
        self.aguardar()
        self.assertEqual(detalhe.equipamentos[detalhe.equipamento.current()]['codigo'], 'B')
        self.app.servico.dar_baixa_equipamento('B', 'Inativado')
        detalhe.atualizar()
        self.aguardar()
        self.assertEqual(detalhe.equipamento.current(), -1)
        self.assertTrue(detalhe.botao_saida.instate(['disabled']))
        detalhe.atualizar()
        self.aguardar()
        self.assertEqual(detalhe.equipamento.current(), -1)
        self.assertEqual(self.erros, [])
