# Help Desk — versão local em Tkinter

Aplicação desktop em Python, sem API, servidor, conexão de rede ou banco de dados.
As telas usam diretamente as classes do projeto original por meio de `SistemaLocal`.

## Executar

Instale Python 3.10 ou superior com Tkinter e execute nesta pasta:

```powershell
python main.py
```

No Windows, também é possível abrir `iniciar.bat`.
Não é necessário instalar bibliotecas com pip. Tkinter acompanha a instalação
padrão do Python para Windows.

## Primeiro acesso

O programa começa com a mesma administradora da demonstração original:

- E-mail: `marina@empresa.com`
- Senha: `admin123`

Esse é um acesso de demonstração local. Entre com ele e use **Cadastrar usuário**
para criar contas comuns, técnicas ou outro administrador. As demais contas não
são criadas automaticamente.

## Telas

- Login com e-mail e senha.
- Painel de chamados com resumo, busca, filtros e atualização.
- Cadastro de usuários pelo administrador, com campo de setor, especialidade ou cargo.
- Abertura de chamado pelo usuário comum.
- Detalhes e histórico de atendimento.
- Cancelamento de chamado aberto pelo solicitante.
- Técnico assume, registra diagnóstico/observação/solução e altera o status.

As telas mantêm o mesmo fluxo da versão com API. A diferença é que cada ação
chama métodos dos objetos Python que estão na memória do próprio programa.
O backend original decide as permissões e as regras de negócio.

## Demonstrar no trabalho

1. Abra o programa e entre como Marina.
2. Cadastre um usuário comum e um técnico, anotando os acessos escolhidos.
3. Clique em **Sair da conta**, sem fechar a janela.
4. Entre como usuário comum e abra um chamado sobre um erro em um sistema.
5. Saia da conta e entre como técnico. Abra o chamado e clique em **Assumir chamado**.
6. Na aba **Registrar atendimento**, registre um diagnóstico ou uma pendência.
7. Registre uma Solução, escolhendo o status Resolvido.
8. Volte à conta do solicitante e consulte o status e o histórico.

**Sair da conta mantém os dados. Fechar o programa apaga os dados da execução.**
Cada janela iniciada em outro processo é independente. Esta versão não compartilha
chamados entre computadores, pois não usa servidor nem arquivos de persistência.

## Estrutura

- `main.py`: inicia o Tkinter.
- `aplicacao.py`: controla a janela e a navegação.
- `sistema_local.py`: mantém o usuário logado, chama o domínio e prepara os campos para as telas.
- `telas/`: login, painel, cadastro, chamados e componentes visuais.
- `helpdesk/`: classes originais de usuários, chamados, atendimentos e estoque.
- `tests/`: testes originais e testes da integração local com as telas.
- `exemplos/demonstracao_terminal.py`: demonstração original pelo terminal.

As classes em `helpdesk/` foram copiadas sem alterações da `main` do projeto
original, revisão `d324b73`. Isso preserva herança, encapsulamento, polimorfismo,
classes abstratas, exceções e regras de negócio já implementadas pelo grupo.

O módulo de estoque e os métodos de edição/bloqueio de contas continuam no domínio
original. As telas desta versão são as mesmas da versão com API e não incluem
interfaces para essas operações adicionais.

Para executar a demonstração original completa (incluindo estoque e administração):

```powershell
python -m exemplos.demonstracao_terminal
```

## Testes

```powershell
python -m unittest discover -s tests
```

Os testes incluem o domínio original, isolamento dos chamados por usuário, troca
de perfil, filtros, cancelamento, atendimento e resolução. O teste de fluxo local
bloqueia conexões de rede para confirmar que o programa funciona sem servidor.

## Integrantes

Vinicius Begnini Felicio, Gabriel Verruck, Guilherme Bortoletti e Mateus Biegalski.
