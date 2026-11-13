-- Sprint 2: agendamentos (ver docs/mer.md).
-- O agendamento guarda início e fim: o fim é o início + a duração do serviço no momento da marcação.
-- Cancelar não apaga a linha: o status vira 'cancelado' e o horário volta a ficar livre.

CREATE TABLE agendamentos (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id      INT           NOT NULL,
    profissional_id INT           NOT NULL,
    servico_id      INT           NOT NULL,
    inicio          DATETIME      NOT NULL,
    fim             DATETIME      NOT NULL,
    valor           DECIMAL(10,2) NOT NULL,   -- preço do serviço no dia, para a receita do BI não mudar
    status          ENUM('agendado', 'concluido', 'cancelado') NOT NULL DEFAULT 'agendado',
    cancelado_em    DATETIME      NULL,
    cancelado_por   INT           NULL,       -- usuário (cliente ou equipe) que cancelou
    criado_em       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_agendamento_cliente FOREIGN KEY (cliente_id) REFERENCES usuarios (id),
    CONSTRAINT fk_agendamento_profissional FOREIGN KEY (profissional_id) REFERENCES profissionais (id),
    CONSTRAINT fk_agendamento_servico FOREIGN KEY (servico_id) REFERENCES servicos (id),
    CONSTRAINT fk_agendamento_cancelado_por FOREIGN KEY (cancelado_por) REFERENCES usuarios (id),
    CONSTRAINT ck_agendamento_intervalo CHECK (fim > inicio),
    CONSTRAINT ck_agendamento_valor CHECK (valor >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Agenda de um profissional num dia (disponibilidade e checagem de conflito)
CREATE INDEX ix_agendamentos_profissional_inicio ON agendamentos (profissional_id, inicio);

-- "Meus agendamentos" do cliente
CREATE INDEX ix_agendamentos_cliente_inicio ON agendamentos (cliente_id, inicio);
