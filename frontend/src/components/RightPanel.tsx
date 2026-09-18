import type {
  EnvironmentalProfile,
  Recommendation,
  Evidence,
} from '../types';

import {
  Sprout,
  Cloud,
  FileText,
  ChevronRight,
} from 'lucide-react';

const isProvided = (value?: string | number | null) =>
  value !== undefined &&
  value !== null &&
  String(value).trim() !== '';

function StatusBox({ provided }: { provided: boolean }) {
  return (
    <span
      className={`inline-flex shrink-0 items-center justify-center rounded-lg px-2.5 py-1.5 text-[10px] font-semibold ${
        provided
          ? 'bg-canopy-sage/60 text-canopy-green'
          : 'bg-gray-100 text-gray-400'
      }`}
    >
      {provided ? 'Provided' : 'Not provided'}
    </span>
  );
}

function MetricRow({
  label,
  value,
}: {
  label: string;
  value?: string | number | null;
}) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-lg border border-canopy-border bg-white px-3 py-2.5">
      <span className="min-w-0 text-sm text-canopy-muted">
        {label}
      </span>

      <StatusBox provided={isProvided(value)} />
    </div>
  );
}

function EvidenceCard({ evidence }: { evidence: Evidence }) {
  return (
    <div className="group rounded-xl border border-canopy-border bg-white p-3.5 transition-colors hover:border-canopy-teal">
      <div className="flex items-start gap-2.5">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-canopy-sage/50">
          <FileText className="h-4 w-4 text-canopy-green" />
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2">
            <div className="truncate text-xs font-semibold text-canopy-primary">
              Document {evidence.document_id}
            </div>

            <ChevronRight className="h-3.5 w-3.5 shrink-0 text-gray-300 transition-colors group-hover:text-canopy-teal" />
          </div>

          <div className="mt-1 text-[10px] font-medium uppercase tracking-wide text-canopy-green">
            Chunk {evidence.id}
          </div>

          <p className="mt-2 line-clamp-4 text-xs leading-relaxed text-canopy-muted">
            {evidence.text}
          </p>

          <div className="mt-2 text-[10px] text-gray-400">
            Similarity {evidence.similarity.toFixed(2)}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function RightPanel({
  profile,
  recommendation: _recommendation,
  evidence,
  isLoading,
}: {
  profile: EnvironmentalProfile;
  recommendation: Recommendation | null;
  evidence: Evidence[];
  isLoading: boolean;
}) {
  return (
    <div className="hidden h-screen w-96 overflow-y-auto border-l border-canopy-border bg-white p-5 lg:block">
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h2 className="text-sm font-bold tracking-wide text-canopy-primary">
            YOUR ENVIRONMENT
          </h2>

          <p className="mt-1 text-xs text-canopy-muted">
            Live assessment profile
          </p>
        </div>

        {isLoading && (
          <span className="flex items-center gap-1 text-xs text-canopy-green animate-pulse">
            Updating...
          </span>
        )}
      </div>

      <div className="space-y-4">
        <section className="rounded-xl border border-canopy-border bg-gray-50 p-3">
          <div className="mb-3 flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-canopy-sage/50">
              <Sprout className="h-5 w-5 text-canopy-green" />
            </div>

            <h3 className="text-sm font-semibold text-canopy-primary">
              SOIL
            </h3>
          </div>

          <div className="space-y-2">
            <MetricRow
              label="pH"
              value={profile.soil?.ph}
            />

            <MetricRow
              label="Organic Carbon"
              value={profile.soil?.organic_carbon}
            />

            <MetricRow
              label="Moisture"
              value={profile.soil?.moisture}
            />
          </div>
        </section>

        <section className="rounded-xl border border-canopy-border bg-gray-50 p-3">
          <div className="mb-3 flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-50">
              <Cloud className="h-5 w-5 text-blue-500" />
            </div>

            <h3 className="text-sm font-semibold text-canopy-primary">
              CLIMATE
            </h3>
          </div>

          <div className="space-y-2">
            <MetricRow
              label="Rainfall"
              value={profile.climate?.rainfall}
            />

            <MetricRow
              label="Temperature"
              value={profile.climate?.temperature}
            />
          </div>
        </section>

        {evidence.length > 0 && (
          <section className="pt-2">
            <div className="mb-3 flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold tracking-wide text-canopy-primary">
                  EVIDENCE
                </h3>

                <p className="mt-1 text-xs text-canopy-muted">
                  Retrieved scientific sources
                </p>
              </div>

              <span className="rounded-full bg-canopy-sage/60 px-2.5 py-1 text-[10px] font-semibold text-canopy-green">
                {evidence.length}
              </span>
            </div>

            <div className="space-y-3">
              {evidence.map((ev) => (
                <EvidenceCard
                  key={`${ev.document_id}-${ev.id}`}
                  evidence={ev}
                />
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}