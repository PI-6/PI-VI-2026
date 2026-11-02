-- Sprint 2/3: bloqueios de horário do profissional (issues #17, #18 e #19; ver docs/mer.md).
-- Um bloqueio tira um intervalo da agenda: ninguém agenda ali e o horário aparece como ocupado.
--
-- Dois tipos, na mesma tabela:
--   pontual: um intervalo com data e hora (consulta médica, folga, curso). Pode passar de um dia.
--            Usa inicio e fim; dia_semana, hora_inicio e hora_fim ficam nulos.
--   semanal: repete toda semana no mesmo dia e faixa de horário (almoço de toda terça).
--            Usa dia_semana, hora_inicio e hora_fim; inicio e fim ficam nulos.
-- O CHECK garante que cada linha preenche só as colunas do seu tipo.
-- Remover um bloqueio apaga a linha: ele não entra no BI, então não há histórico a preservar.

CREATE TABLE bloqueios (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    profissional_id INT          NOT NULL,
    tipo            ENUM('pontual', 'semanal') NOT NULL,
    inicio          DATETIME     NULL,
    fim             DATETIME     NULL,
    dia_semana      TINYINT      NULL,          -- 0 = segunda ... 6 = domingo, igual a horarios_trabalho
    hora_inicio     TIME         NULL,
    hora_fim        TIME         NULL,
    motivo          VARCHAR(120) NULL,
    criado_por      INT          NOT NULL,      -- usuário da equipe que bloqueou
    criado_em       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_bloqueio_profissional FOREIGN KEY (profissional_id) REFERENCES profissionais (id) ON DELETE CASCADE,
    CONSTRAINT fk_bloqueio_criado_por FOREIGN KEY (criado_por) REFERENCES usuarios (id),
    CONSTRAINT ck_bloqueio_tipo CHECK (
        (tipo = 'pontual'
            AND inicio IS NOT NULL AND fim IS NOT NULL AND fim > inicio
            AND dia_semana IS NULL AND hora_inicio IS NULL AND hora_fim IS NULL)
        OR
        (tipo = 'semanal'
            AND dia_semana BETWEEN 0 AND 6
            AND hora_inicio IS NOT NULL AND hora_fim IS NOT NULL AND hora_fim > hora_inicio
            AND inicio IS NULL AND fim IS NULL)
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Bloqueios pontuais de um profissional num período (disponibilidade, agenda do dia)
CREATE INDEX ix_bloqueios_profissional_inicio ON bloqueios (profissional_id, inicio);

-- Bloqueios semanais de um profissional num dia da semana
CREATE INDEX ix_bloqueios_profissional_dia ON bloqueios (profissional_id, dia_semana);
