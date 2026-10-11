import { Monitor, Moon, Sun } from "lucide-react";
import type { ThemePreference } from "@/hooks/useTheme";

const choices: {
  value: ThemePreference;
  label: string;
  icon: typeof Sun;
}[] = [
  { value: "light", label: "Light", icon: Sun },
  { value: "dark", label: "Dark", icon: Moon },
  { value: "system", label: "System", icon: Monitor },
];

interface ThemeToggleProps {
  value: ThemePreference;
  onChange: (value: ThemePreference) => void;
}

export function ThemeToggle({ value, onChange }: ThemeToggleProps) {
  return (
    <div className="theme-toggle" role="group" aria-label="Color theme">
      {choices.map(({ value: choice, label, icon: Icon }) => (
        <button
          aria-label={label}
          aria-pressed={value === choice}
          className="theme-choice"
          key={choice}
          onClick={() => onChange(choice)}
          title={label}
          type="button"
        >
          <Icon aria-hidden="true" size={14} strokeWidth={1.7} />
        </button>
      ))}
    </div>
  );
}
