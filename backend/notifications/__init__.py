"""Envio de e-mails do sistema (RF04 e Sprint 3).

Os serviços nunca falam com o SMTP direto: eles chamam um "notifier" deste pacote,
que monta a mensagem com um template e entrega por um "sender".
"""
