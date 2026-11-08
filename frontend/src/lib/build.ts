/**
 * Captured once when the static site is built. Every page shares the same value
 * so the footer timestamp stays consistent across the output.
 */
export const BUILD_TIMESTAMP = new Date().toISOString();
