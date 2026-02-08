-- Migração: Adicionar campos de armazenamento inteligente
-- Data: 2026-02-08
-- Descrição: Adiciona campos para suportar política de retenção em tiers e metadados de conexão

-- Criar tipos enum se não existirem
DO $$ BEGIN
    CREATE TYPE storage_tier AS ENUM ('hot', 'warm', 'cold');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'play_start';
    ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'play_complete';
    ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'upload';
    ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'auth_failed';
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Adicionar novos campos à tabela replays
ALTER TABLE replays ADD COLUMN IF NOT EXISTS protocol VARCHAR(20);
ALTER TABLE replays ADD COLUMN IF NOT EXISTS hostname VARCHAR(255);
ALTER TABLE replays ADD COLUMN IF NOT EXISTS connection_name VARCHAR(255);
ALTER TABLE replays ADD COLUMN IF NOT EXISTS storage_tier storage_tier DEFAULT 'hot';
ALTER TABLE replays ADD COLUMN IF NOT EXISTS checksum_sha256 VARCHAR(64);
ALTER TABLE replays ADD COLUMN IF NOT EXISTS is_compressed BOOLEAN DEFAULT FALSE;
ALTER TABLE replays ADD COLUMN IF NOT EXISTS original_size BIGINT;

-- Criar índices para otimizar buscas
CREATE INDEX IF NOT EXISTS idx_replays_storage_tier ON replays(storage_tier);
CREATE INDEX IF NOT EXISTS idx_replays_protocol ON replays(protocol);
CREATE INDEX IF NOT EXISTS idx_replays_hostname ON replays(hostname);

-- Comentários nas colunas
COMMENT ON COLUMN replays.protocol IS 'Protocolo da conexão: RDP, SSH, VNC, TELNET';
COMMENT ON COLUMN replays.hostname IS 'Nome do host de destino da conexão';
COMMENT ON COLUMN replays.connection_name IS 'Nome da conexão configurada no Guacamole';
COMMENT ON COLUMN replays.storage_tier IS 'Tier de armazenamento: hot (0-4m), warm (4m-2a), cold (>2a)';
COMMENT ON COLUMN replays.checksum_sha256 IS 'Hash SHA-256 para verificação de integridade';
COMMENT ON COLUMN replays.is_compressed IS 'Se o arquivo está comprimido com gzip';
COMMENT ON COLUMN replays.original_size IS 'Tamanho original antes da compressão em bytes';
