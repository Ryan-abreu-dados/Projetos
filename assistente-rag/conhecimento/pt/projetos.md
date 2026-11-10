---
fonte: site
titulo: Projetos do Ryan
rotulo_fonte: Projetos
url: /projetos/
atualizado: 2026-11-10
---

## Quais projetos o Ryan já fez?
O projeto público do Ryan é a replicação incremental com CDC no PostgreSQL, que está no GitHub. Ele
também criou o organizador de arquivos em Python na Tel Contact Center, o próprio site de portfólio e
este assistente de IA (RAG), que ainda está em construção. No trabalho, sem números internos, ele fez a
replicação CDC entre os bancos da empresa, lidera o sistema de cobranças (em andamento) e montou uma
visão de contatos desqualificados para o time comercial.

## Replicação incremental com CDC no PostgreSQL (projeto público)
O Ryan ligou a replicação lógica nativa do PostgreSQL entre o banco de uma loja virtual e um banco
analítico, com dados sintéticos gerados com Faker: 370.708 linhas na carga inicial, em 4 tabelas, e cerca
de 85 operações por segundo na simulação. Cada INSERT, UPDATE e DELETE confirmado na origem sai do log de
transações (WAL) e é aplicado no destino. O projeto é sobre o que acontece quando algo sai do lugar.

## Resultados medidos no projeto de CDC
Com o destino desligado por 30 segundos, o WAL retido na origem subiu de 1,77 para 3,39 MB; religado, o
destino alcançou a origem em 0,72 segundo. Uma conexão de replicação derrubada voltou sozinha em 2,47
segundos. O atraso medido da origem ao destino teve mediana de 0,3 ms e p99 de 3,3 ms, com os dois bancos
na mesma máquina.

## Reconciliação por md5 no projeto de CDC
A replicação lógica não acusa uma linha alterada direto no destino: continua sem erro e o dado fica
errado. Por isso o Ryan criou uma reconciliação que compara os dois lados por faixas de 10 mil ids, com
contagem e md5, e só desce linha a linha nas faixas diferentes. No teste, ele alterou 3 linhas no
destino; a replicação não acusou nada, e a reconciliação achou as 3 e copiou de volta o valor da origem.
O projeto tem 11 testes cobrindo as falhas e roda com Docker e GitHub Actions.

## O que o Ryan aprendeu com o projeto de CDC
WAL retido é o custo de um destino parado e, sem limite, enche o disco da origem. No destino, chave
estrangeira não protege nada que venha da replicação. E replicação "verde" não quer dizer dado certo:
conferir o conteúdo é outro trabalho.
