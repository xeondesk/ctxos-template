-- CtxOS Database Initialization Script

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS ctxos_core;
CREATE SCHEMA IF NOT EXISTS ctxos_analytics;
CREATE SCHEMA IF NOT EXISTS ctxos_audit;

-- Set default permissions
ALTER DEFAULT PRIVILEGES IN SCHEMA ctxos_core GRANT ALL ON TABLES TO ctxos_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA ctxos_analytics GRANT ALL ON TABLES TO ctxos_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA ctxos_audit GRANT ALL ON TABLES TO ctxos_user;

-- Create basic tables (simplified for demo)
CREATE TABLE IF NOT EXISTS ctxos_core.entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    source VARCHAR(100),
    severity VARCHAR(20),
    confidence FLOAT,
    properties JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ctxos_core.signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id UUID REFERENCES ctxos_core.entities(id),
    signal_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20),
    confidence FLOAT,
    properties JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ctxos_core.contexts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    entities JSONB,
    signals JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_entities_name ON ctxos_core.entities USING gin(name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_entities_type ON ctxos_core.entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_entities_source ON ctxos_core.entities(source);
CREATE INDEX IF NOT EXISTS idx_entities_created_at ON ctxos_core.entities(created_at);
CREATE INDEX IF NOT EXISTS idx_signals_entity_id ON ctxos_core.signals(entity_id);
CREATE INDEX IF NOT EXISTS idx_signals_type ON ctxos_core.signals(signal_type);
CREATE INDEX IF NOT EXISTS idx_signals_created_at ON ctxos_core.signals(created_at);

-- Create audit table
CREATE TABLE IF NOT EXISTS ctxos_audit.audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name VARCHAR(100) NOT NULL,
    operation VARCHAR(10) NOT NULL, -- INSERT, UPDATE, DELETE
    record_id UUID,
    old_values JSONB,
    new_values JSONB,
    user_id VARCHAR(100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create function for audit logging
CREATE OR REPLACE FUNCTION ctxos_audit.trigger_audit()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO ctxos_audit.audit_log (table_name, operation, record_id, old_values)
        VALUES (TG_TABLE_NAME, TG_OP, OLD.id, row_to_json(OLD));
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO ctxos_audit.audit_log (table_name, operation, record_id, old_values, new_values)
        VALUES (TG_TABLE_NAME, TG_OP, NEW.id, row_to_json(OLD), row_to_json(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO ctxos_audit.audit_log (table_name, operation, record_id, new_values)
        VALUES (TG_TABLE_NAME, TG_OP, NEW.id, row_to_json(NEW));
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create audit triggers
CREATE TRIGGER audit_entities
    AFTER INSERT OR UPDATE OR DELETE ON ctxos_core.entities
    FOR EACH ROW EXECUTE FUNCTION ctxos_audit.trigger_audit();

CREATE TRIGGER audit_signals
    AFTER INSERT OR UPDATE OR DELETE ON ctxos_core.signals
    FOR EACH ROW EXECUTE FUNCTION ctxos_audit.trigger_audit();

CREATE TRIGGER audit_contexts
    AFTER INSERT OR UPDATE OR DELETE ON ctxos_core.contexts
    FOR EACH ROW EXECUTE FUNCTION ctxos_audit.trigger_audit();

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION ctxos_core.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create updated_at triggers
CREATE TRIGGER update_entities_updated_at
    BEFORE UPDATE ON ctxos_core.entities
    FOR EACH ROW EXECUTE FUNCTION ctxos_core.update_updated_at_column();

CREATE TRIGGER update_contexts_updated_at
    BEFORE UPDATE ON ctxos_core.contexts
    FOR EACH ROW EXECUTE FUNCTION ctxos_core.update_updated_at_column();

-- Insert sample data for testing
INSERT INTO ctxos_core.entities (name, entity_type, source, severity, confidence, properties) VALUES
('example.com', 'domain', 'dns_collector', 'medium', 0.85, '{"registrar": "NameCheap", "created_date": "2020-01-15"}'),
('192.168.1.100', 'ip_address', 'network_scanner', 'low', 0.90, '{"country": "US", "provider": "AWS"}'),
('admin@example.com', 'email', 'email_collector', 'high', 0.95, '{"verified": true, "domain": "example.com"}')
ON CONFLICT DO NOTHING;

-- Grant permissions to the user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA ctxos_core TO ctxos_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA ctxos_analytics TO ctxos_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA ctxos_audit TO ctxos_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA ctxos_core TO ctxos_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA ctxos_analytics TO ctxos_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA ctxos_audit TO ctxos_user;
