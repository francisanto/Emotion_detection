import { useEffect, useMemo, useState } from "react";
import { Sparkles, Trash2, X } from "lucide-react";
import { Person } from "./AvatarGrid";
import { analyzeChat, AnalyzeChatPayloadMessage, getRelationshipSummary } from "@/lib/api";

interface Props {
  person: Person;
  onClose: () => void;
  onUpdate: (person: Person) => void;
  onDelete: (id: number) => void;
}

const EmotionModal = ({ person, onClose, onUpdate, onDelete }: Props) => {
  const [chatInput, setChatInput] = useState("");
  const [analysing, setAnalysing] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<number | null>(person.conversationId ?? null);
  const [stage, setStage] = useState<string | null>(person.relationshipStage ?? null);
  const [emotionCounts, setEmotionCounts] = useState<Record<string, number>>(person.emotionCounts ?? {});
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

  const loadSummary = async (cid: number) => {
    const summary = await getRelationshipSummary(cid);
    const nextTimeline = summary.data?.metrics_last_7_days ?? [];
    setTimeline(nextTimeline);
    onUpdate({
      ...person,
      conversationId: cid,
      relationshipStage: summary.data?.relationship_stage ?? stage ?? undefined,
      emotionCounts,
      metrics,
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
      const res = await analyzeChat(messages);
      const data = res.data;
      if (!data) throw new Error("Empty response");
      setConversationId(data.conversation_id);
      setStage(data.relationship_stage ?? null);
      setEmotionCounts(data.chat_summary?.emotions_detected ?? {});
      setMetrics(data.relationship_metrics ?? null);
      await loadSummary(data.conversation_id);
      onUpdate({
        ...person,
        conversationId: data.conversation_id,
        relationshipStage: data.relationship_stage ?? undefined,
        emotionCounts: data.chat_summary?.emotions_detected ?? {},
        metrics: data.relationship_metrics ?? null,
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to analyze chat");
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

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-foreground/30 backdrop-blur-sm animate-fade-in" onClick={onClose} />

      <div className="relative bg-card rounded-2xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto border border-border animate-scale-in">
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
                <span className="text-primary-foreground font-bold text-xl">{person.initials}</span>
            </div>
            </div>
            <div>
              <h2 className="font-display text-xl font-bold text-primary-foreground">{person.name}, {person.age}</h2>
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
          <div>
            <label className="text-sm font-semibold text-foreground mb-2 block">Chat lines (Sender: message)</label>
            <textarea
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              rows={8}
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

          {error && <div className="text-sm text-red-500">{error}</div>}

          <div className="bg-secondary rounded-xl p-4">
            <h3 className="text-sm font-semibold text-foreground mb-2 flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-primary" />
              Relationship Analysis
            </h3>
            <div className="text-sm text-muted-foreground space-y-1">
              <p>Conversation ID: {conversationId ?? "-"}</p>
              <p>Relationship Stage: <span className="font-medium text-foreground">{stage ?? "-"}</span></p>
              <p>Messages analyzed: {metrics?.message_count ?? 0}</p>
              <p>Positive: {metrics ? metrics.positive_score.toFixed(2) : "-"} | Negative: {metrics ? metrics.negative_score.toFixed(2) : "-"} | Affection: {metrics ? metrics.affection_score.toFixed(2) : "-"}</p>
            </div>
          </div>

          <div className="rounded-xl border border-border p-4">
            <h3 className="text-sm font-semibold text-foreground mb-2">Emotion Counts</h3>
            {emotionList.length === 0 ? (
              <p className="text-sm text-muted-foreground">No results yet.</p>
            ) : (
              <ul className="text-sm text-muted-foreground space-y-1">
                {emotionList.map(([emotion, count]) => (
                  <li key={emotion}>
                    <span className="capitalize">{emotion}</span>: {count}
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="rounded-xl border border-border p-4">
            <h3 className="text-sm font-semibold text-foreground mb-2">Last 7 Days Metrics</h3>
            {timeline.length === 0 ? (
              <p className="text-sm text-muted-foreground">No timeline data yet.</p>
            ) : (
              <div className="space-y-1 text-sm text-muted-foreground">
                {timeline.map((d) => (
                  <p key={d.date}>
                    {d.date}: P {d.positive_score.toFixed(2)} / N {d.negative_score.toFixed(2)} / A {d.affection_score.toFixed(2)} / M {d.message_count}
                  </p>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmotionModal;
