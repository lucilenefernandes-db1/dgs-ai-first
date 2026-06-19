import { app, type HttpRequest, type HttpResponseInit, type InvocationContext } from '@azure/functions';
import { validateQueryRequest } from './validator.js';
import { ValidationError } from '../../shared/errors.js';
import { createRequestLogger } from '../../shared/logger.js';
import type { QueryResponse } from '../../shared/types.js';

app.http('queryEndpoint', {
  methods: ['POST'],
  authLevel: 'anonymous',
  handler: async (request: HttpRequest, _context: InvocationContext): Promise<HttpResponseInit> => {
    const requestId = crypto.randomUUID();
    const log = createRequestLogger(requestId);
    const start = Date.now();
    let questionLength = 0;
    let status = 500;

    try {
      let body: unknown;
      try {
        body = await request.json();
      } catch {
        status = 400;
        return {
          status: 400,
          jsonBody: { error: 'invalid_json', details: [] },
        };
      }

      const queryRequest = validateQueryRequest(body);
      questionLength = queryRequest.question.length;

      const response: QueryResponse = {
        answer: 'mock',
        sourceDocuments: [],
        lowConfidence: false,
      };

      status = 200;
      return { status: 200, jsonBody: response };

    } catch (error) {
      if (error instanceof ValidationError) {
        status = 400;
        return {
          status: 400,
          jsonBody: { error: error.message, details: error.details },
        };
      }
      throw error;
    } finally {
      log.info(
        { requestId, questionLength, durationMs: Date.now() - start, status },
        'query request'
      );
    }
  },
});