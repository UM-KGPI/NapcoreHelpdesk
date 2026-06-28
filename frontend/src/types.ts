export type StandardsScope = "Transmodel" | "NeTEx" | "SIRI" | "OpRa" | "Profile Documentation";

export type AnswerMode = "faq" | "rag" | "abstain";

export interface Citation {
  repositoryUrl: string;
  commitSha: string;
  sourcePath: string;
  chunkId: string;
  label?: string;
}

export interface AnswerTrace {
  requestId: string;
  questionEventId: string;
  matchedFaqEntryId: string | null;
  retrievalEventIds: string[];
  evidenceLinkIds?: string[];
  provenanceIds?: string[];
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

export interface AnswerResponse {
  answerId: string;
  mode: AnswerMode;
  confidence: number;
  answer: string;
  citations: Citation[];
  abstained: boolean;
  abstentionReason: string | null;
  reviewRequired: boolean;
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
}

export interface QuestionEventDetail {
  questionEventId: string;
  requestId: string;
  question: string;
  answer: string;
  mode: AnswerMode;
  confidence: number;
  citations: QuestionEventCitation[];
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
