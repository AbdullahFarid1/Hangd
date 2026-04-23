-- ============================================================
-- Allow multiple analyses per side for the same user.
-- ============================================================
-- The original schema had a unique index on
--   (user_id, color_file, sha256)
-- that rejected re-uploads of the same PGN. The product now supports
-- running multiple independent analyses on the same file, so we drop it.
-- Each upload still has a unique storage_path (the frontend prefixes with
-- Date.now()), and each analysis_jobs row is independent.
-- ============================================================

drop index if exists public.uploads_user_sha_idx;
