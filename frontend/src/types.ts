/**
 * TypeScript type definitions for all API request and response shapes.
 *
 * Shared across the API client (api.ts) and UI components. Types mirror the
 * backend serializers so the compiler enforces contract alignment without a
 * generated client.
 *
 * Requirements & design: Andrej Tibaut, Sara Guerra de Oliveira (UM KGPI)
 * Crafted by: AI coding agents
 * Created: 2026-03-28  |  Modified: 2026-06-28
 */

export type StandardsScope = "Transmodel" | "NeTEx" | "SIRI" | "OpRa" | "Profile Documentation";

export type AnswerMode = "faq" | "rag" | "abstain";

export interface Citation {
  repositoryUrl: string;
  commitSha: string;
  sourcePath: string;
  chunkId: string;
  label?: string;
  /** Readable name of a cited part of an EU act ("MMTIS Art. 4"); absent for other sources. */
  title?: string;
}

/** A provision of an EU act that names the standard an answer is about. */
export interface LegalContextItem {
  label: string;
  url: string;
}

export interface AnswerTrace {
  requestId: string;
  questionEventId: string;
  matchedFaqEntryId: string | null;
  retrievalEventIds: string[];
  evidenceLinkIds?: string[];
  provenanceIds?: string[];
  graphExpansionHops?: number;
  graphConceptIds?: string[];
  graphEvidenceCount?: number;
  graphScoreContribution?: number;
  graphCandidatesAdded?: number;
  graphProvenanceChainCount?: number;
  exampleChunksAdded?: number;
  repositoryCoverageCount?: number;
  conceptCoverageCount?: number;
  semanticAlignmentScore?: number;
  ruleHitsCount?: number;
  ruleConclusions?: Array<Record<string, unknown>>;
  ontologyVersions?: Array<{
    ontologyKey: string;
    version: string;
    graphUri: string;
    contentHash: string;
  }>;
  semanticQuery?: {
    intent: string;
    normativity: "mandatory" | "recommended" | "optional" | "unspecified";
    coreConcept: string;
    coreConcepts: string[];
    ambiguousCoreConcept: boolean;
    candidateStandards: string[];
    originalTerms: string[];
    confidence: {
      intent: number;
      concept: number;
    };
  };
  semanticDisambiguationRequired?: boolean;
  semanticDisambiguationPrompt?: string | null;
  semanticFallback?: "NO_CONCEPT_MATCH" | "AMBIGUOUS_CORE_CONCEPT" | "PARTIAL_EVIDENCE" | null;
  semanticProvisional?: boolean;
  semanticProvisionalReason?:
    | "LOW_RETRIEVAL_CONFIDENCE"
    | "LIMITED_EVIDENCE_COVERAGE"
    | "CROSS_STANDARD_GAP"
    | null;
  evidenceCoverageLevel?: "low" | "medium" | "high";
  crossStandardConflict?: boolean;
  crossStandardConflictType?:
    | "NORMATIVE_STRENGTH_MISMATCH"
    | "EVIDENCE_COVERAGE_ASYMMETRY"
    | null;
  crossStandardEvidencePartitions?: CrossStandardEvidencePartition[];
  userLikes?: boolean;
  userDislikes?: boolean;
  answerSuccess?: boolean | null;
  citationClickCount?: number;
}

export interface CrossStandardEvidencePartition {
  standard: string;
  evidenceCount: number;
  avgScore: number;
  topSourcePaths: string[];
  normativitySignals: Array<"mandatory" | "optional">;
}

/** A NeTEx fragment generated for an "example with values" question, validated against the XSD. */
export interface GeneratedExample {
  valid: boolean;
  attempts: number;
  xml?: string;
  document?: string;
  schema?: string;
  schemaVersion?: string;
  schemaCommit?: string;
  elementNotes?: { name: string; documentation: string }[];
  valuePlaces?: { value: string; element: string; path: string[]; count?: number }[];
  /** "generated" for the model's fragment, "standard" for an excerpt of one of the standard's own example files. */
  origin?: "generated" | "standard";
  /** Whether the fragment passed the XSD on its own (an excerpt can fail on references outside it). */
  validated?: boolean;
  /** An excerpt of a larger object of the standard's example: what the question asks for, the rest marked "…". */
  excerpt?: boolean;
  sourcePath?: string;
  sourceUrl?: string;
  repositoryUrl?: string;
  /** false: a standard example shown because no generated one validated; it does not hold the question's values. */
  holdsValues?: boolean;
  /** The question's values the shown standard example does not contain. */
  missingValues?: string[];
  /** The object the question asks for (resolved from the schema) and the standard file its skeleton came from. */
  askedObject?: string;
  skeletonSourcePath?: string;
  skeletonCompanion?: string;
  evidenceChunkIds?: string[];
  errors?: string[];
  generationMs?: number;
  validationMs?: number;
  schemaDeclarations?: number;
}

