import { z } from 'zod';
import { ValidationError } from '../../shared/errors.js';
import type { QueryRequest } from '../../shared/types.js';

export const QueryRequestSchema = z.object({
  question: z
  .string({ required_error: 'question is required' })
  .trim()
  .min(1, { message: 'question must not be empty' })
  .max(2000, { message: 'question must not exceed 2000 characters' }),
  conversationHistory: z
    .array(
      z.object({
        role: z.enum(['user', 'assistant']),
        content: z.string(),
      })
    )
    .optional(),
});

export const QueryResponseSchema = z.object({
  answer: z.string(),
  sourceDocuments: z.array(
    z.object({
      documentId: z.string(),
      section: z.string(),
      version: z.string(),
    })
  ),
  lowConfidence: z.boolean(),
});

export function validateQueryRequest(body: unknown): QueryRequest {
  const result = QueryRequestSchema.safeParse(body);
  if (!result.success) {
    const first = result.error.issues.map((i) => i.message).join('; ');
    throw new ValidationError(first, result.error.issues);
  }
  return result.data;
}
