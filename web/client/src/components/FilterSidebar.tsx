import type { EnumItem, Label } from '@/api/types'
import type { Filters, Tri } from '@/lib/filters'
import { toggleValue } from '@/lib/filters'
import { cn } from '@/lib/utils'

type Props = {
  filters: Filters
  onChange: (filters: Filters) => void
  statuses: EnumItem[]
  types: EnumItem[]
  labels: Label[]
}

function Select<T extends string>({
  label,
  value,
  options,
  onChange,
}: {
  label: string
  value: T
  options: { value: T; label: string }[]
  onChange: (value: T) => void
}) {
  return (
    <label className="flex items-center justify-between gap-2 text-sm">
      <span className="text-neutral-400">{label}</span>
      <select
        aria-label={label}
        value={value}
        onChange={(event) => onChange(event.target.value as T)}
        className="min-w-0 flex-1 rounded border border-neutral-700 bg-neutral-900 px-2 py-1 text-sm"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  )
}

function Check({
  checked,
  onChange,
  children,
}: {
  checked: boolean
  onChange: () => void
  children: React.ReactNode
}) {
  return (
    <label className="flex items-center gap-1.5 text-sm text-neutral-300">
      <input type="checkbox" checked={checked} onChange={onChange} className="accent-sky-500" />
      {children}
    </label>
  )
}

function Section({ title, children }: { title?: string; children: React.ReactNode }) {
  return (
    <section className="grid gap-1.5 border-t border-neutral-800 pt-2">
      {title && <h3 className="text-xs uppercase tracking-wide text-neutral-500">{title}</h3>}
      {children}
    </section>
  )
}

export function FilterSidebar({ filters, onChange, statuses, types, labels }: Props) {
  const set = (patch: Partial<Filters>) => onChange({ ...filters, ...patch })

  return (
    <details className="rounded border border-neutral-800 bg-neutral-900/40">
      <summary className="cursor-pointer px-3 py-2 text-sm text-neutral-300">Filters and sorting</summary>
      <div className="grid gap-2 border-t border-neutral-800 p-3">
        <label className="flex flex-col gap-1 text-sm">
          <span className="text-neutral-400">Search</span>
          <input
            value={filters.query}
            onChange={(event) => set({ query: event.target.value })}
            placeholder="Name, developer or tag"
            aria-label="Filter games"
            className="rounded border border-neutral-700 bg-neutral-900 px-2 py-1 placeholder:text-neutral-500"
          />
        </label>

        <Section>
          <Select
            label="Archived"
            value={filters.archived}
            onChange={(archived) => set({ archived })}
            options={[
              { value: 'show', label: 'Show' },
              { value: 'hide', label: 'Hide' },
              { value: 'only', label: 'Only archived' },
            ]}
          />
          <Select<Tri>
            label="Installed"
            value={filters.installed}
            onChange={(installed) => set({ installed })}
            options={[
              { value: 'any', label: 'Any' },
              { value: 'yes', label: 'Yes' },
              { value: 'no', label: 'No' },
            ]}
          />
          <Select<Tri>
            label="Finished"
            value={filters.finished}
            onChange={(finished) => set({ finished })}
            options={[
              { value: 'any', label: 'Any' },
              { value: 'yes', label: 'Yes' },
              { value: 'no', label: 'No' },
            ]}
          />
        </Section>

        <Section title="Status">
          <div className="flex max-h-40 flex-col gap-1 overflow-y-auto">
            {statuses.map((status) => (
              <Check
                key={status.value}
                checked={filters.status.includes(status.value)}
                onChange={() => set({ status: toggleValue(filters.status, status.value) })}
              >
                <span style={{ color: status.color || undefined }}>{status.name}</span>
              </Check>
            ))}
          </div>
        </Section>

        <Section title="Type">
          <div className="flex max-h-40 flex-col gap-1 overflow-y-auto">
            {types.map((type) => (
              <Check
                key={type.value}
                checked={filters.type.includes(type.value)}
                onChange={() => set({ type: toggleValue(filters.type, type.value) })}
              >
                <span style={{ color: type.color || undefined }}>{type.name}</span>
                <span className="text-xs text-neutral-500">{type.category}</span>
              </Check>
            ))}
          </div>
        </Section>

        {labels.length > 0 && (
          <Section title="Labels">
            <div className="flex flex-wrap gap-1.5">
              {labels.map((label) => (
                <button
                  key={label.id}
                  type="button"
                  onClick={() => set({ labels: toggleValue(filters.labels, label.id) })}
                  aria-pressed={filters.labels.includes(label.id)}
                  className={cn(
                    'rounded border px-2 py-0.5 text-xs',
                    filters.labels.includes(label.id)
                      ? 'border-sky-500 text-white'
                      : 'border-neutral-700 text-neutral-300',
                  )}
                  style={filters.labels.includes(label.id) ? { borderColor: label.color, color: label.color } : undefined}
                >
                  {label.name || 'Unnamed'}
                </button>
              ))}
            </div>
          </Section>
        )}
      </div>
    </details>
  )
}
