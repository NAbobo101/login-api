# Login API

[![CI](https://github.com/NAbobo101/login-api/actions/workflows/ci.yml/badge.svg)](https://github.com/NAbobo101/login-api/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)

API de autenticação com **JWT** construída com **FastAPI** e **SQLModel**: cadastro de usuários,
login (OAuth2 password flow), tokens de acesso e de renovação (refresh) e rota protegida.

> **EN:** JWT authentication REST API built with FastAPI and SQLModel — user registration, OAuth2
> password login, access/refresh tokens, Argon2 password hashing, tests and CI.

## Funcionalidades

- Cadastro de usuário com validação de dados (username e tamanho mínimo de senha)
- Login via OAuth2 password flow (compatível com o botão **Authorize** do Swagger)
- Par de tokens **access** (curta duração) + **refresh** (longa duração), com tipo verificado
- Senhas armazenadas com **Argon2** (`pwdlib`)
- Mensagem genérica para credenciais inválidas e proteção contra *timing attack* na enumeração de usuários
- Configuração por variáveis de ambiente (nenhum segredo no código)
- Testes automatizados com `pytest`, lint com `ruff` e CI no GitHub Actions
- Docker e Docker Compose prontos para uso

## Stack

| Camada        | Tecnologia                          |
| ------------- | ----------------------------------- |
| Framework     | FastAPI                             |
| ORM / Banco   | SQLModel + SQLite (troca via `DATABASE_URL`) |
| Autenticação  | PyJWT (HS256), pwdlib (Argon2)      |
| Configuração  | pydantic-settings                   |
| Qualidade     | pytest, ruff, GitHub Actions        |

## Estrutura

```
app/
├── main.py            # criação da aplicação, CORS, rotas e /health
├── core/
│   ├── config.py      # configurações lidas do ambiente / .env
│   └── security.py    # hash de senha e criação/validação de JWT
├── db.py              # engine e sessão do banco
├── models.py          # tabela User
├── schemas.py         # modelos de entrada/saída da API
├── deps.py            # dependências (sessão, usuário autenticado)
└── api/routes/
    ├── auth.py        # /auth/register, /auth/login, /auth/refresh
    └── users.py       # /users/me
tests/                 # testes de integração com TestClient
```

## Como rodar

### Localmente

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

cp .env.example .env
# gere uma chave e coloque em SECRET_KEY no .env:
python -c "import secrets; print(secrets.token_hex(32))"

uvicorn app.main:app --reload
```

A documentação interativa fica em <http://localhost:8000/docs>.

### Com Docker

```bash
cp .env.example .env   # defina SECRET_KEY
docker compose up --build
```

## Endpoints

| Método | Rota             | Autenticação | Descrição                                  |
| ------ | ---------------- | ------------ | ------------------------------------------ |
| POST   | `/auth/register` | —            | Cria um usuário                            |
| POST   | `/auth/login`    | —            | Retorna `access_token` e `refresh_token`   |
| POST   | `/auth/refresh`  | —            | Troca um refresh token por um novo par     |
| GET    | `/users/me`      | Bearer       | Dados do usuário autenticado               |
| GET    | `/health`        | —            | Health check                               |

### Exemplo

```bash
# cadastro
curl -X POST localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "maria", "password": "senha-forte-123"}'

# login (form data, padrão OAuth2)
curl -X POST localhost:8000/auth/login \
  -d "username=maria&password=senha-forte-123"
# {"access_token": "eyJ...", "refresh_token": "eyJ...", "token_type": "bearer"}

# rota protegida
curl localhost:8000/users/me -H "Authorization: Bearer <access_token>"

# renovar tokens
curl -X POST localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'
```

## Configuração

| Variável                       | Padrão                      | Descrição                                  |
| ------------------------------ | --------------------------- | ------------------------------------------ |
| `SECRET_KEY`                   | — (obrigatória, ≥ 32 chars) | Chave de assinatura dos JWT                |
| `ACCESS_TOKEN_EXPIRE_MINUTES`  | `15`                        | Validade do access token                   |
| `REFRESH_TOKEN_EXPIRE_MINUTES` | `10080` (7 dias)            | Validade do refresh token                  |
| `DATABASE_URL`                 | `sqlite:///./database.db`   | URL de conexão do SQLAlchemy               |
| `CORS_ORIGINS`                 | `[]`                        | Lista JSON de origens permitidas           |

## Testes e qualidade

```bash
pytest -q
ruff check .
ruff format --check .
```

## Próximos passos

- Migrações com Alembic
- Revogação de refresh tokens (blacklist / rotação persistida)
- Rate limiting no endpoint de login

## Licença

Livre para estudar, copiar e adaptar.
