import { useEffect, useMemo, useState } from "react";
import { Activity, Image as ImageIcon, Lightbulb, MessageSquare, Mic, Sparkles, Trash2, X } from "lucide-react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Person } from "./AvatarGrid";
import {
  analyzeChat,
  analyzeChatImage,
  analyzeVoice,
  AnalyzeChatPayloadMessage,
  getRelationshipSummary,
  VoiceAnalyzeData,
} from "@/lib/api";

interface Props {
  person: Person;
  onClose: () => void;
  onUpdate: (person: Person) => void;
  onDelete: (id: number) => void;
}

type InputMode = "text" | "screenshot" | "audio";

const EmotionModal = ({ person, onClose, onUpdate, onDelete }: Props) => {
  const [activeMode, setActiveMode] = useState<InputMode>("text");
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [analysisDate, setAnalysisDate] = useState(new Date().toISOString().slice(0, 10));
  const [chatInput, setChatInput] = useState("");
  const [analysing, setAnalysing] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<number | null>(person.conversationId ?? null);
  const [stage, setStage] = useState<string | null>(person.relationshipStage ?? null);
  const [currentMood, setCurrentMood] = useState<string | null>(person.currentMood ?? null);
  const [emotionCounts, setEmotionCounts] = useState<Record<string, number>>(person.emotionCounts ?? {});
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [selectedAudio, setSelectedAudio] = useState<File | null>(null);
  const [voiceData, setVoiceData] = useState<VoiceAnalyzeData | null>(null);
  const [metrics, setMetrics] = useState<{
    positive_score: number;
    negative_score: number;
    affection_score: number;
    message_count: number;
    date: string;
  } | null>(person.metrics ?? null);
  const [timeline, setTimeline] = useState<Array<{
    date: string;
    positive_score: number;
    negative_score: number;
    affection_score: number;
    message_count: number;
  }>>(person.timeline ?? []);

  const parseLinesToMessages = (): AnalyzeChatPayloadMessage[] => {
    const lines = chatInput
      .split("\n")
      .map((l) => l.trim())
      .filter(Boolean);

    const messages: AnalyzeChatPayloadMessage[] = [];
    for (const line of lines) {
      // expected format: Name: message
      const sep = line.indexOf(":");
      if (sep === -1) continue;
      const sender = line.slice(0, sep).trim();
      const text = line.slice(sep + 1).trim();
      if (sender && text) {
        messages.push({ sender, text });
      }
    }
    return messages;
  };

  const loadSummary = async (cid: number, endDate?: string) => {
    const summary = await getRelationshipSummary(cid, endDate);
    const nextTimeline = summary.data?.metrics_last_7_days ?? [];
    const newestMetric = nextTimeline.length > 0 ? nextTimeline[nextTimeline.length - 1] : null;
    const summaryEmotionCounts = summary.data?.emotion_counts ?? {};
    setTimeline(nextTimeline);
    setMetrics(newestMetric);
    if (Object.keys(summaryEmotionCounts).length > 0) {
      setEmotionCounts(summaryEmotionCounts);
    }
    onUpdate({
      ...person,
      conversationId: cid,
      relationshipStage: summary.data?.relationship_stage ?? stage ?? undefined,
      currentMood: summary.data?.current_mood ?? currentMood ?? undefined,
      emotionCounts: Object.keys(summaryEmotionCounts).length > 0 ? summaryEmotionCounts : emotionCounts,
      metrics: newestMetric,
      timeline: nextTimeline,
    });
  };

  useEffect(() => {
    const cid = person.conversationId;
    if (!cid) return;
    loadSummary(cid).catch(() => {
      // keep existing state when summary fetch fails
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [person.conversationId]);

  const runTextAnalysis = async () => {
    const messages = parseLinesToMessages();
    if (messages.length === 0) {
      setError("Please add chat lines in format: Sender: message");
      return;
    }
    setError(null);
    setAnalysing(true);
    try {
      const res = await analyzeChat(messages, analysisDate, conversationId ?? undefined);
      const data = res.data;
      if (!data) throw new Error("Empty response");
      setConversationId(data.conversation_id);
      setStage(data.relationship_stage ?? null);
      setCurrentMood(data.current_mood ?? null);
      setMetrics(data.relationship_metrics ?? null);
      await loadSummary(data.conversation_id, analysisDate);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to analyze chat");
    } finally {
      setAnalysing(false);
    }
  };

  const runScreenshotAnalysis = async () => {
    if (!selectedImage) {
      setError("Please select a chat screenshot first.");
      return;
    }
    setError(null);
    setAnalysing(true);
    try {
      const res = await analyzeChatImage(
        selectedImage,
        analysisDate,
        conversationId ?? undefined,
        person.name,
        "Me",
      );
      const data = res.data;
      if (!data) throw new Error("Empty response");
      setConversationId(data.conversation_id);
      setStage(data.relationship_stage ?? null);
      setCurrentMood(data.current_mood ?? null);
      setMetrics(data.relationship_metrics ?? null);
      await loadSummary(data.conversation_id, analysisDate);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to analyze screenshot");
    } finally {
      setAnalysing(false);
    }
  };

  const runVoiceAnalysis = async () => {
    if (!selectedAudio) {
      setError("Please select an audio file first.");
      return;
    }
    setError(null);
    setAnalysing(true);
    try {
      const res = await analyzeVoice(selectedAudio, analysisDate, conversationId ?? undefined);
      if (!res.data) throw new Error("Empty voice response");
      setVoiceData(res.data);
      setCurrentMood(res.data.dominant_emotion ?? currentMood ?? null);
      if (conversationId) {
        await loadSummary(conversationId, analysisDate);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to analyze voice");
    } finally {
      setAnalysing(false);
    }
  };

  const handleDelete = () => {
    if (confirmDelete) {
      onDelete(person.id);
      onClose();
    } else {
      setConfirmDelete(true);
      setTimeout(() => setConfirmDelete(false), 3000);
    }
  };

  const emotionList = useMemo(
    () =>
      Object.entries(emotionCounts).sort((a, b) => b[1] - a[1]),
    [emotionCounts],
  );
  const graphData = useMemo(
    () =>
      [...timeline]
        .reverse()
        .map((d) => ({
          date: d.date.slice(5),
          positive: Number(d.positive_score.toFixed(2)),
          negative: Number(d.negative_score.toFixed(2)),
          affection: Number(d.affection_score.toFixed(2)),
        })),
    [timeline],
  );
  const totalAnalyzedMessages = useMemo(
    () => Object.values(emotionCounts).reduce((sum, count) => sum + Number(count || 0), 0),
    [emotionCounts],
  );
  const emotionSuggestions: Record<string, string[]> = {
    anger: ["Take a 5-minute pause before replying.", "Use calm words and short sentences."],
    sadness: ["Offer support and reassurance.", "Avoid harsh or dismissive language."],
    fear: ["Give clarity and patience.", "Use gentle, validating responses."],
    joy: ["Keep the positive tone going.", "Share appreciation and gratitude."],
    love: ["Express warmth honestly.", "Support with consistent actions."],
    surprise: ["Ask clarifying questions first.", "Respond thoughtfully, not instantly."],
    disgust: ["Avoid blaming language.", "Refocus on constructive points."],
    neutral: ["Keep communication clear.", "Ask open-ended follow-up questions."],
  };
  const activeSuggestions = emotionSuggestions[(currentMood ?? "neutral").toLowerCase()] ?? emotionSuggestions.neutral;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-foreground/30 backdrop-blur-sm animate-fade-in" onClick={onClose} />

      <div className="relative bg-card rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto border border-border animate-scale-in">
        {/* Header */}
        <div className="gradient-love p-5 rounded-t-2xl relative">
          <div className="absolute top-3 right-3 flex items-center gap-2">
            <button
              onClick={handleDelete}
              className={`p-1.5 rounded-full transition-all duration-200 ${
                confirmDelete
                  ? "bg-primary-foreground/30 text-primary-foreground"
                  : "text-primary-foreground/50 hover:text-primary-foreground hover:bg-primary-foreground/10"
              }`}
              title={confirmDelete ? "Click again to confirm" : "Delete person"}
            >
              <Trash2 className="w-4 h-4" />
            </button>
            <button onClick={onClose} className="text-primary-foreground/70 hover:text-primary-foreground transition-colors">
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full border-2 border-primary-foreground/20 overflow-hidden flex-shrink-0">
              <div className="w-full h-full bg-primary-foreground/20 flex items-center justify-center">
                <span className="text-primary-foreground font-bold text-xl tracking-wide">{person.initials}</span>
            </div>
            </div>
            <div>
              <h2 className="font-display text-2xl font-bold text-primary-foreground tracking-tight">{person.name}, {person.age}</h2>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-primary-foreground/70 text-sm">Conversation analysis</span>
              </div>
            </div>
          </div>
          {confirmDelete && (
            <p className="text-primary-foreground/80 text-xs mt-2 animate-fade-in">Click delete again to confirm removal</p>
          )}
        </div>

        <div className="p-5 space-y-6">
          <div className="rounded-xl border border-border p-2 grid grid-cols-3 gap-2 bg-secondary/50 animate-fade-in">
            <button
              onClick={() => setActiveMode("text")}
              className={`rounded-lg px-3 py-2 text-sm font-semibold transition-all duration-300 ${activeMode === "text" ? "gradient-love text-primary-foreground shadow-love" : "text-foreground/80 hover:bg-background hover:scale-[1.02]"}`}
            >
              <span className="inline-flex items-center gap-2"><MessageSquare className="w-4 h-4" />Text</span>
            </button>
            <button
              onClick={() => setActiveMode("screenshot")}
              className={`rounded-lg px-3 py-2 text-sm font-semibold transition-all duration-300 ${activeMode === "screenshot" ? "gradient-love text-primary-foreground shadow-love" : "text-foreground/80 hover:bg-background hover:scale-[1.02]"}`}
            >
              <span className="inline-flex items-center gap-2"><ImageIcon className="w-4 h-4" />Screenshot</span>
            </button>
            <button
              onClick={() => setActiveMode("audio")}
              className={`rounded-lg px-3 py-2 text-sm font-semibold transition-all duration-300 ${activeMode === "audio" ? "gradient-love text-primary-foreground shadow-love" : "text-foreground/80 hover:bg-background hover:scale-[1.02]"}`}
            >
              <span className="inline-flex items-center gap-2"><Mic className="w-4 h-4" />Audio</span>
            </button>
          </div>
          <div className="rounded-xl border border-border p-4 bg-secondary/30 animate-fade-in">
            <label className="text-sm font-semibold text-foreground mb-2 block">Analysis Date</label>
            <input
              type="date"
              value={analysisDate}
              onChange={(e) => setAnalysisDate(e.target.value)}
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm font-medium"
            />
          </div>

          {activeMode === "text" && (
            <div className="rounded-xl border border-border p-4 animate-fade-in">
              <label className="text-sm font-semibold text-foreground mb-2 block">Chat lines (Sender: message)</label>
              <textarea
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                rows={7}
                placeholder={`${person.name}: hi how are you\nMe: I am good`}
                className="w-full rounded-xl border border-border bg-background px-3 py-2 text-sm"
              />
              <button
                onClick={runTextAnalysis}
                disabled={analysing}
                className="mt-3 w-full gradient-love text-primary-foreground py-2.5 rounded-xl font-medium shadow-love hover:opacity-90 disabled:opacity-70"
              >
                {analysing ? "Analyzing..." : "Analyze Chat Text"}
              </button>
            </div>
          )}

          {activeMode === "screenshot" && (
            <div className="rounded-xl border border-border p-4 space-y-3 animate-fade-in">
              <h3 className="text-sm font-semibold text-foreground">Chat Screenshot Analysis</h3>
              <input
                type="file"
                accept="image/*"
                onChange={(e) => setSelectedImage(e.target.files?.[0] ?? null)}
                className="w-full text-sm"
              />
              <button
                onClick={runScreenshotAnalysis}
                disabled={analysing}
                className="w-full gradient-love text-primary-foreground py-2.5 rounded-xl font-medium shadow-love hover:opacity-90 disabled:opacity-70"
              >
                {analysing ? "Analyzing..." : "Analyze Chat Screenshot"}
              </button>
            </div>
          )}

          {activeMode === "audio" && (
            <div className="rounded-xl border border-border p-4 space-y-3 animate-fade-in">
              <h3 className="text-sm font-semibold text-foreground">Audio File Analysis</h3>
              <input
                type="file"
                accept="audio/*,.wav,.mp3,.ogg,.flac,.m4a"
                onChange={(e) => setSelectedAudio(e.target.files?.[0] ?? null)}
                className="w-full text-sm"
              />
              <button
                onClick={runVoiceAnalysis}
                disabled={analysing}
                className="w-full gradient-love text-primary-foreground py-2.5 rounded-xl font-medium shadow-love hover:opacity-90 disabled:opacity-70"
              >
                {analysing ? "Analyzing..." : "Analyze Audio"}
              </button>
              {voiceData && (
                <p className="text-sm text-muted-foreground">
                  Voice Emotion: <span className="font-medium text-foreground capitalize">{voiceData.dominant_emotion ?? "neutral"}</span>
                  {" | "}Stress: {voiceData.stress_level.toFixed(2)}
                </p>
              )}
            </div>
          )}

          {error && <div className="text-sm text-red-500">{error}</div>}

          <div className="bg-secondary rounded-xl p-4">
            <h3 className="text-sm font-semibold text-foreground mb-2 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-primary" />
              Relationship Analysis
            </h3>
            <div className="text-sm text-muted-foreground space-y-1">
              <p>Conversation ID: {conversationId ?? "-"}</p>
              <p>Relationship Stage: <span className="font-medium text-foreground">{stage ?? "-"}</span></p>
              <p>Current Mood: <span className="font-medium text-foreground capitalize">{currentMood ?? "-"}</span></p>
              <p>Messages analyzed: {totalAnalyzedMessages}</p>
              <p>Positive: {metrics ? metrics.positive_score.toFixed(2) : "-"} | Negative: {metrics ? metrics.negative_score.toFixed(2) : "-"} | Affection: {metrics ? metrics.affection_score.toFixed(2) : "-"}</p>
            </div>
            <button
              onClick={() => setShowSuggestions((v) => !v)}
              className="mt-3 inline-flex items-center gap-2 rounded-lg border border-border px-3 py-1.5 text-sm hover:bg-background"
            >
              <Lightbulb className="w-4 h-4 text-primary" />
              {showSuggestions ? "Hide Suggestions" : "Show Suggestions"}
            </button>
            {showSuggestions && (
              <div className="mt-3 rounded-lg border border-border bg-background p-3">
                <p className="text-sm font-semibold text-foreground mb-1 capitalize">Suggestions for {currentMood ?? "neutral"} mood</p>
                <ul className="text-sm text-muted-foreground space-y-1">
                  {activeSuggestions.map((tip) => (
                    <li key={tip}>- {tip}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <div className="rounded-xl border border-border p-4">
            <h3 className="text-sm font-semibold text-foreground mb-2">Emotion Counts</h3>
            {emotionList.length === 0 ? (
              <p className="text-sm text-muted-foreground">No results yet.</p>
            ) : (
              <ul className="grid grid-cols-2 gap-2 text-sm text-muted-foreground">
                {emotionList.map(([emotion, count]) => (
                  <li key={emotion} className="rounded-lg border border-border px-2 py-1 bg-secondary/40">
                    <span className="capitalize">{emotion}</span>: <span className="font-medium text-foreground">{count}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="rounded-xl border border-border p-4">
            <h3 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
              <Activity className="w-4 h-4 text-primary" />
              Emotion Intensity Trend
            </h3>
            {timeline.length === 0 ? (
              <p className="text-sm text-muted-foreground">No timeline data yet.</p>
            ) : (
              <div className="h-56 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={graphData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis domain={[0, 1]} />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="positive" fill="#22c55e" radius={[4, 4, 0, 0]} animationDuration={900} />
                    <Bar dataKey="negative" fill="#ef4444" radius={[4, 4, 0, 0]} animationDuration={900} />
                    <Bar dataKey="affection" fill="#e11d48" radius={[4, 4, 0, 0]} animationDuration={900} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmotionModal;
