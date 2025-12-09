import { TrendingUp, User } from 'lucide-react';

export function Header() {
  return (
    <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-3">
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 p-2 rounded-lg">
              <TrendingUp className="size-6 text-white" />
            </div>
            <span className="text-xl text-slate-100">
              Global CapFlow
            </span>
          </div>
          
          <div className="flex items-center gap-4">
            <button className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors">
              <User className="size-5 text-slate-300" />
              <span className="text-sm text-slate-300">프로필</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}