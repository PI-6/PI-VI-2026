-- Estoque (RF09, issue #68): produtos do salão, conforme a entidade PRODUTOS de docs/mer.md.
-- Estoque baixo = quantidade <= quantidade_minima (gatilho do alerta do Dashboard, RF05).
--
-- unidade: ml, g (gramas), l (litros) ou un (unidade).
-- quantidade e quantidade_minima com 3 casas decimais, porque ml, g e l podem ser fracionados
-- (ex.: 0,5 l). Para "un", a API só aceita números inteiros.
-- O RF09 não prevê exclusão de produto, então não há coluna "ativo".

CREATE TABLE produtos (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    nome              VARCHAR(120)  NOT NULL,
    descricao         VARCHAR(500)  NULL,
    quantidade        DECIMAL(10,3) NOT NULL DEFAULT 0,
    quantidade_minima DECIMAL(10,3) NOT NULL DEFAULT 0,
    preco_unitario    DECIMAL(10,2) NOT NULL,
    unidade           ENUM('ml', 'g', 'l', 'un') NOT NULL,
    criado_em         DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_produtos_nome UNIQUE (nome),
    CONSTRAINT ck_produtos_quantidade CHECK (quantidade >= 0),
    CONSTRAINT ck_produtos_quantidade_minima CHECK (quantidade_minima >= 0),
    CONSTRAINT ck_produtos_preco CHECK (preco_unitario >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
