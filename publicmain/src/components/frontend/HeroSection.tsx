import { useState, useEffect } from "react";
import { Heart, Sparkles } from "lucide-react";
import heroBg1 from "@/assets/hero-bg-1.jpg";
import heroBg2 from "@/assets/hero-bg-2.jpg";
import heroBg3 from "@/assets/hero-bg-3.jpg";
import heroBg4 from "@/assets/hero-bg-4.jpg";

const backgrounds = [heroBg1, heroBg2, heroBg3, heroBg4];
const captions = ["Lovers", "Hearts", "Friends", "Romance"];

const HeroSection = ({ onGetStarted }: { onGetStarted: () => void }) => {
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % backgrounds.length);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Cycling backgrounds with crossfade */}
      {backgrounds.map((bg, i) => (
        <div
          key={i}
          className="absolute inset-0 transition-opacity duration-[1500ms] ease-in-out"
          style={{ opacity: i === currentIndex ? 1 : 0 }}
        >
          <img
            src={bg}
            alt={captions[i]}
            className="w-full h-full object-cover"
            width={1920}
            height={1080}
          />
        </div>
      ))}

      {/* Overlay */}
      <div className="absolute inset-0 bg-background/70" />
      <div className="absolute inset-0 bg-gradient-to-b from-background/40 via-transparent to-background" />

      {/* Content */}
      <div className="relative z-10 text-center px-4 max-w-3xl mx-auto animate-fade-in">
        <div className="flex items-center justify-center gap-2 mb-6">
          <Heart className="w-10 h-10 text-primary fill-primary animate-pulse-heart" />
        </div>

        <h1 className="font-display text-5xl md:text-7xl font-bold mb-6 tracking-tight text-foreground">
          Feel the{" "}
          <span className="text-gradient-love">Connections</span>
        </h1>

        {/* Animated caption */}
        <p className="text-sm font-medium text-primary mb-4 tracking-widest uppercase transition-opacity duration-700">
          {captions[currentIndex]}
        </p>

        <p className="text-lg text-muted-foreground max-w-xl mx-auto mb-12 leading-relaxed">
          AI-powered relationship analysis for dating apps. Understand emotions
          through images and voice to predict connection strength.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <button
            onClick={onGetStarted}
            className="gradient-love text-primary-foreground px-10 py-4 text-lg font-semibold rounded-full shadow-love hover:opacity-90 transition-all duration-300 hover:scale-105 flex items-center gap-2"
          >
            <Sparkles className="w-5 h-5" />
            Get Started
          </button>
        </div>

        {/* Slide indicators */}
        <div className="mt-10 flex items-center justify-center gap-2">
          {backgrounds.map((_, i) => (
            <button
              key={i}
              onClick={() => setCurrentIndex(i)}
              className={`w-2 h-2 rounded-full transition-all duration-500 ${
                i === currentIndex
                  ? "w-6 bg-primary"
                  : "bg-muted-foreground/30 hover:bg-muted-foreground/50"
              }`}
              aria-label={`Show ${captions[i]}`}
            />
          ))}
        </div>

        <div className="mt-12 flex items-center justify-center gap-8 text-muted-foreground">
          <div className="text-center">
            <p className="text-2xl font-bold text-foreground">6+</p>
            <p className="text-xs">Emotion Types</p>
          </div>
          <div className="w-px h-8 bg-border" />
          <div className="text-center">
            <p className="text-2xl font-bold text-foreground">AI</p>
            <p className="text-xs">Powered</p>
          </div>
          <div className="w-px h-8 bg-border" />
          <div className="text-center">
            <p className="text-2xl font-bold text-foreground">Live</p>
            <p className="text-xs">Analysis</p>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;
