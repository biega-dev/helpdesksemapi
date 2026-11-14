# Help Desk — Tkinter local

Sistema de chamados, atendimento técnico, estoque e administração de usuários.
Segue os 24 casos de uso dos documentos em [docs/modelagem](docs/modelagem),
reenviados em 14/11/2026. Python 3.10+ e biblioteca padrão, sem API ou banco.

## Abrir

No Windows, abra **iniciar.bat**, ou execute `python main.py` nesta pasta.
O Python precisa incluir Tkinter (opção padrão do instalador para Windows).

- **Aplicativo Principal:** usuários comuns e técnicos. “Criar minha conta” cria
  somente usuário comum, com nome, e-mail, setor e senha.
- **Painel Administrativo:** administradores. Conta inicial de demonstração:
  `marina@empresa.com`, senha `admin123`.
- `python painel_admin.py` abre a entrada administrativa diretamente.

Para demonstrar os perfis **com os mesmos dados**, mantenha uma janela aberta e
use “Sair da conta”, selecione a área e entre com outra conta. Sair preserva os
registros; **fechar o programa descarta todos os dados da execução**. Processos
separados não compartilham dados. Para dois computadores, use `helpdeskteste`.

## Telas e casos de uso

| Área | Operações | Casos de uso |
| --- | --- | --- |
| Entrada | Autocadastro comum; login separado por área | UC01, UC06, UC16 |
| Chamados do usuário | Abrir, consultar, cancelar enquanto aberto, histórico | UC02–UC05 |
| Chamados do técnico | Fila, assumir, registrar atendimento, atualizar status | UC07–UC10 |
| Equipamentos no chamado | Saída de estoque vinculada e registrada no histórico | UC11 |
| Estoque | Cadastro, consulta, edição, reposição, baixa e movimentações | UC12–UC15 |
| Usuários (admin) | Gestão de técnicos, bloqueio/desbloqueio e gestão de administradores | UC17–UC22 |
| Chamados da empresa (admin) | Consultar todos os chamados e históricos | UC23 |
| Equipe (admin) | Carga, pendências, resolvidos e chamados por técnico | UC24 |

“Minha senha” permite trocar a própria senha, informando a atual. As regras
RN01–RN06 continuam nas classes: cancelamento só pelo solicitante enquanto aberto;
limite de cinco atendimentos por técnico; solução obrigatória para resolver;
estoque não negativo e sem movimentação após baixa; exclusão de técnico impedida
quando em atendimento; preservação do último administrador ativo.

## Demonstrar

1. Entre como administrador, cadastre um técnico e confira Usuários/Equipe.
2. Saia, selecione Aplicativo Principal, crie uma conta comum e abra um chamado.
3. Entre como técnico, assuma o chamado e cadastre equipamentos em Estoque.
4. Faça uma reposição; no chamado, registre uma saída na aba Equipamentos.
5. Confira o saldo e as Movimentações; registre atendimento e finalize com solução.
6. Volte ao administrador para consultar a equipe, editar, bloquear/desbloquear
   e excluir um técnico sem chamados em atendimento.

## Código e verificação

- `helpdesk/`: domínio do público main `d324b73`. Única extensão nesta cópia
  privada: data/tipo de movimentação previstos no UML. Público não alterado.
- `sistema_local.py`: sessão, validação de campos e adaptação para as telas.
- `aplicacao.py`, `telas/`: interface e tratamento de erros.
- `docs/modelagem/`: exatamente os documentos novos fornecidos pelo grupo.
- `exemplos/demonstracao_terminal.py`: demonstração original.

Execute `python -m unittest discover -v`. Os testes incluem os fluxos gráficos
com conexões de rede bloqueadas. Não há e-mail, SLA, banco ou integrações externas.
A visibilidade do técnico segue o código público: fila aberta e chamados que ele
atende. Administradores consultam todos os chamados.
