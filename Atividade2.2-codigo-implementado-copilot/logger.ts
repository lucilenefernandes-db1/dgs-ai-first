import pino from 'pino';

const logger = pino({
  level: 'info',
  base: { service: 'novatech-assistant' },
});

export default logger;

export function createRequestLogger(requestId: string) {
  return logger.child({ requestId });
}
