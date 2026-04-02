export interface AnalyzeChatPayloadMessage {
  sender: string;
  text: string;
  timestamp?: string;
}

export interface VoiceAnalyzeData {
  stress_level: number;
  emotional_intensity: number;
  voice_confidence: number;
  dominant_emotion?: string | null;
}

export interface AnalyzeChatResponseData {
  conversation_id: number;
  relationship_stage: string;
  current_mood?: string;
  participants?: {
    person_a?: string | null;
    person_b?: string | null;
  };
  relationship_metrics?: {
    date: string;
    positive_score: number;
    negative_score: number;
    affection_score: number;
    message_count: number;
  };
  chat_summary?: {
    message_count: number;
    emotions_detected: Record<string, number>;
    relationship_stage?: string;
  };
  extracted_message_count?: number;
}

export interface ApiEnvelope<T> {
  success: boolean;
  data: T | null;
  metadata?: Record<string, unknown>;
}

const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL as string | undefined;
const baseUrlCandidates = [
  configuredBaseUrl,
  "http://127.0.0.1:8005",
  "http://127.0.0.1:8004",
  "http://localhost:8005",
  "http://localhost:8004",
].filter(Boolean) as string[];

let activeBaseUrl = baseUrlCandidates[0];

async function fetchWithFallback(path: string, init?: RequestInit): Promise<Response> {
  const urls = [activeBaseUrl, ...baseUrlCandidates.filter((u) => u !== activeBaseUrl)];
  let lastError: unknown = null;

  for (const baseUrl of urls) {
    try {
      const controller = new AbortController();
      // Large OCR/audio requests can take longer; avoid premature client aborts.
      const timeout = window.setTimeout(() => controller.abort(), 180000);
      const response = await fetch(`${baseUrl}${path}`, { ...init, signal: controller.signal });
      window.clearTimeout(timeout);
      activeBaseUrl = baseUrl;
      return response;
    } catch (err) {
      lastError = err;
    }
  }

  throw lastError ?? new Error("Failed to fetch");
}

async function handleResponse<T>(response: Response): Promise<ApiEnvelope<T>> {
  let json: ApiEnvelope<T>;
  try {
    json = (await response.json()) as ApiEnvelope<T>;
  } catch {
    throw new Error(`Server returned non-JSON response (${response.status}).`);
  }
  if (!response.ok || !json.success) {
    const err = json?.metadata?.error ?? `Request failed: ${response.status}`;
    throw new Error(String(err));
  }
  return json;
}

export async function analyzeChat(
  messages: AnalyzeChatPayloadMessage[],
  analysisDate?: string,
  conversationId?: number,
): Promise<ApiEnvelope<AnalyzeChatResponseData>> {
  const response = await fetchWithFallback(`/analyze-chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, analysis_date: analysisDate, conversation_id: conversationId }),
  });
  return handleResponse<AnalyzeChatResponseData>(response);
}

export async function analyzeChatImage(
  imageFile: File,
  analysisDate?: string,
  conversationId?: number,
  senderA?: string,
  senderB?: string,
): Promise<ApiEnvelope<AnalyzeChatResponseData>> {
  const formData = new FormData();
  formData.append("image", imageFile);
  if (analysisDate) formData.append("analysis_date", analysisDate);
  if (conversationId) formData.append("conversation_id", String(conversationId));
  if (senderA) formData.append("sender_a", senderA);
  if (senderB) formData.append("sender_b", senderB);

  const response = await fetchWithFallback(`/analyze-chat-image`, {
    method: "POST",
    body: formData,
  });
  return handleResponse<AnalyzeChatResponseData>(response);
}

export async function analyzeVoice(
  audioFile: File,
  analysisDate?: string,
  conversationId?: number,
): Promise<ApiEnvelope<VoiceAnalyzeData>> {
  const formData = new FormData();
  formData.append("audio", audioFile);
  if (analysisDate) formData.append("analysis_date", analysisDate);
  if (conversationId) formData.append("conversation_id", String(conversationId));

  const response = await fetchWithFallback(`/api/v1/voice/analyze`, {
    method: "POST",
    body: formData,
  });
  return handleResponse<VoiceAnalyzeData>(response);
}

export async function getRelationshipSummary(conversationId: number, endDate?: string): Promise<ApiEnvelope<{
  conversation_id: number;
  participants?: {
    person_a?: string | null;
    person_b?: string | null;
  };
  relationship_stage: string;
  current_mood?: string;
  stage_updated_at: string | null;
  graph_analysis?: {
    labels: string[];
    positive_series: number[];
    negative_series: number[];
    affection_series: number[];
  };
  emotion_counts?: Record<string, number>;
  metrics_last_7_days: Array<{
    date: string;
    positive_score: number;
    negative_score: number;
    affection_score: number;
    message_count: number;
  }>;
}>> {
  const query = endDate ? `?end_date=${encodeURIComponent(endDate)}` : "";
  const response = await fetchWithFallback(`/conversations/${conversationId}/relationship-summary${query}`);
  return handleResponse(response);
}

