import type { ZodIssue } from 'zod';

export class AppError extends Error {
  readonly statusCode: number;

  constructor(message: string, statusCode: number) {
    super(message);
    this.name = this.constructor.name;
    this.statusCode = statusCode;
  }
}

export class ValidationError extends AppError {
  readonly details: readonly ZodIssue[];

  constructor(message: string, details: readonly ZodIssue[] = []) {
    super(message, 400);
    this.details = details;
  }
}

export class EmbeddingError extends AppError {
  constructor(message: string) {
    super(message, 502);
  }
}

export class SearchError extends AppError {
  constructor(message: string) {
    super(message, 502);
  }
}

export class CompletionError extends AppError {
  constructor(message: string) {
    super(message, 502);
  }
}
