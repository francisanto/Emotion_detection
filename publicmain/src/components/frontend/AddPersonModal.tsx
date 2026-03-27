import { useState } from "react";
import { X, UserPlus } from "lucide-react";
import { Person } from "./AvatarGrid";

interface Props {
  onClose: () => void;
  onAdd: (person: Omit<Person, "id">) => void;
}

const AddPersonModal = ({ onClose, onAdd }: Props) => {
  const [name, setName] = useState("");
  const [age, setAge] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !age.trim()) return;

    const base = name.trim().replace(/\s+/g, "");
    const initials = base.substring(0, 2).toUpperCase() || "NA";
    const newPerson: Omit<Person, "id"> = {
      name: name.trim(),
      age: Number(age),
      initials,
      conversationId: undefined,
      relationshipStage: undefined,
      emotionCounts: {},
      metrics: null,
      timeline: [],
    };

    onAdd(newPerson);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-foreground/30 backdrop-blur-sm animate-fade-in" onClick={onClose} />
      <div className="relative bg-card rounded-2xl shadow-2xl max-w-sm w-full border border-border animate-scale-in">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <UserPlus className="w-5 h-5 text-primary" />
              <h2 className="font-display text-lg font-bold text-foreground">Add Person</h2>
            </div>
            <button onClick={onClose} className="text-muted-foreground hover:text-foreground transition-colors">
              <X className="w-5 h-5" />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm font-medium text-foreground mb-1 block">Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Enter name..."
                className="w-full px-4 py-2.5 rounded-xl border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50 transition-colors"
                required
              />
            </div>
            <div>
              <label className="text-sm font-medium text-foreground mb-1 block">Age</label>
              <input
                type="number"
                value={age}
                onChange={(e) => setAge(e.target.value)}
                placeholder="Enter age..."
                min={1}
                max={120}
                className="w-full px-4 py-2.5 rounded-xl border border-border bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/50 transition-colors"
                required
              />
            </div>
            <button
              type="submit"
              className="w-full gradient-love text-primary-foreground py-3 rounded-xl font-medium shadow-love hover:opacity-90 transition-opacity"
            >
              Add & Start Tracking
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default AddPersonModal;
