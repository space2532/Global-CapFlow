import { Home, Trophy, List, GitCompare } from 'lucide-react';

interface NavItem {
  id: 'home' | 'ranking' | 'list' | 'compare';
  icon: React.ReactNode;
  label: string;
}

const navItems: NavItem[] = [
  { id: 'home', icon: <Home className="size-5" />, label: '홈' },
  { id: 'ranking', icon: <Trophy className="size-5" />, label: 'Top 20' },
  { id: 'list', icon: <List className="size-5" />, label: 'Top 100' },
  { id: 'compare', icon: <GitCompare className="size-5" />, label: '비교' },
];

interface BottomNavigationProps {
  currentPage?: string;
  onNavigate?: (page: string) => void;
}

export function BottomNavigation({ currentPage = 'home', onNavigate }: BottomNavigationProps) {
  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-slate-900/98 backdrop-blur-lg border-t border-slate-800 shadow-2xl z-50">
      <div className="max-w-7xl mx-auto px-4">
        <div className="grid grid-cols-4 gap-1">
          {navItems.map((item) => {
            const isActive = currentPage === item.id;
            
            return (
              <button
                key={item.id}
                onClick={() => onNavigate?.(item.id)}
                className={`relative flex flex-col items-center justify-center py-3 gap-1.5 transition-all ${
                  isActive
                    ? 'text-blue-400'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <div className={`transition-transform ${isActive ? 'scale-110' : ''}`}>
                  {item.icon}
                </div>
                <span className="text-xs">{item.label}</span>
                {isActive && (
                  <div className="absolute bottom-0 w-16 h-1 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-t-full" />
                )}
              </button>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
