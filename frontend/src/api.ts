import type{ ChatResponse } from './types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://canopy-backend-8wpo.onrender.com';

export async function sendChatMessage(sessionId: string, message: string): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message }),
  });
  
  if (!res.ok) throw new Error('Failed to communicate with Canopy AI');
  return res.json();
}