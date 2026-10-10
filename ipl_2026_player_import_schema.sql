-- Run this in Supabase SQL Editor before importing.
-- This is additive only: it does not delete or reset player records.
ALTER TABLE public.auction_player_pool
  ADD COLUMN IF NOT EXISTS photo_url TEXT,
  ADD COLUMN IF NOT EXISTS batting_style TEXT,
  ADD COLUMN IF NOT EXISTS bowling_style TEXT,
  ADD COLUMN IF NOT EXISTS matches INTEGER,
  ADD COLUMN IF NOT EXISTS runs INTEGER,
  ADD COLUMN IF NOT EXISTS batting_average NUMERIC,
  ADD COLUMN IF NOT EXISTS strike_rate NUMERIC,
  ADD COLUMN IF NOT EXISTS highest_score TEXT,
  ADD COLUMN IF NOT EXISTS fifties INTEGER,
  ADD COLUMN IF NOT EXISTS hundreds INTEGER,
  ADD COLUMN IF NOT EXISTS wickets INTEGER,
  ADD COLUMN IF NOT EXISTS bowling_economy NUMERIC,
  ADD COLUMN IF NOT EXISTS base_price_is_mock BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS previous_team TEXT,
  ADD COLUMN IF NOT EXISTS squad_status TEXT,
  ADD COLUMN IF NOT EXISTS source_type TEXT,
  ADD COLUMN IF NOT EXISTS bowling_style_group TEXT,
  ADD COLUMN IF NOT EXISTS bowling_style_note TEXT,
  ADD COLUMN IF NOT EXISTS source_season TEXT,
  ADD COLUMN IF NOT EXISTS unsold_list_source TEXT,
  ADD COLUMN IF NOT EXISTS auction_order INTEGER;

-- Optional helpful index; does not change auction logic.
CREATE INDEX IF NOT EXISTS idx_auction_player_pool_room_order
  ON public.auction_player_pool (room_code, auction_order);