/** What an element contains according to the NeTEx schema (own children first, then inherited), no model involved. */
export interface SchemaStructure {
  element: string;
  documentation?: string;
  source?: string;
  groups: { owner: string; inherited: boolean; children: { name: string; documentation: string }[] }[];
  attributes: { name: string; documentation: string; owner: string }[];
}

export interface AnswerResponse {
  answerId: string;
  mode: AnswerMode;
  confidence: number;
  answer: string;
  citations: Citation[];
  legalContext?: LegalContextItem[];
  abstained: boolean;
  abstentionReason: string | null;
  reviewRequired: boolean;
  generatedExample?: GeneratedExample | null;
  schemaStructure?: SchemaStructure | null;
  trace: AnswerTrace;
}

export interface AskedQuestionRow {
  question: string;
  askedAt: string;
  requestId: string;
  questionEventId: string;
  mode: AnswerMode;
  confidence: number;
  reviewRequired: boolean;
  userLikes: boolean;
  userDislikes: boolean;
  answerSuccess: boolean | null;
}

export interface QuestionEventsResponse {
  page: number;
  pageSize: number;
  total: number;
  items: AskedQuestionRow[];
}

export interface TrendingQuestion {
  question: string;
  answer: string;
  askedAt: string;
  requestId: string;
  questionEventId: string;
  mode: AnswerMode;
  confidence: number;
}

export interface TrendingQuestionsResponse {
  items: TrendingQuestion[];
}

export interface PromotionCandidate {
  questionEventId: string;
  normalizedIntent: string;
  questionCount: number;
  notHelpfulRate: number;
  lastAskedAt: string;
  recommendedAction: "CREATE_FAQ_DRAFT" | "REVIEW_EXISTING_FAQ" | "MONITOR";
}

export interface PromotionCandidatesResponse {
  windowDays: number;
  minCount: number;
  items: PromotionCandidate[];
}

export interface EditorialQueueResponse {
  queued: boolean;
  queueItemId: string;
  status: string;
}

export interface EditorialTransition {
  action: "request_changes" | "approve" | "reject" | "revoke" | "publish" | "reopen";
  fromStatus: string;
  toStatus: string;
  actorId: string;
  actorRoles: string[];
}

export interface EditorialQueueTransitionResponse {
  queueItemId: string;
  status: string;
  transition: EditorialTransition;
}

export interface EditorialBoardItem {
  queueItemId: string;
  status: "in_review" | "approved" | "rejected" | "revoked" | "published";
  reason: "LOW_CONFIDENCE" | "CITATION_GAP" | "POLICY_REVIEW" | "USER_ESCALATION";
  priority: "low" | "normal" | "high";
  questionEventId: string;
  requestId: string;
  question: string;
  createdAt: string;
  updatedAt: string;
  allowedActions: Array<"approve" | "reject" | "revoke" | "reopen">;
}

export interface EditorialBoardResponse {
  page: number;
  pageSize: number;
  total: number;
  actorRoles: string[];
  items: EditorialBoardItem[];
}

export interface EditorialBoardMetricsResponse {
  windowDays: number;
  slaHours: number;
  generatedAt: string;
  totalItems: number;
  unresolvedItems: number;
  overdueItems: number;
  byStatus: Record<"in_review" | "approved" | "rejected" | "revoked" | "published", number>;
  byPriority: Record<"low" | "normal" | "high", number>;
  byReason: Record<"LOW_CONFIDENCE" | "CITATION_GAP" | "POLICY_REVIEW" | "USER_ESCALATION", number>;
  agingBuckets: {
    lt24h: number;
    h24to72: number;
    gt72h: number;
  };
  feedbackToday: {
    likes: number;
    dislikes: number;
    answerSuccess: number;
    citationClicks: number;
  };
  feedbackWindow: {
    likes: number;
    dislikes: number;
    answerSuccess: number;
    citationClicks: number;
  };
}

export interface SemanticKeywordCount {
  token: string;
  count: number;
}

