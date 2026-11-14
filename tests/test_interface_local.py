import gc
import socket
import time
import unittest
from unittest.mock import patch

from aplicacao import Aplicacao
from telas.chamados import DetalheChamado, NovoChamado
from telas.usuarios import CadastroUsuario


class TestInterfaceLocal(unittest.TestCase):
    def setUp(self):
        bloqueio = patch.object(socket.socket, 'connect', side_effect=AssertionError('Conexão de rede não permitida.'))
        bloqueio.start()
        self.addCleanup(bloqueio.stop)
        self.app = Aplicacao()
        self.app.withdraw()
        self.app.update()
        self.erros = []
        for nome in ('showinfo', 'showwarning', 'showerror'):
            remendo = patch(f'tkinter.messagebox.{nome}')
            if nome == 'showerror':
                remendo = patch('tkinter.messagebox.showerror', side_effect=lambda *args, **kw: self.erros.append(args))
            remendo.start()
            self.addCleanup(remendo.stop)
        confirmacao = patch('tkinter.messagebox.askyesno', return_value=True)
        confirmacao.start()
        self.addCleanup(confirmacao.stop)

    def tearDown(self):
        self.app.destroy()
        del self.app
        gc.collect()

    def aguardar(self):
        limite = time.monotonic() + 3
        while self.app.ocupado and time.monotonic() < limite:
            self.app.update()
            time.sleep(0.005)
        self.app.update()
        self.assertFalse(self.app.ocupado)

    def preencher(self, campo, valor):
        campo.delete(0, 'end')
        campo.insert(0, valor)

    def login(self, email, senha='teste123'):
        self.preencher(self.app.tela.email, email)
        self.preencher(self.app.tela.senha, senha)
        self.app.tela.entrar()
        self.aguardar()
        self.assertEqual(self.app.servico.usuario['email'], email)

    def test_fluxo_pelas_telas_com_troca_de_perfil_sem_internet(self):
        self.login('marina@empresa.com', 'admin123')
        for nome, perfil, complemento in [('ana', 'Usuário Comum', 'Financeiro'), ('carlos', 'Técnico de TI', 'Sistemas')]:
            self.app.abrir_dialogo(CadastroUsuario)
            form = self.app.dialogo
            for widget, valor in [(form.nome, nome), (form.email, f'{nome}@teste.com'),
                                  (form.senha, 'teste123'), (form.confirmacao, 'teste123'), (form.complemento, complemento)]:
                self.preencher(widget, valor)
            form.perfil.set(perfil)
            form.atualizar_perfil()
            form.salvar()
            self.aguardar()
            self.assertFalse(form.winfo_exists())
        self.app.sair()
        self.login('ana@teste.com')
        self.app.abrir_dialogo(NovoChamado)
        form = self.app.dialogo
        self.preencher(form.titulo, 'Erro na emissão do relatório')
        form.descricao.insert('1.0', 'O relatório de estoque não é gerado.')
        form.salvar()
        self.aguardar()
        chamado_id = self.app.tela.chamados[0]['id']
        self.app.tela.busca.set('emissao')
        self.assertEqual(self.app.tela.tabela.get_children(), (str(chamado_id),))
        self.app.tela.tabela.selection_set(str(chamado_id))
        self.app.tela.atualizar()
        self.aguardar()
        self.assertEqual(self.app.tela.tabela.selection(), (str(chamado_id),))
        self.assertEqual(self.app.tela.busca.get(), 'emissao')
        self.app.sair()
        self.login('carlos@teste.com')
        self.app.abrir_dialogo(DetalheChamado, chamado_id)
        self.aguardar()
        detalhe = self.app.dialogo
        detalhe.assumir()
        self.aguardar()
        self.assertEqual(detalhe.chamado['status'], 'EM_ATENDIMENTO')
        detalhe.tipo.set('Observação')
        detalhe.novo_status.set('Pendente')
        detalhe.descricao.insert('1.0', 'Aguardando o arquivo de exemplo.')
        detalhe.registrar()
        self.aguardar()
        self.assertEqual(detalhe.chamado['status'], 'PENDENTE')
        detalhe.tipo.set('Solução')
        detalhe.novo_status.set('Resolvido')
        detalhe.descricao.insert('1.0', 'Ajustado o filtro de produtos do relatório.')
        detalhe.registrar()
        self.aguardar()
        self.assertEqual(detalhe.chamado['status'], 'RESOLVIDO')
        detalhe.fechar()
        self.aguardar()
        self.app.sair()
        self.login('ana@teste.com')
        self.assertEqual(self.app.tela.chamados[0]['status'], 'RESOLVIDO')
        self.app.abrir_dialogo(DetalheChamado, chamado_id)
        self.aguardar()
        self.assertIn('Ajustado o filtro', self.app.dialogo.texto_historico.get('1.0', 'end'))
        self.assertEqual(self.erros, [])

    def test_cancelamento_na_tela_encerra_chamado(self):
        self.app.servico.login('marina@empresa.com', 'admin123')
        self.app.servico.cadastrar_usuario({'nome': 'Ana', 'email': 'ana@teste.com', 'senha': 'teste123',
                                           'perfil': 'comum', 'setor': 'Financeiro'})
        self.login('ana@teste.com')
        chamado = self.app.servico.abrir_chamado({'titulo': 'Duplicado', 'descricao': 'Aberto por engano.',
                                                'categoria': 'SOFTWARE', 'prioridade': 'BAIXA'})
        self.app.abrir_dialogo(DetalheChamado, chamado['id'])
        self.aguardar()
        self.app.dialogo.cancelar()
        self.aguardar()
        self.assertEqual(self.app.dialogo.chamado['status'], 'CANCELADO')
        self.assertTrue(self.app.dialogo.botao_cancelar.instate(['disabled']))
        self.assertEqual(self.erros, [])


if __name__ == '__main__':
    unittest.main()
