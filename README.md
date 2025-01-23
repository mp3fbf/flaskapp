# Gerenciador de Assinaturas

Um aplicativo web para gerenciar suas assinaturas pessoais, construído com Flask, SQLite e HTMX.

## Funcionalidades

- Cadastro manual de assinaturas
- Cálculo automático de custos mensais/anuais
- Suporte a múltiplas moedas
- Interface responsiva e moderna
- Dashboard com visão geral dos gastos

## Requisitos

- Python 3.8+
- pip (gerenciador de pacotes Python)

## Instalação

1. Clone o repositório:
```bash
git clone <seu-repositorio>
cd gerenciador-assinaturas
```

2. Crie e ative um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
- Copie o arquivo `.env.example` para `.env`
- Edite o arquivo `.env` com suas configurações

5. Inicialize o banco de dados:
```bash
python
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
```

6. Crie um usuário inicial:
```python
>>> from app import User, db
>>> with app.app_context():
...     user = User(username="seu_usuario", password="sua_senha")
...     db.session.add(user)
...     db.session.commit()
```

## Executando o Projeto

1. Ative o ambiente virtual (se não estiver ativo):
```bash
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. Execute o servidor Flask:
```bash
python app.py
```

3. Acesse o aplicativo em `http://localhost:5000`

## Estrutura do Projeto

```
/my-subscriptions/
├── app.py                 # Aplicação Flask
├── requirements.txt       # Dependências
├── .env                  # Configurações
├── /templates            # Templates HTML
│   ├── login.html
│   ├── dashboard.html
│   └── add_subscription.html
├── /static               # Arquivos estáticos
│   └── styles.css
└── /utils               # Utilitários
```

## Próximos Passos

- [ ] Implementar upload de documentos via LLM
- [ ] Adicionar alertas de renovação
- [ ] Criar dashboard com gráficos
- [ ] Implementar backup automático
- [ ] Adicionar suporte a dark mode

## Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Crie um Pull Request

## Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes. 