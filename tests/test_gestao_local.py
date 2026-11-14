import unittest

from helpdesk.excecoes import HelpDeskError
from sistema_local import ErroSistema, SistemaLocal


class TestGestaoLocal(unittest.TestCase):
    def setUp(self):
        self.s = SistemaLocal()
        self.admin()
        self.tecnico = self.s.cadastrar_usuario(dict(nome='Carlos', email='tecnico@teste.com', senha='1234',
                                                     perfil='tecnico', especialidade='Hardware'))
        self.comum = self.s.cadastrar_usuario(dict(nome='Ana', email='ana@teste.com', senha='1234',
                                                   perfil='comum', setor='Compras'))

    def admin(self):
        return self.s.login('marina@empresa.com', 'admin123')

    def preparar_estoque(self):
        self.s.login('ana@teste.com', '1234')
        c = self.s.abrir_chamado(dict(titulo='Trocar teclado', descricao='Teclado não funciona.',
                                     categoria='HARDWARE', prioridade='MEDIA'))
        self.s.login('tecnico@teste.com', '1234')
        self.s.assumir_chamado(c['id'])
        self.s.cadastrar_equipamento(dict(codigo='TEC-1', descricao='Teclado USB', tipo='Periférico',
                                          quantidade='2', quantidade_minima='2'))
        return c['id']

    def test_autocadastro_e_login_por_area(self):
        self.s.logout()
        dados = dict(nome='Bia', email='bia@teste.com', senha='1234', setor='Financeiro')
        with self.assertRaises(ErroSistema):
            self.s.cadastrar_conta(dict(dados, perfil='administrador'))
        conta = self.s.cadastrar_conta(dados)
        self.assertEqual(conta['perfil'], 'Usuário Comum')
        with self.assertRaises(ErroSistema):
            self.s.login('bia@teste.com', '1234', 'administrativo')
        self.assertIsNone(self.s.usuario)
        self.s.login('bia@teste.com', '1234', 'principal')
        with self.assertRaises(ErroSistema):
            self.s.login('marina@empresa.com', 'admin123', 'principal')
        self.assertEqual(self.s.login('marina@empresa.com', 'admin123', 'administrativo')['perfil'], 'Administrador')

    def test_gestao_tecnicos_bloqueio_e_administradores(self):
        self.s.atualizar_tecnico(self.tecnico['id'], dict(nome='Carlos Silva', especialidade='Redes'))
        cadastros = {u['id']: u for u in self.s.listar_usuarios()}
        self.assertEqual(cadastros[self.tecnico['id']]['especialidade'], 'Redes')
        self.s.alterar_bloqueio(self.comum['id'], True)
        with self.assertRaises(ErroSistema):
            self.s.login('ana@teste.com', '1234')
        marina = self.admin()
        self.s.alterar_bloqueio(self.comum['id'], False)
        with self.assertRaises(HelpDeskError):
            self.s.desativar_administrador(marina['id'])
        outro = self.s.cadastrar_usuario(dict(nome='Gestor', email='gestor@teste.com', senha='1234',
                                             perfil='administrador', cargo='Gerente'))
        self.s.desativar_administrador(outro['id'])
        self.s.excluir_tecnico(self.tecnico['id'])
        self.assertNotIn(self.tecnico['id'], [u['id'] for u in self.s.listar_usuarios()])

    def test_edicao_invalida_nao_muda_metade_dos_dados(self):
        with self.assertRaises(ValueError):
            self.s.atualizar_tecnico(self.tecnico['id'], dict(nome='Nome novo', especialidade='  '))
        tecnico = next(u for u in self.s.listar_usuarios() if u['id'] == self.tecnico['id'])
        self.assertEqual(tecnico['nome'], 'Carlos')

    def test_exclusao_protegida_historico_e_sessao_excluida(self):
        chamado_id = self.preparar_estoque()
        tecnico_obj = self.s.usuario_atual()
        self.admin()
        with self.assertRaises(HelpDeskError):
            self.s.excluir_tecnico(self.tecnico['id'])
        self.s.login('tecnico@teste.com', '1234')
        self.s.registrar_atendimento(chamado_id, dict(tipo='SOLUCAO', descricao='Teclado substituído.', novo_status='RESOLVIDO'))
        self.admin()
        self.s.excluir_tecnico(self.tecnico['id'])
        self.assertEqual(self.s.listar_atendimentos(chamado_id)[-1]['autor']['nome'], 'Carlos')
        sessao_antiga = SistemaLocal(self.s.sistema, tecnico_obj)
        with self.assertRaises(ErroSistema):
            sessao_antiga.usuario_atual()

    def test_atividades_nao_misturam_homonimos(self):
        chamado_id = self.preparar_estoque()
        self.admin()
        outro = self.s.cadastrar_usuario(dict(nome='Carlos', email='outro@teste.com', senha='1234',
                                             perfil='tecnico', especialidade='Redes'))
        atividades = {u['id']: u for u in self.s.listar_atividades()}
        self.assertEqual(atividades[self.tecnico['id']]['em_atendimento'], 1)
        self.assertEqual(atividades[outro['id']]['em_atendimento'], 0)
        self.assertEqual(atividades[self.tecnico['id']]['chamados'][0]['id'], chamado_id)

    def test_ciclo_estoque_com_historico_e_vinculo(self):
        chamado_id = self.preparar_estoque()
        self.s.repor_equipamento('TEC-1', '3', 'Compra de reposição')
        self.s.registrar_saida_equipamento('TEC-1', '4', chamado_id)
        self.s.atualizar_equipamento('TEC-1', dict(descricao='Teclado ABNT2', quantidade_minima='3'))
        item = self.s.listar_equipamentos()[0]
        self.assertEqual(item['quantidade'], 1)
        self.assertTrue(item['abaixo_do_minimo'])
        movimentos = self.s.listar_movimentacoes('TEC-1')
        self.assertEqual([m['tipo'] for m in movimentos], ['ENTRADA', 'SAIDA'])
        self.assertEqual(movimentos[-1]['chamado_id'], chamado_id)
        self.assertTrue(movimentos[0]['data_hora'])
        self.assertIn('Saída de 4 un.', self.s.listar_atendimentos(chamado_id)[-1]['descricao'])
        self.s.dar_baixa_equipamento('TEC-1', 'Danificado')
        self.assertEqual(self.s.listar_equipamentos(), [])
        self.assertFalse(self.s.listar_equipamentos(False)[0]['ativo'])
        self.assertEqual(self.s.listar_movimentacoes('TEC-1')[-1]['tipo'], 'BAIXA')
        with self.assertRaises(HelpDeskError):
            self.s.repor_equipamento('TEC-1', 1, 'Reposição')

    def test_quantidades_invalidas_ou_chamado_invalido_nao_movimentam(self):
        chamado_id = self.preparar_estoque()
        for quantidade in ('0', '-1', '1.5', 1.5, True, 'abc', ''):
            with self.subTest(quantidade=quantidade), self.assertRaises(ValueError):
                self.s.registrar_saida_equipamento('TEC-1', quantidade, chamado_id)
        with self.assertRaises(HelpDeskError):
            self.s.registrar_saida_equipamento('TEC-1', 3, chamado_id)
        with self.assertRaises(ErroSistema):
            self.s.registrar_saida_equipamento('TEC-1', 1, 9999)
        self.assertEqual(self.s.listar_equipamentos()[0]['quantidade'], 2)
        self.assertEqual(self.s.listar_movimentacoes('TEC-1'), [])

    def test_perfis_nao_autorizados_e_saida_de_outro_tecnico(self):
        chamado_id = self.preparar_estoque()
        self.admin()
        self.s.cadastrar_usuario(dict(nome='Outro', email='outro@teste.com', senha='1234',
                                       perfil='tecnico', especialidade='Redes'))
        with self.assertRaises(HelpDeskError):
            self.s.listar_equipamentos()
        self.s.login('outro@teste.com', '1234')
        with self.assertRaises(ErroSistema):
            self.s.registrar_saida_equipamento('TEC-1', 1, chamado_id)
        with self.assertRaises(ErroSistema):
            self.s.listar_usuarios()
        with self.assertRaises(ErroSistema):
            self.s.listar_atividades()
        self.assertEqual(self.s.listar_equipamentos()[0]['quantidade'], 2)

    def test_alterar_senha(self):
        self.s.login('ana@teste.com', '1234')
        with self.assertRaises(HelpDeskError):
            self.s.alterar_senha('errada', 'nova123')
        self.s.alterar_senha('1234', 'nova123')
        self.s.logout()
        self.assertEqual(self.s.login('ana@teste.com', 'nova123')['nome'], 'Ana')
