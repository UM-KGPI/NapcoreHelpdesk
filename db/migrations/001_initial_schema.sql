CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TYPE faq_status AS ENUM (
    'draft',
    'review',
    'approved',
    'published',
    'archived'
);

CREATE TYPE review_decision AS ENUM (
    'approve',
    'reject',
    'request_changes'
);

CREATE TYPE answer_mode AS ENUM (
    'faq',
    'rag',
    'abstain'
);

CREATE TYPE feedback_value AS ENUM (
    'helpful',
    'not_helpful',
    'needs_escalation'
);

CREATE TABLE approved_repositories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_url TEXT NOT NULL UNIQUE,
    repository_owner TEXT NOT NULL,
    repository_name TEXT NOT NULL,
    default_ref TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE source_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID NOT NULL REFERENCES approved_repositories(id),
    git_ref TEXT NOT NULL,
    commit_sha TEXT NOT NULL,
    source_path TEXT NOT NULL,
    document_type TEXT NOT NULL,
    standard_tag TEXT,
    version_tag TEXT,
    content_hash TEXT NOT NULL,
    indexed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (repository_id, commit_sha, source_path)
);

CREATE TABLE source_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES source_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    section_heading TEXT,
    chunk_text TEXT NOT NULL,
    citation_label TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (document_id, chunk_index)
);

CREATE TABLE faq_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    canonical_question TEXT NOT NULL,
    normalized_intent TEXT NOT NULL,
    standard_tag TEXT,
    status faq_status NOT NULL DEFAULT 'draft',
    current_version_id UUID,
    first_published_at TIMESTAMPTZ,
    last_reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (normalized_intent)
);

CREATE TABLE faq_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    faq_entry_id UUID NOT NULL REFERENCES faq_entries(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    answer_markdown TEXT NOT NULL,
    answer_mode answer_mode NOT NULL,
    confidence_score NUMERIC(5,4),
    has_complete_citations BOOLEAN NOT NULL DEFAULT FALSE,
    has_unsupported_claims BOOLEAN NOT NULL DEFAULT FALSE,
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (faq_entry_id, version_number)
);

ALTER TABLE faq_entries
    ADD CONSTRAINT fk_faq_entries_current_version
    FOREIGN KEY (current_version_id) REFERENCES faq_versions(id);

CREATE TABLE review_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    faq_version_id UUID NOT NULL REFERENCES faq_versions(id) ON DELETE CASCADE,
    reviewer_id TEXT NOT NULL,
    decision review_decision NOT NULL,
    review_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE question_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT,
    user_id TEXT,
    raw_question TEXT NOT NULL,
    normalized_intent TEXT,
    matched_faq_entry_id UUID REFERENCES faq_entries(id),
    answer_mode answer_mode NOT NULL,
    confidence_score NUMERIC(5,4),
    feedback feedback_value,
    abstention_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE retrieval_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_event_id UUID NOT NULL REFERENCES question_events(id) ON DELETE CASCADE,
    repository_id UUID REFERENCES approved_repositories(id),
    retrieval_query TEXT NOT NULL,
    top_k INTEGER NOT NULL,
    retrieval_score NUMERIC(8,6),
    evidence_sufficient BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE answer_evidence_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    faq_version_id UUID REFERENCES faq_versions(id) ON DELETE CASCADE,
    question_event_id UUID REFERENCES question_events(id) ON DELETE CASCADE,
    source_chunk_id UUID NOT NULL REFERENCES source_chunks(id) ON DELETE CASCADE,
    claim_label TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (
        faq_version_id IS NOT NULL OR question_event_id IS NOT NULL
    )
);

CREATE INDEX idx_source_documents_repository_id
    ON source_documents(repository_id);

CREATE INDEX idx_source_chunks_document_id
    ON source_chunks(document_id);

CREATE INDEX idx_faq_entries_status
    ON faq_entries(status);

CREATE INDEX idx_faq_entries_normalized_intent
    ON faq_entries(normalized_intent);

CREATE INDEX idx_question_events_normalized_intent
    ON question_events(normalized_intent);

CREATE INDEX idx_question_events_created_at
    ON question_events(created_at);

CREATE INDEX idx_retrieval_events_question_event_id
    ON retrieval_events(question_event_id);

CREATE INDEX idx_answer_evidence_links_faq_version_id
    ON answer_evidence_links(faq_version_id);

CREATE INDEX idx_answer_evidence_links_question_event_id
    ON answer_evidence_links(question_event_id);

COMMENT ON TABLE approved_repositories IS
    'Allowlist of GitHub repositories permitted as knowledge sources.';

COMMENT ON TABLE answer_evidence_links IS
    'Maps answers to retrieved source chunks so unsupported claims can be blocked.';