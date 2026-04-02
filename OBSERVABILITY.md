# Observabilidade - Logs Estruturados, Métricas Prometheus e Grafana

## Visão Geral

Este projeto agora possui uma solução completa de observabilidade que inclui:

- **Logs Estruturados**: Usando `structlog` com formato JSON em produção
- **Métricas Prometheus**: Coleta de métricas HTTP e LLM
- **Visualização Grafana**: Dashboard para visualização de métricas

## Componentes Implementados

### 1. Módulo de Métricas (`app/metrics/metrics.py`)

Mais de sete métricas principais foram definidas:

#### Métricas HTTP
- `http_requests_total`: Counter de requisições HTTP com labels [`method`, `endpoint`, `status_code`]
- `http_errors_total`: Counter de erros HTTP com labels [`method`, `endpoint`, `status_code`]
- `http_request_duration_seconds`: Histogram de duração de requisições com buckets apropriados

#### Métricas LLM
- `llm_calls_total`: Counter de chamadas LLM com labels [`provider`, `model`, `outcome`]
- `llm_request_duration_seconds`: Histogram de duração de requisições LLM
- `llm_grounding_total`: Counter de uso de grounding com label [`reason`]
- `llm_fallback_total`: Counter de fallbacks com labels [`primary_provider`, `fallback_provider`]

### 2. FastAPI Configuração (`app/main.py`)

#### Middleware de Métricas HTTP
- `CustomPrometheusMiddleware`: Captura métrica HTTP em cada requisição
- Registra tempo de processamento, status code, método e endpoint
- Incrementa contadores de erro para status codes >= 400

#### Endpoint Prometheus
- `/metrics`: Endpoint que expõe todas as métricas no formato Prometheus

#### Exception Handler Global
- Captura todas as exceções não tratadas
- Registra com tipo de erro e incrementa métrica de erro HTTP

### 3. LLM Service Instrumentação (`app/services/llm_service.py`)

Três caminhos principais instrumentados:

#### Path 1: Roteamento Direto para Gemini (Web Grounding)
- Measure latência
- Incrementa `llm_calls_total` com outcome="success"
- Observa `llm_request_duration_seconds`
- Incrementa `llm_grounding_total` com reason="routing"
- Log estruturado com: `user_id`, `model`, `provider`, `latency_ms`, `tokens_used`, `grounding_used=True`, `response_id`

#### Path 2: OpenRouter com Retries
- Measure latência
- Incrementa métricas de sucesso
- Registra duração
- Log estruturado com campos contextuais

#### Path 3: Fallback para Gemini
- Incrementa `llm_fallback_total`
- Incrementa `llm_grounding_total` com reason="fallback"
- Mesmes medições de latência e métricas do Path 1
- Log com flag `fallback=True`

### 4. Docker Compose (`docker-compose.yml`)

Três novos serviços adicionados:

#### Prometheus
- Porta: 9090
- Scrape interval: 15s
- Volume: `prometheus_data` para persistência
- Configuração: `prometheus.yml`

#### Grafana
- Porta: 3000
- Credenciais padrão: admin/admin123
- Volume: `grafana_data` para persistência
- Conecta ao Prometheus como datasource

#### Configuração Prometheus (`prometheus.yml`)
- Job name: "fastapi-app"
- Target: api:8000 (nome do serviço no docker-compose)
- Scrape interval: 15s

## Como Usar

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

Novas dependências adicionadas:
- `prometheus_client==0.21.1`: Cliente Prometheus para Python
- `starlette_exporter==0.19.0`: Exporter de métricas para Starlette

### 2. Iniciar os Serviços

```bash
docker-compose up -d
```

Isso iniciará:
- **API**: http://localhost:8000
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000

### 3. Acessar Métricas

#### Endpoint de Métricas da API
```
http://localhost:8000/metrics
```
Retorna todas as métricas em formato Prometheus texto.

#### Prometheus UI
```
http://localhost:9090
```
- Status > Targets para verificar se a API está sendo scrapeada
- Graph para explorar métricas
- Exemplos de queries:
  - `http_requests_total`: Total de requisições
  - `rate(http_requests_total[5m])`: Taxa de requisições por segundo
  - `http_request_duration_seconds_bucket`: Latência das requisições
  - `llm_calls_total`: Total de chamadas LLM
  - `llm_request_duration_seconds`: Duração das chamadas LLM

#### Grafana
```
http://localhost:3000
```
- Login com admin/admin123
- Adicionar Prometheus como datasource se não estiver pré-configurado
  - URL: `http://prometheus:9090`
- Criar dashboards para visualizar:
  - Taxa de requisições HTTP
  - Latência HTTP e LLM
  - Taxa de erros
  - Taxa de uso de grounding
  - Taxa de fallback

### 4. Campos de Log Estruturado

Os logs estruturados incluem os seguintes campos contextuais:

```json
{
  "user_id": "user_123",
  "model": "gemini-2.5-flash",
  "provider": "gemini",
  "latency_ms": 1234.5,
  "tokens_used": 450,
  "grounding_used": true,
  "response_id": "resp_abc123",
  "fallback": false
}
```

## Arquitetura de Observabilidade

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Application                   │
│                   - HTTP Endpoints                        │
│                   - /metrics endpoint                     │
│                   - Custom Middleware                     │
│                   - Exception Handlers                    │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ Métricas em formato Prometheus
                   │
         ┌─────────▼─────────┐
         │    Prometheus     │ (scrape de 15s)
         │   Port: 9090      │
         │  prometheus_data  │
         └──────────┬────────┘
                    │
                    │ Leitura de series de tempo
                    │
         ┌─────────▼─────────┐
         │     Grafana       │
         │   Port: 3000      │
         │   grafana_data    │
         │  (Dashboards)     │
         └───────────────────┘
```

## Verificação e Testes

### Verificar Métricas HTTP

```bash
# Fazer uma requisição
curl -X POST http://localhost:8000/v1/chat -H "Content-Type: application/json" -d '{"user_id":"test","prompt":"Olá"}'

# Acessar métricas
curl http://localhost:8000/metrics | grep http_requests_total
```

### Verificar Prometheus Scraping

1. Acesse http://localhost:9090
2. Vá para Status > Targets
3. Verifique se o target "fastapi-app" está no estado "UP"

### Verificar Grafana

1. Acesse http://localhost:3000
2. Login com admin/admin123
3. Adicione Prometheus como datasource (se não estiver)
4. Crie panels com queries como:
   - `rate(http_requests_total[1m])`
   - `histogram_quantile(0.95, http_request_duration_seconds_bucket)`
   - `llm_calls_total`

## Referências

- [Prometheus Client Python](https://prometheus.io/docs/instrumenting/writing_clientlibs/)
- [Structlog Documentation](https://www.structlog.org/)
- [Grafana Documentation](https://grafana.com/docs/)
- [FastAPI Middleware](https://fastapi.tiangolo.com/tutorial/middleware/)
