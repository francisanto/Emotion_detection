import { useEffect, useMemo, useRef, useState } from "react";
import {
  Activity,
  Calendar,
  ChevronDown,
  Heart,
  Image as ImageIcon,
  Lightbulb,
  Loader2,
  MessageSquare,
  Smile,
  Sparkles,
  Trash2,
  UploadCloud,
  X,
} from "lucide-react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Person } from "./AvatarGrid";
import {
  analyzeChat,
  analyzeChatImage,
  AnalyzeChatPayloadMessage,
  getRelationshipSummary,
} from "@/lib/api";

interface Props {
  person: Person;
  onClose: () => void;
  onUpdate: (person: Person) => void;
  onDelete: (id: number) => void;
}

type InputMode = "text" | "screenshot";

const MOOD_EMOJIS: Record<string, string> = {
  joy: "😊",
  love: "💕",
  anger: "😠",
  sadness: "😢",
  fear: "😨",
  surprise: "😲",
  disgust: "😒",
  neutral: "😐",
};

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
  const fileInputRef = useRef<HTMLInputElement>(null);

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

  const posPct = metrics ? Math.round(metrics.positive_score * 100) : 0;
  const negPct = metrics ? Math.round(metrics.negative_score * 100) : 0;
  const affPct = metrics ? Math.round(metrics.affection_score * 100) : 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm animate-fade-in" onClick={onClose} />

      {/* Modal Dialog */}
      <div className="relative bg-card rounded-2xl shadow-2xl max-w-lg w-full max-h-[88vh] flex flex-col border border-border animate-scale-in overflow-hidden">
        {/* Subtle accent bar */}
        <div className="h-1 w-full gradient-love flex-shrink-0" />

        {/* Minimal Header */}
        <div className="px-4 sm:px-5 py-3 border-b border-border/70 flex items-center justify-between flex-shrink-0 bg-card">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full gradient-love flex items-center justify-center flex-shrink-0 shadow-sm ring-2 ring-primary/20">
              <span className="text-primary-foreground font-bold text-sm tracking-wide">{person.initials}</span>
            </div>
            <div>
              <h2 className="font-display text-base sm:text-lg font-bold text-foreground leading-tight flex items-center gap-1.5">
                {person.name}
                <span className="text-xs font-normal text-muted-foreground">· {person.age}y</span>
              </h2>
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground mt-0.5">
                <span>Conversation Analysis</span>
                {conversationId && (
                  <>
                    <span className="inline-block w-1 h-1 rounded-full bg-muted-foreground/40" />
                    <span className="text-[10px] font-mono text-muted-foreground/80">ID #{conversationId}</span>
                  </>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-1.5">
            {confirmDelete ? (
              <button
                onClick={handleDelete}
                className="text-xs px-2.5 py-1 rounded-lg bg-destructive text-destructive-foreground font-medium animate-pulse"
              >
                Confirm?
              </button>
            ) : (
              <button
                onClick={handleDelete}
                className="p-1.5 rounded-lg text-muted-foreground/60 hover:text-destructive hover:bg-destructive/10 transition-colors"
                title="Delete person"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-muted-foreground/60 hover:text-foreground hover:bg-muted transition-colors"
              title="Close"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Scrollable Content */}
        <div className="p-4 sm:p-5 pb-6 overflow-y-auto space-y-3.5">
          {/* Compact Toolbar: Mode Switcher + Date Picker */}
          <div className="flex items-center justify-between gap-2">
            <div className="inline-flex items-center p-0.5 bg-muted/70 rounded-xl border border-border/60">
              <button
                type="button"
                onClick={() => setActiveMode("text")}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  activeMode === "text"
                    ? "bg-card text-foreground shadow-sm font-semibold"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <MessageSquare className="w-3.5 h-3.5 text-primary" />
                <span>Text</span>
              </button>
              <button
                type="button"
                onClick={() => setActiveMode("screenshot")}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                  activeMode === "screenshot"
                    ? "bg-card text-foreground shadow-sm font-semibold"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                <ImageIcon className="w-3.5 h-3.5 text-primary" />
                <span>Screenshot</span>
              </button>
            </div>

            <div className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-muted/30 border border-border/60 rounded-xl text-xs text-muted-foreground focus-within:border-primary/40 focus-within:bg-card transition-colors">
              <Calendar className="w-3.5 h-3.5 text-muted-foreground flex-shrink-0" />
              <input
                type="date"
                value={analysisDate}
                onChange={(e) => setAnalysisDate(e.target.value)}
                className="bg-transparent text-xs text-foreground font-medium focus:outline-none cursor-pointer"
                title="Analysis Date"
              />
            </div>
          </div>

          {/* Mode 1: Text Analysis */}
          {activeMode === "text" && (
            <div className="rounded-xl border border-border/70 bg-card p-3 space-y-2.5">
              <div className="flex items-center justify-between text-xs">
                <span className="font-medium text-foreground">Chat Lines</span>
                <button
                  type="button"
                  onClick={() =>
                    setChatInput(`${person.name}: hey, how was your day?\nMe: pretty good! how about you?\n${person.name}: missed talking to you today`)
                  }
                  className="text-[11px] text-primary hover:underline font-medium"
                >
                  Insert example
                </button>
              </div>
              <textarea
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                rows={4}
                placeholder={`${person.name}: hi how are you\nMe: I am good`}
                className="w-full rounded-lg border border-border bg-background px-3 py-2 text-xs sm:text-sm text-foreground placeholder:text-muted-foreground/60 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all font-mono resize-y"
              />
              <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                <span>Format: <code className="px-1 py-0.5 rounded bg-muted text-[10px]">Sender: message</code></span>
              </div>
              <button
                type="button"
                onClick={runTextAnalysis}
                disabled={analysing}
                className="w-full gradient-love text-primary-foreground py-2 px-4 rounded-xl font-medium text-xs sm:text-sm shadow-love hover:opacity-95 active:scale-[0.99] transition-all flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {analysing ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Analyzing...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Analyze Chat Text</span>
                  </>
                )}
              </button>
            </div>
          )}

          {/* Mode 2: Screenshot Analysis */}
          {activeMode === "screenshot" && (
            <div className="rounded-xl border border-border/70 bg-card p-3 space-y-2.5">
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(e) => {
                  setSelectedImage(e.target.files?.[0] ?? null);
                }}
              />

              {!selectedImage ? (
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="border border-dashed border-border hover:border-primary/50 bg-muted/20 hover:bg-muted/40 rounded-xl p-6 text-center cursor-pointer transition-colors flex flex-col items-center justify-center gap-2"
                >
                  <div className="w-9 h-9 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                    <UploadCloud className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-foreground">Click to upload chat screenshot</p>
                    <p className="text-[11px] text-muted-foreground mt-0.5">PNG, JPG, or WebP</p>
                  </div>
                </div>
              ) : (
                <div className="border border-border/80 bg-muted/30 rounded-xl p-3 flex items-center justify-between">
                  <div className="flex items-center gap-2.5 overflow-hidden">
                    <ImageIcon className="w-5 h-5 text-primary flex-shrink-0" />
                    <div className="truncate text-xs">
                      <p className="font-medium text-foreground truncate">{selectedImage.name}</p>
                      <p className="text-[10px] text-muted-foreground">{(selectedImage.size / 1024).toFixed(0)} KB</p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setSelectedImage(null);
                      if (fileInputRef.current) fileInputRef.current.value = "";
                    }}
                    className="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                    title="Remove image"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              )}

              <button
                type="button"
                onClick={runScreenshotAnalysis}
                disabled={analysing || !selectedImage}
                className="w-full gradient-love text-primary-foreground py-2 px-4 rounded-xl font-medium text-xs sm:text-sm shadow-love hover:opacity-95 active:scale-[0.99] transition-all flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {analysing ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Processing Screenshot OCR...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Analyze Chat Screenshot</span>
                  </>
                )}
              </button>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="rounded-xl bg-destructive/10 border border-destructive/20 px-3 py-2 text-xs text-destructive flex items-center justify-between">
              <span>{error}</span>
              <button onClick={() => setError(null)} className="p-1 hover:opacity-75">
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          )}

          {/* Minimal Relationship Summary Card */}
          <div className="rounded-xl border border-border/70 bg-card p-3.5 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-foreground">
                <Sparkles className="w-3.5 h-3.5 text-primary" />
                <span>Relationship Analysis</span>
              </div>
              {totalAnalyzedMessages > 0 && (
                <span className="text-[11px] text-muted-foreground font-medium">
                  {totalAnalyzedMessages} {totalAnalyzedMessages === 1 ? "message" : "messages"}
                </span>
              )}
            </div>

            {/* Stage & Mood mini cards */}
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-muted/30 border border-border/60 rounded-lg p-2.5 flex items-center gap-2.5">
                <div className="w-7 h-7 rounded-md bg-primary/10 flex items-center justify-center flex-shrink-0 text-primary">
                  <Heart className="w-3.5 h-3.5" />
                </div>
                <div className="overflow-hidden">
                  <div className="text-[10px] text-muted-foreground uppercase font-medium">Stage</div>
                  <div className="font-semibold text-foreground capitalize truncate">
                    {stage ?? "Pending"}
                  </div>
                </div>
              </div>

              <div className="bg-muted/30 border border-border/60 rounded-lg p-2.5 flex items-center gap-2.5">
                <div className="w-7 h-7 rounded-md bg-primary/10 flex items-center justify-center flex-shrink-0 text-primary">
                  <Smile className="w-3.5 h-3.5" />
                </div>
                <div className="overflow-hidden">
                  <div className="text-[10px] text-muted-foreground uppercase font-medium">Mood</div>
                  <div className="font-semibold text-foreground capitalize truncate flex items-center gap-1">
                    <span>{MOOD_EMOJIS[(currentMood ?? "").toLowerCase()] ?? "✨"}</span>
                    <span>{currentMood ?? "Neutral"}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Metrics Breakdown if available */}
            {metrics && (
              <div className="space-y-2 pt-1 border-t border-border/50">
                <div className="grid grid-cols-3 gap-1.5 text-center">
                  <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-lg py-1 px-1.5">
                    <div className="text-[10px] text-emerald-600 dark:text-emerald-400 font-medium">Positive</div>
                    <div className="text-xs font-bold text-emerald-700 dark:text-emerald-300">{posPct}%</div>
                  </div>
                  <div className="bg-rose-500/10 border border-rose-500/20 rounded-lg py-1 px-1.5">
                    <div className="text-[10px] text-rose-600 dark:text-rose-400 font-medium">Affection</div>
                    <div className="text-xs font-bold text-rose-700 dark:text-rose-300">{affPct}%</div>
                  </div>
                  <div className="bg-red-500/10 border border-red-500/20 rounded-lg py-1 px-1.5">
                    <div className="text-[10px] text-red-600 dark:text-red-400 font-medium">Negative</div>
                    <div className="text-xs font-bold text-red-700 dark:text-red-300">{negPct}%</div>
                  </div>
                </div>
                <div className="w-full h-1.5 bg-muted rounded-full overflow-hidden flex">
                  <div style={{ width: `${posPct}%` }} className="bg-emerald-500 h-full transition-all" />
                  <div style={{ width: `${affPct}%` }} className="bg-rose-500 h-full transition-all" />
                  <div style={{ width: `${negPct}%` }} className="bg-red-500 h-full transition-all" />
                </div>
              </div>
            )}

            {/* Advice / Suggestions accordion */}
            <div className="pt-1">
              <button
                type="button"
                onClick={() => setShowSuggestions((v) => !v)}
                className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg bg-muted/40 hover:bg-muted/70 text-xs text-foreground/80 hover:text-foreground transition-colors"
              >
                <span className="flex items-center gap-1.5 font-medium">
                  <Lightbulb className="w-3.5 h-3.5 text-amber-500" />
                  <span>Advice for <span className="capitalize">{currentMood ?? "neutral"}</span> mood</span>
                </span>
                <ChevronDown
                  className={`w-3.5 h-3.5 text-muted-foreground transition-transform duration-200 ${
                    showSuggestions ? "rotate-180" : ""
                  }`}
                />
              </button>
              {showSuggestions && (
                <div className="mt-2 rounded-lg border border-border/60 bg-muted/20 p-2.5 text-xs text-muted-foreground space-y-1.5 animate-fade-in">
                  {activeSuggestions.map((tip) => (
                    <div key={tip} className="flex items-start gap-1.5">
                      <span className="text-primary font-bold">•</span>
                      <span>{tip}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Emotion Breakdown Chips (Only when data exists) */}
          {emotionList.length > 0 && (
            <div className="rounded-xl border border-border/70 bg-card p-3 space-y-2">
              <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Emotion Counts
              </div>
              <div className="flex flex-wrap gap-1.5">
                {emotionList.map(([emotion, count]) => (
                  <span
                    key={emotion}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs bg-muted/60 border border-border/50 text-foreground font-medium"
                  >
                    <span>{MOOD_EMOJIS[emotion.toLowerCase()] ?? "✨"}</span>
                    <span className="capitalize">{emotion}</span>
                    <span className="text-[10px] font-bold px-1.5 py-0.2 rounded-md bg-background border border-border/50 text-foreground">
                      {count}
                    </span>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Emotion Intensity Trend Chart (Only when timeline exists) */}
          {timeline.length > 0 && (
            <div className="rounded-xl border border-border/70 bg-card p-3 space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5 text-primary" /> Emotion Intensity Trend
                </h4>
                <span className="text-[10px] text-muted-foreground">Last {timeline.length} entries</span>
              </div>
              <div className="h-36 w-full pt-1">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={graphData} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                    <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                    <YAxis domain={[0, 1]} tick={{ fontSize: 10 }} />
                    <Tooltip contentStyle={{ fontSize: 11, borderRadius: 8 }} />
                    <Legend wrapperStyle={{ fontSize: 10, paddingTop: 4 }} />
                    <Bar dataKey="positive" fill="#22c55e" radius={[3, 3, 0, 0]} name="Positive" />
                    <Bar dataKey="negative" fill="#ef4444" radius={[3, 3, 0, 0]} name="Negative" />
                    <Bar dataKey="affection" fill="#e11d48" radius={[3, 3, 0, 0]} name="Affection" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EmotionModal;
