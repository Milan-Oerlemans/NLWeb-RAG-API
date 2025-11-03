-- Active: 1761927156767@@localhost@5434@vector_db
-- First, create the table
-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

-- 
-- NOTE: You must define this custom type first.
-- This is an EXAMPLE definition, yours might be different.
--
CREATE TYPE schema_validation_status AS ENUM (
    'pending',
    'valid',
    'invalid'
    -- Add other statuses as needed
);


CREATE TABLE public.vector_embeddings (
    embedding_id      uuid NOT NULL DEFAULT gen_random_uuid(),
    document_id       uuid NOT NULL,
    site_id           uuid NOT NULL,
    id                text NOT NULL,
    url               text NOT NULL,
    name              text NOT NULL,
    schema_json       jsonb NOT NULL,
    embedding         vector(1536) NOT NULL,
    validation_status schema_validation_status NOT NULL,
    errors            jsonb,
    PRIMARY KEY (embedding_id),
    UNIQUE (id, site_id)
);

-- Then, create the HNSW index on the new table
CREATE INDEX embedding_cosine_idx 
ON public.vector_embeddings 
USING hnsw (embedding vector_cosine_ops) 
WITH (m = 16, ef_construction = 200);

CREATE TABLE public.topicclusters (
    topic_id        uuid NOT NULL DEFAULT gen_random_uuid(),
    site_id         uuid NOT NULL,
    topic_label     text NOT NULL,
    signal_label    text,
    centroid_vector vector(1536) NOT NULL,
    PRIMARY KEY (topic_id)
);

CREATE TABLE public.topic_discovery_nodes (
    node_id           text NOT NULL,
    document_id       uuid NOT NULL,
    site_id           uuid NOT NULL,
    node_content_hash text NOT NULL,
    embedding         vector(1536) NOT NULL,
    PRIMARY KEY (node_id)
);

CREATE TABLE public.chunktopicassignments (
    assignment_id    uuid NOT NULL DEFAULT gen_random_uuid(),
    chunk_id         text NOT NULL,
    topic_id         uuid NOT NULL,
    similarity_score real NOT NULL,
    PRIMARY KEY (assignment_id),
    UNIQUE (chunk_id)
);