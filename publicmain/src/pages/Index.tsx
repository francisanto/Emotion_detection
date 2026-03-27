import { useRef } from "react";
import { Heart } from "lucide-react";
import HeroSection from "@/components/frontend/HeroSection";
import AvatarGrid from "@/components/frontend/AvatarGrid";

const Index = () => {
  const avatarRef = useRef<HTMLDivElement>(null);

  const handleGetStarted = () => {
    avatarRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Navbar */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-background/90 backdrop-blur-md border-b border-border/50">
        <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Heart className="w-5 h-5 text-primary fill-primary" />
            <span className="font-display text-lg font-bold text-foreground">FeelConnect</span>
          </div>
          <button
            onClick={handleGetStarted}
            className="gradient-love text-primary-foreground px-5 py-2 rounded-full text-sm font-medium shadow-love hover:opacity-90 transition-opacity"
          >
            Get Started
          </button>
        </div>
      </nav>

      <HeroSection onGetStarted={handleGetStarted} />

      <div ref={avatarRef}>
        <AvatarGrid />
      </div>

      <footer className="border-t border-border py-8 px-4 text-center">
        <p className="text-sm text-muted-foreground">FeelConnect — AI Relationship Analysis</p>
      </footer>
    </div>
  );
};

export default Index;
