---
fonte: site
titulo: Estágio na Almeida e Matos
rotulo_fonte: Experiência · Almeida e Matos
url: /experiencia/
atualizado: 2026-11-10
---

## Onde o Ryan trabalha hoje?
Desde maio de 2026, o Ryan é estagiário com foco em dados na Almeida e Matos Sociedade de Advogados, em
Alphaville (Barueri/SP). Ele trabalha com engenharia de dados em produção, com PostgreSQL e Supabase.

## Replicação incremental (CDC)
O Ryan desenvolveu a primeira versão da replicação incremental entre o banco transacional e o banco
analítico da empresa, usando a replicação lógica do PostgreSQL (CDC), e depois a estendeu para novas
tabelas, com recuperação de falhas e reconciliação de divergências.

## Cargas incrementais e consultas mais rápidas
O Ryan trocou um refresh completo, que estourava o tempo limite, por cargas incrementais idempotentes
(watermark, upsert e deduplicação), e fez um SCD tipo 2 incremental no passo mais pesado do orquestrador.
Ele também otimiza consultas e painéis com EXPLAIN ANALYZE, índices covering e manutenção de autovacuum.

## Qualidade, monitoramento e segurança dos dados
O Ryan criou checagens automáticas de qualidade que reprovam de verdade e alertam por e-mail (com n8n), e
detecção automática de mudança de estrutura (schema drift), com testes. Na segurança, implementou
controle de acesso por setor no banco (RLS) e autorização, pensando na LGPD.

## Integrações e telas
O Ryan fez a sincronização semanal de milhares de arquivos e conversas para o Google Drive (com
paginação, nova tentativa e deduplicação), a identificação de clientes pela API do WhatsApp (Meta) e um
executor de fluxos no n8n. Também desenvolve telas em React e TypeScript, ligadas a funções em PL/pgSQL e
Edge Functions do Supabase.

## Qual foi o maior desafio que o Ryan já resolveu no trabalho?
O desafio que o Ryan já resolveu foi colocar de pé a replicação incremental (CDC) entre o banco
principal e o banco analítico (em camadas, no modelo medalhão), com um orquestrador que mantém os dois
sempre sincronizados. No começo, ele tentou fazer sem pesquisar a documentação direito, e a primeira
abordagem gerava muitos erros. Com a orientação do chefe, refez a solução do jeito certo e, junto com ele,
implementou o CDC com o orquestrador sempre conectado. Também criaram uma tela de monitoramento e alertas
pelo WhatsApp, feitos com n8n, para avisar se a replicação parar. O que ele aprendeu: ler a documentação
e pesquisar antes de construir.

## O Ryan já liderou algum projeto ou pessoa?
Sim, um projeto: o Ryan está liderando um sistema de cobranças, ainda em andamento. É a primeira vez que
ele lidera um projeto; ele diz que está aprendendo bastante e quer fazer melhor nos próximos. Ele ainda
não liderou pessoas.

## Sistema de cobranças (em andamento)
O desafio atual do Ryan é um sistema de cobranças integrado por API ao sistema financeiro da empresa. A
parte difícil é a regra de negócio: fazer algo que funcione de verdade para o time financeiro. O sistema
envia lembretes automáticos no dia de cada parcela, recebe o comprovante enviado pelo cliente e o coloca
numa tela para o financeiro conferir e dar baixa. Ele se encaixa num fluxo de tarefas que já existia na
empresa.

## O Ryan já trabalhou com pessoas de outras áreas?
Sim, e é uma parte do trabalho de que ele gosta. Para o Ryan, quem conhece o fluxo de trabalho são as
pessoas de cada área: o time de vendas sabe como vender e sabe o que precisa para trabalhar melhor (uma
mensagem automática, uma automação, um campo novo). O papel dele é entender exatamente o que elas
procuram e entregar isso com os dados e as ferramentas que tem. Por exemplo, a gestora do time comercial
queria acompanhar os contatos desqualificados e explicou por quê; o Ryan montou para ela uma visão desses
dados com filtros por período (ontem, hoje, mês), por safra e por quem desqualificou mais.
