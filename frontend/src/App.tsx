import { useState, useRef, useEffect } from 'react';

import { v4 as uuidv4 } from 'uuid';

import Sidebar from './components/Sidebar';
import RightPanel from './components/RightPanel';

import { sendChatMessage } from './api';

import type {
  Message,
  EnvironmentalProfile,
  Recommendation,
  Evidence,
} from './types';

import {
  Send,
  Sprout,
  Bug,
  Map,
  BarChart3,
  User,
  Leaf,
} from 'lucide-react';

export default function App() {
  const [sessionId, setSessionId] = useState(uuidv4());
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const [profile, setProfile] = useState<EnvironmentalProfile>({});
  const [recommendation, setRecommendation] =
    useState<Recommendation | null>(null);
  const [evidence, setEvidence] = useState<Evidence[]>([]);

  const endOfMessagesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({
      behavior: 'smooth',
    });
  }, [messages, isLoading]);

  const handleNewAssessment = () => {
    setSessionId(uuidv4());
    setMessages([]);
    setProfile({});
    setRecommendation(null);
    setEvidence([]);
  };

  const handleSend = async (text: string = input) => {
    if (!text.trim() || isLoading) return;

    const userMsg: Message = {
      id: uuidv4(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const res = await sendChatMessage(sessionId, text);

      const botMsg: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: res.response,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, botMsg]);
      setProfile(res.profile);
      setRecommendation(res.recommendation);
      setEvidence(res.retrieved_evidence);
    } catch (_err) {
      setMessages((prev) => [
        ...prev,
        {
          id: uuidv4(),
          role: 'assistant',
          content:
            "Canopy couldn't process that message. Please try again.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const latestAssistantMessageId = [...messages]
    .reverse()
    .find((message) => message.role === 'assistant')?.id;

  return (
    <div className="flex h-screen overflow-hidden bg-canopy-bg font-sans">
      <Sidebar onNewChat={handleNewAssessment} />

      <div className="relative flex h-full flex-1 flex-col">
        <header className="flex h-14 items-center justify-between border-b border-canopy-border bg-white px-6">
          <div className="text-sm font-medium text-canopy-muted">
            Environmental Assessment
          </div>

          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2 text-canopy-green">
              <div className="h-2 w-2 animate-pulse rounded-full bg-canopy-green" />
              SYSTEM ONLINE
            </div>

            <button
              onClick={handleNewAssessment}
              className="rounded-md bg-canopy-primary px-3 py-1.5 text-white transition-colors hover:bg-canopy-green"
            >
              + New Assessment
            </button>

            <div className="h-4 w-px bg-canopy-border" />

            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gray-200 font-medium">
              VB
            </div>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-6 md:p-12">
          {messages.length === 0 ? (
            <div className="mx-auto mt-12 max-w-3xl">
              <div className="mb-2 text-xs font-bold tracking-widest text-canopy-muted">
                AI ENVIRONMENTAL SCIENTIST
              </div>

              <h1 className="mb-4 font-serif text-4xl text-canopy-primary">
                Understand your environment.
              </h1>

              <p className="mb-12 text-canopy-muted">
                Ask Canopy about your soil, climate, land,
                biodiversity, and environmental risks.
              </p>

              <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
                {[
                  {
                    icon: Sprout,
                    title: 'Analyze my soil',
                    desc: 'Get insights about your soil health',
                    prompt: 'I need to analyze my soil health.',
                  },
                  {
                    icon: Bug,
                    title: 'Improve biodiversity',
                    desc: 'Biodiversity suggestions for your land',
                    prompt: 'How can I improve biodiversity on my farm?',
                  },
                  {
                    icon: Map,
                    title: 'Understand my farm',
                    desc: 'Get a complete assessment',
                    prompt:
                      "I'd like to do a complete environmental assessment of my farm.",
                  },
                  {
                    icon: BarChart3,
                    title: 'What should I improve?',
                    desc: 'Prioritized recommendations',
                    prompt:
                      'What environmental metrics should I prioritize improving?',
                  },
                ].map((card) => (
                  <button
                    key={card.title}
                    onClick={() => handleSend(card.prompt)}
                    className="group rounded-xl border border-canopy-border bg-white p-4 text-left transition-colors hover:border-canopy-green"
                  >
                    <card.icon className="mb-3 h-6 w-6 text-canopy-green" />

                    <div className="mb-1 text-sm font-semibold text-canopy-primary">
                      {card.title}
                    </div>

                    <div className="text-xs text-canopy-muted">
                      {card.desc}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="mx-auto max-w-3xl space-y-6 pb-24">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex gap-4 ${
                    msg.role === 'user' ? 'flex-row-reverse' : ''
                  }`}
                >
                  <div
                    className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                      msg.role === 'user'
                        ? 'bg-gray-200 text-gray-600'
                        : 'bg-canopy-primary text-white'
                    }`}
                  >
                    {msg.role === 'user' ? (
                      <User size={16} />
                    ) : (
                      <Leaf size={16} />
                    )}
                  </div>

                  <div
                    className={`max-w-[88%] ${
                      msg.role === 'user'
                        ? 'rounded-2xl rounded-tr-none border border-canopy-border bg-white px-5 py-3 text-sm text-canopy-primary shadow-sm'
                        : 'pt-1 text-sm leading-relaxed text-canopy-primary'
                    }`}
                  >
                    {msg.role === 'user' ? (
                      msg.content
                    ) : (
                      <>
                        <div className="mb-2 text-xs font-bold uppercase tracking-wide text-canopy-muted">
                          CANOPY
                        </div>

                        <div className="rounded-2xl border border-canopy-border bg-white px-6 py-5 shadow-sm">
                          <div className="text-sm leading-7 text-canopy-primary">
                            {msg.content}
                          </div>

                          {recommendation &&
                            msg.id === latestAssistantMessageId && (
                              <div className="mt-5 overflow-hidden rounded-2xl border border-canopy-teal/20 bg-canopy-sage/20">
                                <div className="border-b border-canopy-teal/10 px-5 py-3">
                                  <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-canopy-green">
                                    <Leaf className="h-4 w-4" />
                                    Environmental Insight
                                  </div>
                                </div>

                                <div className="px-5 py-5">
                                  <h3 className="mb-3 text-lg font-bold leading-snug text-canopy-primary">
                                    {recommendation.recommendation}
                                  </h3>

                                  <p className="text-sm leading-6 text-canopy-muted">
                                    {recommendation.why}
                                  </p>

                                  {recommendation.affected_metrics.length > 0 && (
                                    <div className="mt-5">
                                      <div className="mb-2 text-xs font-semibold uppercase tracking-wide text-canopy-green">
                                        Key Environmental Benefits
                                      </div>

                                      <div className="flex flex-wrap gap-2">
                                        {recommendation.affected_metrics.map(
                                          (metric) => (
                                            <span
                                              key={metric}
                                              className="rounded-lg border border-canopy-border bg-white px-3 py-2 text-xs font-medium text-canopy-teal"
                                            >
                                              {metric}
                                            </span>
                                          ),
                                        )}
                                      </div>
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}
                        </div>
                      </>
                    )}
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex gap-4">
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-canopy-primary">
                    <Leaf
                      size={16}
                      className="animate-pulse text-white"
                    />
                  </div>

                  <div className="pt-2 text-sm text-canopy-muted animate-pulse">
                    Canopy is analyzing...
                  </div>
                </div>
              )}

              <div ref={endOfMessagesRef} />
            </div>
          )}
        </div>

        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-canopy-bg via-canopy-bg to-transparent p-6">
          <div className="mx-auto flex max-w-3xl items-center rounded-xl border border-canopy-border bg-white p-2 shadow-sm transition-all focus-within:ring-2 focus-within:ring-canopy-green/20">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Ask Canopy anything about your environment..."
              className="flex-1 bg-transparent px-4 py-2 text-sm text-canopy-primary outline-none placeholder:text-canopy-muted"
            />

            <button
              onClick={() => handleSend()}
              disabled={!input.trim() || isLoading}
              className="rounded-lg bg-canopy-green p-2 text-white transition-colors hover:bg-canopy-teal disabled:opacity-50"
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      </div>

      <RightPanel
        profile={profile}
        recommendation={recommendation}
        evidence={evidence}
        isLoading={isLoading}
      />
    </div>
  );
}