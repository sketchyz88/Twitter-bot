create table if not exists swings (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  club text not null,
  source_uri text not null,
  traced_uri text,
  shot_shape text,
  apex_height_meters numeric,
  estimated_carry_yards numeric,
  launch_direction_degrees numeric,
  favorite boolean default false,
  created_at timestamptz default now()
);

create index if not exists swings_user_id_idx on swings(user_id);
create index if not exists swings_club_idx on swings(club);
