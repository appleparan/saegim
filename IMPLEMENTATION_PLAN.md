## Stage 1: README English Defaults
**Goal**: Make the default repository README files English while preserving Korean variants where useful.
**Success Criteria**: Root, demo, e2e, and frontend README entry points no longer present Korean as the default reader experience.
**Tests**: Markdown link sanity check and Korean-text scan for the updated README entry points.
**Status**: Complete

## Stage 2: Frontend UI English Copy
**Goal**: Translate user-facing Korean strings in the Svelte frontend to English.
**Success Criteria**: `saegim-frontend/src` has no Korean UI copy except intentional sample/document text values.
**Tests**: Korean-text scan across frontend source, plus frontend type check and unit tests.
**Status**: Not Started

## Stage 3: Documentation Navigation I18n
**Goal**: Improve MkDocs navigation coverage and English nav labels for translated documentation.
**Success Criteria**: Existing translated documentation pages are reachable from navigation with English labels in the English build.
**Tests**: MkDocs strict build.
**Status**: Not Started
