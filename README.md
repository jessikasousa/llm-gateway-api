# LLM Gateway API

API Gateway de LLMs desenvolvida com FastAPI para centralizar chamadas de IA, persistir interacoes e expor observabilidade com Prometheus + Grafana.

## Visao Geral

O servico oferece um endpoint unico de chat e abstrai provedores de LLM com roteamento inteligente:

- Rota primaria: OpenRouter
- Rota de grounding (web search): Gemini
- Fallback: Gemini quando a rota primaria falha
- Persistencia: PostgreSQL (prompt + resposta)
- Observabilidade: endpoint /metrics, Prometheus e Grafana

## Frontend

Cliente web em **Angular 18** para interacao com a API. Interface intuitiva para enviar prompts e visualizar respostas.

- Repositorio: https://github.com/jessikasousa/llm-gateway-frontend
- Local (desenvolvimento): http://localhost:4200
- Detalhes de instalacao e execucao: ver README do repo frontend

## Aderencia ao Desafio

Status de aderencia com base no que esta implementado no repositorio:

- API REST de chat: atendido (`POST /v1/chat`)
- Integracao com provedores LLM: atendido (OpenRouter e Gemini)
- Persistencia de interacoes: atendido (SQLAlchemy + Alembic + PostgreSQL)
- Resiliencia com retries/fallback: atendido (tenacity + fallback de provedor)
- Observabilidade com Prometheus/Grafana: atendido
- Docker Compose para subir stack local: atendido
- Frontend dedicado: atendido como extra no repo separado
- Circuit breaker completo: parcial (existe esqueleto em `app/core/circuit_breaker.py`, ainda nao integrado no fluxo)

## Repositorios

- Backend: https://github.com/jessikasousa/llm-gateway-api
- Frontend: https://github.com/jessikasousa/llm-gateway-frontend

## Arquitetura

