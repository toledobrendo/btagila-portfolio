/**
 * Media layer: upload validation, resizing and variant generation, and storage of
 * originals plus derivatives on the configured media path.
 *
 * <p>The backend serves these files itself (see ARCHITECTURE.md §6), so variant names
 * are content-hashed to allow immutable caching.
 */
package com.btagila.portfolio.media;
