import socket
import unittest
from unittest.mock import patch


class TestSistemaLocal(unittest.TestCase):
    def setUp(self):
        from sistema_local import SistemaLocal
        self.servico = SistemaLocal()

    def test_fluxo_completo_sem_rede(self):
        with patch.object(socket.socket, 'connect', side_effect=AssertionError('A versão local não pode conectar à rede.')):
            self.servico.login('marina@empresa.com', 'admin123')
            self.servico.cadastrar_usuario({'nome': 'Ana', 'email': 'ana@teste.com', 'senha': 'ana123',
                                          'perfil': 'comum', 'setor': 'Financeiro'})
            self.servico.cadastrar_usuario({'nome': 'Carlos', 'email': 'carlos@teste.com', 'senha': 'carlos123',
                                          'perfil': 'tecnico', 'especialidade': 'Sistemas'})
            self.servico.logout()
            self.servico.login('ana@teste.com', 'ana123')
            chamado = self.servico.abrir_chamado({'titulo': 'Erro no estoque', 'descricao': 'A entrada não foi salva.',
                                                'categoria': 'SOFTWARE', 'prioridade': 'ALTA'})
            self.servico.logout()
            self.servico.login('carlos@teste.com', 'carlos123')
            self.assertEqual(len(self.servico.listar_chamados()), 1)
            self.servico.assumir_chamado(chamado['id'])
            self.servico.registrar_atendimento(chamado['id'], {'tipo': 'SOLUCAO', 'descricao': 'Corrigida a configuração.',
                                                              'novo_status': 'RESOLVIDO'})
            self.servico.logout()
            self.servico.login('ana@teste.com', 'ana123')
            self.assertEqual(self.servico.consultar_chamado(chamado['id'])['status'], 'RESOLVIDO')
            self.assertEqual(self.servico.listar_atendimentos(chamado['id'])[-1]['descricao'], 'Corrigida a configuração.')

    def test_usuario_comum_nao_cadastra_contas_nem_ve_chamados_alheios(self):
        from sistema_local import ErroSistema
        self.servico.login('marina@empresa.com', 'admin123')
        for nome in ('ana', 'bruno'):
            self.servico.cadastrar_usuario({'nome': nome, 'email': f'{nome}@teste.com', 'senha': '1234',
                                          'perfil': 'comum', 'setor': 'Financeiro'})
        self.servico.login('ana@teste.com', '1234')
        chamado = self.servico.abrir_chamado({'titulo': 'Dúvida', 'descricao': 'Como fechar o mês?',
                                            'categoria': 'SOFTWARE', 'prioridade': 'MEDIA'})
        with self.assertRaises(ErroSistema):
            self.servico.cadastrar_usuario({'nome': 'Intruso'})
        self.servico.login('bruno@teste.com', '1234')
        self.assertEqual(self.servico.listar_chamados(), [])
        with self.assertRaises(ErroSistema):
            self.servico.consultar_chamado(chamado['id'])

    def test_login_errado_e_logout_nao_mantem_acesso_anterior(self):
        from sistema_local import ErroSistema
        self.servico.login('marina@empresa.com', 'admin123')
        with self.assertRaises(ErroSistema):
            self.servico.login('marina@empresa.com', 'senhaerrada')
        self.assertIsNone(self.servico.usuario)
        with self.assertRaises(ErroSistema):
            self.servico.listar_chamados()

    def test_nova_execucao_comeca_sem_chamados(self):
        from sistema_local import SistemaLocal
        self.servico.login('marina@empresa.com', 'admin123')
        self.servico.cadastrar_usuario({'nome': 'Ana', 'email': 'ana@teste.com', 'senha': '1234',
                                      'perfil': 'comum', 'setor': 'Financeiro'})
        outra_execucao = SistemaLocal()
        outra_execucao.login('marina@empresa.com', 'admin123')
        self.assertEqual(outra_execucao.listar_chamados(), [])
        self.assertEqual(len(outra_execucao.sistema.usuarios), 1)


if __name__ == '__main__':
    unittest.main()
