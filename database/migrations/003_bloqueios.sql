-- Sprint 2: bloqueios de horário do profissional (issue #19).
-- Dois tipos, em duas tabelas, porque cada um tem campos diferentes:
--   bloqueios             -> pontuais: um intervalo com data e hora (consulta médica dia 15, das 14h às 16h)
--   bloqueios_recorrentes -> repetem toda semana no mesmo dia e horário (almoço de terça a sábado, 12h às 13h)
-- Um horário que cai dentro de qualquer um deles aparece como indisponível na agenda.

CREATE TABLE bloqueios (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    profissional_id INT          NOT NULL,
    inicio          DATETIME     NOT NULL,
    fim             DATETIME     NOT NULL,
    motivo          VARCHAR(150) NULL,
    criado_por      INT          NULL,       -- usuário da equipe que bloqueou
    criado_em       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_bloqueio_profissional FOREIGN KEY (profissional_id) REFERENCES profissionais (id) ON DELETE CASCADE,
    CONSTRAINT fk_bloqueio_criado_por FOREIGN KEY (criado_por) REFERENCES usuarios (id),
    CONSTRAINT ck_bloqueio_intervalo CHECK (fim > inicio)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Agenda de um profissional num dia (mesmo padrão do índice de agendamentos)
CREATE INDEX ix_bloqueios_profissional_inicio ON bloqueios (profissional_id, inicio);

-- dia_semana segue o mesmo padrão de horarios_trabalho: 0 = segunda ... 6 = domingo,
-- que é o date.weekday() do Python e também o WEEKDAY() do MySQL.
-- Repetir em vários dias = uma linha por dia, como em horarios_trabalho.
-- valido_de / valido_ate limitam o período em que a regra vale. valido_ate NULL = sem data para acabar.
CREATE TABLE bloqueios_recorrentes (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    profissional_id INT          NOT NULL,
    dia_semana      TINYINT      NOT NULL,
    hora_inicio     TIME         NOT NULL,
    hora_fim        TIME         NOT NULL,
    valido_de       DATE         NOT NULL,
    valido_ate      DATE         NULL,
    motivo          VARCHAR(150) NULL,
    criado_por      INT          NULL,
    criado_em       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_bloqueio_rec_profissional FOREIGN KEY (profissional_id) REFERENCES profissionais (id) ON DELETE CASCADE,
    CONSTRAINT fk_bloqueio_rec_criado_por FOREIGN KEY (criado_por) REFERENCES usuarios (id),
    CONSTRAINT ck_bloqueio_rec_dia CHECK (dia_semana BETWEEN 0 AND 6),
    CONSTRAINT ck_bloqueio_rec_horario CHECK (hora_fim > hora_inicio),
    CONSTRAINT ck_bloqueio_rec_validade CHECK (valido_ate IS NULL OR valido_ate >= valido_de)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Busca "quais regras valem para este profissional neste dia da semana"
CREATE INDEX ix_bloqueios_rec_profissional_dia ON bloqueios_recorrentes (profissional_id, dia_semana);
