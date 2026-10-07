-- Sprint 1: usuários, serviços, profissionais e horário de trabalho.
-- Agendamentos, bloqueios e estoque entram nas próximas migrations (ver docs/mer.md).

CREATE TABLE usuarios (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    nome          VARCHAR(120) NOT NULL,
    cpf           CHAR(11)     NULL,          -- só dígitos; funcionário pode não ter
    telefone      VARCHAR(11)  NULL,          -- DDD + número, só dígitos
    email         VARCHAR(160) NOT NULL,
    senha_hash    VARCHAR(255) NOT NULL,
    perfil        ENUM('cliente', 'admin', 'gerente') NOT NULL DEFAULT 'cliente',
    ativo         TINYINT(1)   NOT NULL DEFAULT 1,
    criado_em     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_usuarios_email UNIQUE (email),
    CONSTRAINT uq_usuarios_cpf UNIQUE (cpf)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE servicos (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    nome            VARCHAR(100)  NOT NULL,
    descricao       VARCHAR(500)  NULL,
    duracao_minutos SMALLINT      NOT NULL,
    preco           DECIMAL(10,2) NOT NULL,
    ativo           TINYINT(1)    NOT NULL DEFAULT 1,
    criado_em       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT ck_servicos_duracao CHECK (duracao_minutos > 0),
    CONSTRAINT ck_servicos_preco CHECK (preco >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Todo profissional é um usuário da equipe (perfil admin ou gerente).
-- A tabela separada deixa os agendamentos apontando para o profissional, não para qualquer usuário.
CREATE TABLE profissionais (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT      NOT NULL,
    criado_em  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_profissionais_usuario UNIQUE (usuario_id),
    CONSTRAINT fk_profissionais_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE profissional_servicos (
    profissional_id INT NOT NULL,
    servico_id      INT NOT NULL,
    PRIMARY KEY (profissional_id, servico_id),
    CONSTRAINT fk_ps_profissional FOREIGN KEY (profissional_id) REFERENCES profissionais (id) ON DELETE CASCADE,
    CONSTRAINT fk_ps_servico FOREIGN KEY (servico_id) REFERENCES servicos (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- dia_semana segue o padrão do Python (date.weekday()): 0 = segunda ... 6 = domingo.
-- Um intervalo por dia; pausas como o almoço serão feitas com bloqueios (Sprint 3).
CREATE TABLE horarios_trabalho (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    profissional_id INT     NOT NULL,
    dia_semana      TINYINT NOT NULL,
    hora_inicio     TIME    NOT NULL,
    hora_fim        TIME    NOT NULL,
    CONSTRAINT uq_horario_dia UNIQUE (profissional_id, dia_semana),
    CONSTRAINT fk_horario_profissional FOREIGN KEY (profissional_id) REFERENCES profissionais (id) ON DELETE CASCADE,
    CONSTRAINT ck_horario_dia CHECK (dia_semana BETWEEN 0 AND 6),
    CONSTRAINT ck_horario_intervalo CHECK (hora_fim > hora_inicio)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
