export type EnumItem = {
  value: number
  name: string
  icon?: string
  color?: string
  text?: string
  display?: string
  template?: string
  category?: string
}

export type GameSummary = {
  id: number
  custom: boolean
  name: string
  version: string
  developer: string
  type: EnumItem
  status: EnumItem
  url: string
  added_on: number
  last_updated: number
  score: number
  votes: number
  rating: number
  finished: string
  installed: string
  updated: boolean | null
  archived: boolean
  labels: number[]
  tab: number | null
  image_url: string
  image_version: string
  tags: EnumItem[]
  unknown_tags: string[]
  unknown_tags_flag: boolean
  has_image: boolean
}

export type Review = {
  user: string
  score: number
  message: string
  likes: number
  timestamp: number
}

export type TimelineEvent = {
  game_id: number
  timestamp: number
  arguments: string[]
  type: EnumItem
}

export type Download = {
  name: string
  links: { name: string; url: string }[]
}

export type GameDetail = GameSummary & {
  description: string
  changelog: string
  notes: string
  downloads: Download[]
  reviews_total: number
  reviews: Review[]
  previews_urls: string[]
  timeline_events: TimelineEvent[]
  last_check_version: string
  last_full_check: number
}

export type Tab = {
  id: number
  name: string
  icon: string
  color: string | null
  position: number
}

export type Label = {
  id: number
  name: string
  color: string
  position: number
}

export type Settings = {
  refresh_archived_games: boolean
  refresh_completed_games: boolean
  check_notifs: boolean
  max_connections: number
  max_retries: number
  request_timeout: number
  image_timeout: number
  previews_enabled: boolean
  bg_refresh_interval: number
  confirm_on_remove: boolean
  mark_installed_after_add: boolean
  default_tab_is_new: boolean
  hidden_timeline_events: number[]
  highlight_tags: boolean
  tags_highlights: Record<string, number>
  style_accent: string
  style_alt_bg: string
  style_bg: string
  style_border: string
  style_corner_radius: number
  style_text: string
  style_text_dim: string
  proxy_type: number
  proxy_host: string
  proxy_port: number
  insecure_ssl: boolean
}

export type Enums = Record<string, EnumItem[]>

export type RefreshStatus = {
  state: 'idle' | 'running'
  progress: number
  total: number
  started: number | null
  errors: { game_id: number | null; name: string | null; msg: string }[]
  missing_threads: number[]
  last_result: { updated: number[]; finished_at: number } | null
  last_successful_refresh: number
}

export type AddGamesResponse = {
  added: GameSummary[]
  skipped: { id: number; reason: string }[]
}

export type SearchResult = {
  id: number
  title: string
  creator: string
  url: string
  in_list: boolean
}

export type AccountStatus = {
  logged_in: boolean
  has_cookies: boolean
}

export type NotifCounts = {
  alerts: number
  inbox: number
  checked_at: number
}

export type ImportResult = {
  found: number
  added: GameSummary[]
  skipped: { id: number; reason: string }[]
}
