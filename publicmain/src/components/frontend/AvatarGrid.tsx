import { useEffect, useState } from "react";
import { Plus, Sparkles } from "lucide-react";
import EmotionModal from "./EmotionModal";
import AddPersonModal from "./AddPersonModal";

const PEOPLE_STORAGE_KEY = "feelconnect_people_v1";

export interface Person {
  id: number;
  name: string;
  age: number;
  initials: string;
  conversationId?: number;
  relationshipStage?: string;
  currentMood?: string;
  emotionCounts?: Record<string, number>;
  metrics?: {
    date: string;
    positive_score: number;
    negative_score: number;
    affection_score: number;
    message_count: number;
  } | null;
  timeline?: Array<{
    date: string;
    positive_score: number;
    negative_score: number;
    affection_score: number;
    message_count: number;
  }>;
}

const AvatarGrid = () => {
  const [people, setPeople] = useState<Person[]>(() => {
    try {
      const raw = localStorage.getItem(PEOPLE_STORAGE_KEY);
      if (!raw) return [];
      const parsed = JSON.parse(raw) as Person[];
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  });
  const [selectedPerson, setSelectedPerson] = useState<Person | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);

  useEffect(() => {
    localStorage.setItem(PEOPLE_STORAGE_KEY, JSON.stringify(people));
  }, [people]);

  const handleAddPerson = (person: Omit<Person, "id">) => {
    setPeople((prev) => [...prev, { ...person, id: Date.now() }]);
    setShowAddModal(false);
  };

  const handleUpdatePerson = (updated: Person) => {
    setPeople((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
    setSelectedPerson(updated);
  };

  const handleDeletePerson = (id: number) => {
    setPeople((prev) => prev.filter((p) => p.id !== id));
    setSelectedPerson(null);
  };

  return (
    <section id="avatars" className="py-24 px-4">
      <div className="max-w-5xl mx-auto">
        <div className="text-center mb-16 animate-fade-in">
          <h2 className="font-display text-3xl md:text-4xl font-bold text-foreground mb-3">
            People To Analyze
          </h2>
          <p className="text-muted-foreground max-w-md mx-auto">
            Track chat emotions, relationship stage, mood, and 7-day emotional trends.
          </p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          <button
            onClick={() => setShowAddModal(true)}
            className="group flex flex-col items-center justify-center gap-3 rounded-2xl p-6 border-2 border-dashed border-border hover:border-primary/40 transition-all duration-300 min-h-[180px]"
          >
            <div className="w-14 h-14 rounded-full border-2 border-dashed border-muted-foreground/40 group-hover:border-primary/60 flex items-center justify-center transition-colors duration-300">
              <Plus className="w-6 h-6 text-muted-foreground group-hover:text-primary transition-colors" />
            </div>
            <span className="text-sm font-medium text-muted-foreground group-hover:text-foreground transition-colors">
              Add Person
            </span>
          </button>

          {people.map((person, i) => (
            <button
              key={person.id}
              onClick={() => setSelectedPerson(person)}
              className="group bg-card rounded-2xl p-5 border border-border hover:border-primary/40 hover:shadow-love transition-all duration-300 text-left animate-fade-in"
              style={{ animationDelay: `${i * 60}ms` }}
            >
              <div className="relative mx-auto w-14 h-14 mb-3 rounded-full gradient-love flex items-center justify-center">
                <span className="text-primary-foreground font-bold text-base">{person.initials}</span>
              </div>

              <div className="text-center">
                <h3 className="font-display text-sm font-semibold text-foreground inline-flex items-center gap-1">
                  <Sparkles className="w-3.5 h-3.5 text-primary" />
                  {person.name}, {person.age}
                </h3>
                <div className="mt-2 flex flex-col gap-1">
                  <span className="text-[11px] rounded-full px-2 py-0.5 bg-secondary text-foreground">
                    Stage: <span className="capitalize font-medium">{person.relationshipStage ?? "-"}</span>
                  </span>
                  <span className="text-[11px] rounded-full px-2 py-0.5 bg-secondary text-foreground">
                    Mood: <span className="capitalize font-medium">{person.currentMood ?? "-"}</span>
                  </span>
                </div>
              </div>
            </button>
          ))}
        </div>

        {people.length === 0 && (
          <div className="mt-8 rounded-xl border border-dashed border-border p-6 text-center text-muted-foreground">
            No conversation pairs yet. Click <span className="font-medium text-foreground">Add Person</span> to begin.
          </div>
        )}
      </div>

      {selectedPerson && (
        <EmotionModal
          person={selectedPerson}
          onClose={() => setSelectedPerson(null)}
          onUpdate={handleUpdatePerson}
          onDelete={handleDeletePerson}
        />
      )}

      {showAddModal && <AddPersonModal onClose={() => setShowAddModal(false)} onAdd={handleAddPerson} />}
    </section>
  );
};

export default AvatarGrid;