Documentacao detalhada em [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Parte 2 - Desenho de Arquitetura

Os requisitos da Parte 2 estao documentados em [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md):

1. Proposta de escalonamento para oscilacao de carga:
   [secao 7 - Desenho cloud native AWS (proposta)](docs/ARCHITECTURE.md#desenho-cloud-native-aws-proposta)
2. Proposta de observabilidade:
   [secao 4 - Observabilidade](docs/ARCHITECTURE.md#4-observabilidade)
3. Justificativa da escolha do banco de dados:
   [secao 7 - Deploy local e cloud](docs/ARCHITECTURE.md#7-deploy-local-e-cloud)
4. Estrategia para falha de dependencias sem impactar o cliente:
   [secao 5 - Resiliencia e limites atuais](docs/ARCHITECTURE.md#5-resiliencia-e-limites-atuais)

## Execucao Local (Docker Compose)

### Pre-requisitos

- Docker Desktop (com Docker Compose)
- Git

### Passos

1. Clonar repo:

```bash
git clone https://github.com/jessikasousa/llm-gateway-api.git
cd llm-gateway-api
```

2. Criar `.env` baseado no `.env.example`.

3. Subir servicos:

```bash
docker compose up -d --build
```

4. Endpoints locais:

- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health
- Metrics: http://localhost:8000/metrics
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

Credenciais padrao do Grafana (via `.env.example`): `admin / admin123`.

## Teste Manual Rapido (curl e Postman)

### Via curl

1. Health check:

```bash
curl -X GET http://localhost:8000/health
```

2. Metrics (confirma exportacao para Prometheus):

```bash
curl -X GET http://localhost:8000/metrics
```

3. Chat (fluxo padrao):

```bash
curl -X POST http://localhost:8000/v1/chat \
   -H "Content-Type: application/json" \
   -d '{
      "userId": "u1",
      "prompt": "Explique rapidamente o que e IA generativa."
   }'
```

Response esperado (exemplo):

```json
{
  "id": "7859728e-e3d3-49ca-a71f-b73265fc0a03",
  "userId": "u1",
  "prompt": "Explique rapidamente o que e IA generativa.",
  "response": "...texto gerado pelo modelo...",
  "model": "google/gemma-3-4b-it:free",
  "timestamp": "2026-04-02T21:09:53.122069Z"
}
```

Obs.: os campos `id`, `response`, `model` e `timestamp` variam a cada chamada.

4. Chat com chance maior de grounding (termos de busca web):

```bash
curl -X POST http://localhost:8000/v1/chat \
   -H "Content-Type: application/json" \
   -d '{
      "userId": "u1",
      "prompt": "Quais as noticias recentes sobre IA no Brasil hoje?"
   }'
```

Response esperado (exemplo com grounding):

```json
{
  "id": "3b8d9cb0-0c6f-4e8f-8ca8-5b10f4fda4a2",
  "userId": "u1",
  "prompt": "Quais as noticias recentes sobre IA no Brasil hoje?",
  "response": "Aqui estao os principais destaques recentes sobre IA no Brasil...",
  "model": "google/gemini-1.5-flash",
  "timestamp": "2026-04-02T21:25:10.102345Z"
}
```

Obs.: o contrato de resposta e o mesmo do fluxo padrao; no grounding, normalmente o conteudo vem mais orientado a informacoes recentes e o `model` tende a indicar a rota Gemini.

### Via Postman

1. Crie uma request `POST` para `http://localhost:8000/v1/chat`.
2. Em `Headers`, adicione `Content-Type: application/json`.
3. Em `Body -> raw -> JSON`, envie payload com `userId` e `prompt` (conforme exemplos de curl).
4. Execute `GET http://localhost:8000/health` para validar disponibilidade da API.
5. Opcional: importe a especificacao OpenAPI por `http://localhost:8000/openapi.json` para gerar a colecao automaticamente.

## Evidencias de Observabilidade (Grafana/Prometheus)

Para demonstrar o desafio de observabilidade de forma objetiva:

1. Gerar trafego no endpoint de chat.
2. Validar metricas no Prometheus (`llm_calls_total`, `http_requests_total`, `llm_grounding_total`).
3. Mostrar dashboard no Grafana com paines:
   - HTTP Requests Total
   - HTTP Latency (avg)
   - HTTP Errors Total
   - LLM Calls by Provider/Model/Outcome
   - LLM Fallback Total
   - LLM Grounding Total
4. Exportar dashboard JSON no Grafana (`Share -> Export -> Save to file`).
5. Anexar prints no PR/entrega final.

Screenshots adicionados neste repositorio:

- Dashboard completo no Grafana: [docs/screenshots/grafana_dashboard.png](docs/screenshots/grafana_dashboard.png)
- Serie `llm_calls_total` no Prometheus: [docs/screenshots/llm_calls_total-prometheus.png](docs/screenshots/llm_calls_total-prometheus.png)
- Target `fastapi-app` em estado UP: [docs/screenshots/target_up-prometheus.png](docs/screenshots/target_up-prometheus.png)

## Importacao no Grafana

Dashboard JSON versionado neste repositorio:

- [docs/grafana-dashboard-llm-gateway-observability.json](docs/grafana-dashboard-llm-gateway-observability.json)

Para avaliacao rapida, use um dos dois caminhos:

1. Importar JSON manualmente
   - No Grafana: `Dashboards -> New -> Import`
   - Selecione o arquivo [docs/grafana-dashboard-llm-gateway-observability.json](docs/grafana-dashboard-llm-gateway-observability.json).
2. Recriar em 2 minutos com as queries abaixo
   - Crie um dashboard novo e adicione os paines com as consultas de Prometheus desta secao.

Datasource recomendado no Grafana:

- URL: `http://prometheus:9090` (quando rodando via Docker Compose)
- Nome sugerido: `prometheus`

Queries simples (sem regex) usadas no dashboard:

```promql
sum(http_requests_total)
sum(http_errors_total)
sum(http_request_duration_seconds_sum) / sum(http_request_duration_seconds_count)
sum(llm_calls_total) by (provider, model, outcome)
sum(llm_fallback_total)
sum(llm_grounding_total) by (reason)
```

## Banco de Dados e Migracoes

Com o container da API em execucao:

```bash
docker compose exec api alembic upgrade head
```

## Testes e Qualidade

```bash
docker compose exec api pytest tests/ -v
docker compose exec api ruff check .
```

## Stack Tecnica

- FastAPI
- SQLAlchemy 2.0
- Alembic
- PostgreSQL 16
- Redis 7
- OpenRouter + Gemini
- Prometheus + Grafana
- Docker Compose
- Pytest + Ruff

## Licenca

MIT

## Autoria

Jessika Sousa
