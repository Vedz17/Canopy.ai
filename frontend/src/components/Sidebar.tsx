import {
  Leaf,
  MessageSquarePlus,
} from 'lucide-react';

export default function Sidebar({
  onNewChat,
}: {
  onNewChat: () => void;
}) {
  return (
    <div className="hidden h-screen w-64 flex-col border-r border-canopy-border bg-white p-4 md:flex">
      <div className="mb-1 flex items-center gap-2 text-lg font-bold text-canopy-primary">
        <Leaf className="h-6 w-6 text-canopy-green" />
        CANOPY AI
      </div>

      <div className="mb-8 text-xs text-canopy-muted">
        Environmental Intelligence
      </div>

      <nav className="flex-1">
        <button
          onClick={onNewChat}
          className="flex w-full items-center gap-3 rounded-lg bg-canopy-sage px-3 py-2 font-medium text-canopy-green transition-colors hover:bg-canopy-sage/70"
        >
          <MessageSquarePlus className="h-4 w-4" />
          New Chat
        </button>
      </nav>

      <div className="mt-auto rounded-xl bg-canopy-sage/50 p-4">
        <Leaf className="mb-2 h-8 w-8 text-canopy-green opacity-80" />

        <div className="font-serif text-sm text-canopy-primary">
          Healthier Land
          <br />
          Brighter Tomorrow
        </div>
      </div>
    </div>
  );
}