export interface SemanticNgramCount {
  ngram: string;
  count: number;
}

export interface SemanticKeywordAggregation {
  topKeywords: SemanticKeywordCount[];
  topBigrams: SemanticNgramCount[];
  lexicalCohesion: number;
}

export interface EditorialSemanticClusterMember {
  questionEventId: string;
  question: string;
  askedAt: string;
  requestId: string;
  mode: AnswerMode;
  reviewRequired: boolean;
  abstained: boolean;
}

export interface EditorialSemanticCluster {
  clusterId: string;
  labelHint: string;
  validationSignal: "strong" | "medium" | "weak";
  memberCount: number;
  averageSimilarity: number;
  latestAskedAt: string;
  questionEventIds: string[];
  sampleQuestions: string[];
  keywordAggregation: SemanticKeywordAggregation;
  members: EditorialSemanticClusterMember[];
}

export interface EditorialSemanticClustersResponse {
  generatedAt: string;
  windowDays: number;
  minClusterSize: number;
  similarityThreshold: number;
  maxEvents: number;
  totalEvents: number;
  clusteredEvents: number;
  singletonEvents: number;
  clusters: EditorialSemanticCluster[];
}

export interface QuestionEventCitation {
  label: string | null;
  sourcePath: string;
  repositoryUrl: string;
  chunkId: string;
  title?: string;
}

export interface QuestionEventDetail {
  questionEventId: string;
  requestId: string;
  question: string;
  answer: string;
  mode: AnswerMode;
  confidence: number;
  citations: QuestionEventCitation[];
  legalContext?: LegalContextItem[];
  generatedExample?: GeneratedExample | null;
  schemaStructure?: SchemaStructure | null;
  createdAt: string;
}

export interface IndexRepositoryResponse {
  status: "ok";
  requestId: string;
  repositoryUrl: string;
  repositoryPath: string;
  profile: string;
  incremental: boolean;
  prune: boolean;
  autoAllowedRepository: boolean;
  scannedFiles: number;
  skippedFiles: number;
  createdChunks: number;
  updatedChunks: number;
  deletedChunks: number;
}

// A source the knowledge base is harvested from (Editor > Harvest & Index).
export interface HarvestSource {
  name: string;
  repositoryUrl: string;
  profile: string;
  checkoutPresent: boolean;
  indexedChunks: number;
  indexedCommit: string | null;
  indexedAt: string | null;
  // Set when the repository publishes its own ontology, loaded into GraphDB on harvest.
  ontology: { key: string; graphUri: string; version: string | null; lastLoadedAt: string | null } | null;
}

export interface SourcesResponse {
  requestId: string;
  sources: HarvestSource[];
}

export interface HarvestSourceRow {
  status: "ok" | "failed";
  repository: string;
  error?: string;
  commit?: string;
  mode?: "full" | "incremental";
  scanned_files?: number;
  skipped_files?: number;
  created_chunks?: number;
  updated_chunks?: number;
  deleted_chunks?: number;
  ontology?: { key: string; graph: string; version: string; status: "loaded" | "unchanged" | "skipped"; reason?: string } | null;
  seconds?: number;
}

export interface HarvestJobResponse {
  requestId: string;
  jobId: string;
  state: "queued" | "running" | "finished" | "error";
  // The refresh report: status "skipped" when another harvest holds the checkout lock.
  result: { status: "ok" | "partial" | "failed" | "skipped"; reason?: string; results: Record<string, HarvestSourceRow> } | null;
  error: string | null;
}

export type EditorRole = "editor" | "reviewer" | "publisher" | "admin";

// An editor account (Editor > Users); people sign in with GitHub.
export interface EditorUser {
  id: number;
  githubLogin: string;
  name: string;
  avatarUrl: string;
  roles: EditorRole[];
  isActive: boolean;
  // False for an invitation nobody has used yet.
  signedInOnce: boolean;
  invitedBy: string;
  lastLoginAt: string | null;
  createdAt: string;
}

export interface AuthMe {
  subject: string;
  kind: "account" | "anonymous";
  roles: string[];
  account: EditorUser | null;
  githubSignIn: boolean;
}

export interface HealthResponse {
  status: "ok" | "degraded";
  service: string;
  check: "live" | "ready";
  version: string;
  buildRef: string;
  database?: string;
}

export interface ApiErrorEnvelope {
  error?: {
    code?: string;
    message?: string;
    requestId?: string;
  };
}
