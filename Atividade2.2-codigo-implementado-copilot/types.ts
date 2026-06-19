export interface ConversationTurn {
  role: 'user' | 'assistant';
  content: string;
}

export interface QueryRequest {
  question: string;
  conversationHistory?: ConversationTurn[];
}

export interface SourceDocument {
  documentId: string;
  section: string;
  version: string;
}

export interface RetrievedChunk {
  content: string;
  score: number;
  metadata: SourceDocument;
}

export interface QueryResponse {
  answer: string;
  sourceDocuments: SourceDocument[];
  lowConfidence: boolean;
}
