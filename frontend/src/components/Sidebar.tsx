import {
  Leaf,
  MessageSquarePlus,
  Target,
  Database,
  Network,
  Sprout,
} from 'lucide-react';

export default function Sidebar({
  onNewChat,
}: {
  onNewChat: () => void;
}) {
  const steps = [
    {
      num: '01',
      title: 'Understand',
      desc: 'Your environmental context',
      icon: Target,
    },
    {
      num: '02',
      title: 'Retrieve',
      desc: 'Relevant scientific evidence',
      icon: Database,
    },
    {
      num: '03',
      title: 'Connect',
      desc: 'Environmental relationships',
      icon: Network,
    },
    {
      num: '04',
      title: 'Recommend',
      desc: 'Evidence-backed action',
      icon: Sprout,
    },
  ];

  return (
    <aside className="hidden h-screen w-64 flex-col border-r border-canopy-border bg-white p-4 md:flex">
      {/* Brand Header */}
      <div className="shrink-0">
        <div className="flex items-center gap-2 text-lg font-bold text-canopy-primary">
          <Leaf className="h-6 w-6 text-canopy-green" />
          CANOPY AI
        </div>

        <div className="mt-1 text-xs text-canopy-muted">
          Environmental Intelligence
        </div>
      </div>

      {/* Sidebar Content */}
      <div className="mt-8 flex min-h-0 flex-1 flex-col">
        {/* New Chat */}
        <button
          onClick={onNewChat}
          className="flex w-full shrink-0 items-center gap-3 rounded-lg bg-canopy-sage px-3 py-2.5 font-medium text-canopy-green shadow-sm transition-all duration-200 hover:bg-canopy-green hover:text-white hover:shadow-md"
        >
          <MessageSquarePlus className="h-4 w-4" />
          New Chat
        </button>

        {/* Workflow */}
        <div className="mt-9 min-h-0 flex-1 overflow-y-auto overflow-x-hidden pr-1">
          <div className="mb-5 text-[10px] font-bold uppercase tracking-[0.16em] text-canopy-muted">
            How Canopy Works
          </div>

          <div className="relative ml-2">
            {/* Timeline Line */}
            <div className="absolute left-[9px] top-2 bottom-3 w-px bg-canopy-sage/70" />

            <div className="space-y-4">
              {steps.map((step) => {
                const Icon = step.icon;

                return (
                  <div
                    key={step.num}
                    className="group relative flex gap-3"
                  >
                    {/* Timeline Node */}
                    <div className="relative z-10 mt-1 flex h-[18px] w-[18px] shrink-0 items-center justify-center rounded-full bg-white ring-1 ring-canopy-sage transition-all duration-200 group-hover:ring-canopy-green">
                      <div className="h-1.5 w-1.5 rounded-full bg-canopy-green/60 transition-all duration-200 group-hover:h-2 group-hover:w-2 group-hover:bg-canopy-green" />
                    </div>

                    {/* Step Content */}
                    <div className="min-w-0 flex-1 rounded-xl border border-transparent px-2.5 py-2 transition-all duration-200 group-hover:border-canopy-sage/50 group-hover:bg-canopy-sage/15">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-semibold tracking-wide text-canopy-green/55">
                          {step.num}
                        </span>

                        <div className="flex items-center gap-1.5">
                          <h4 className="text-sm font-semibold text-canopy-primary">
                            {step.title}
                          </h4>

                          <Icon className="h-3.5 w-3.5 text-canopy-green/65" />
                        </div>
                      </div>

                      <p className="mt-1 text-[11px] leading-relaxed text-canopy-muted">
                        {step.desc}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Footer Tagline */}
      <div className="relative mt-5 shrink-0 overflow-hidden rounded-xl border border-canopy-sage/30 bg-gradient-to-br from-canopy-sage/50 to-canopy-sage/15 p-4 shadow-sm">
        {/* Decorative Leaf */}
        <Leaf className="absolute -bottom-5 -right-5 h-24 w-24 rotate-12 text-canopy-sage/45" />

        <div className="relative z-10">
          <div className="mb-3 flex h-8 w-8 items-center justify-center rounded-lg bg-white/70">
            <Leaf className="h-4.5 w-4.5 text-canopy-green" />
          </div>

          <div className="font-serif text-sm font-medium leading-relaxed tracking-wide text-canopy-primary">
            Healthier Land
            <br />
            <span className="text-canopy-green">
              Brighter Tomorrow
            </span>
          </div>
        </div>
      </div>
    </aside>
  );
}