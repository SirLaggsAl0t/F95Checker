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
  favourite: boolean
  labels: number[]
  tab: number | null
  image_version: string
  tags: EnumItem[]
  unknown_tags: string[]
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

export type Preview = {
  index: number
  url: string
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
  timeline_events: TimelineEvent[]
  last_check_version: string
}

export type Tab = {
  id: number
  name: string
  icon: string
  color: string | null
}

export type Label = {
  id: number
  name: string
  color: string
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
  style_bg: string
  style_text: string
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
  in_list: boolean
}

export type AccountStatus = {
  logged_in: boolean
}

export type BrowserLoginStatus = {
  state: 'idle' | 'running' | 'done' | 'error'
  error: string | null
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
