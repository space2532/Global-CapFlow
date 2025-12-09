import { useState } from 'react';
import { Header } from './components/Header';
import { HeroSection } from './components/HeroSection';
import { DataGrid } from './components/DataGrid';
import { BottomNavigation } from './components/BottomNavigation';
import { RankingPage } from './components/RankingPage';
import { StockProfilePage } from './components/StockProfilePage';
import { RankingListPage } from './components/RankingListPage';
import { ComparisonPage } from './components/ComparisonPage';

export default function App() {
  const [currentPage, setCurrentPage] = useState<'home' | 'ranking' | 'list' | 'compare' | 'profile'>('home');
  const [selectedTicker, setSelectedTicker] = useState<string>('');
  const [selectedSector, setSelectedSector] = useState<string>('전체');

  const handleNavigate = (page: string) => {
    setCurrentPage(page as 'home' | 'ranking' | 'list' | 'compare' | 'profile');
  };

  const handleViewProfile = (ticker: string) => {
    setSelectedTicker(ticker);
    setCurrentPage('profile');
  };

  const handleNavigateToList = (sector?: string) => {
    if (sector) {
      setSelectedSector(sector);
    } else {
      setSelectedSector('전체');
    }
    setCurrentPage('list');
  };

  const handleBackFromProfile = () => {
    setCurrentPage('ranking');
  };

  if (currentPage === 'profile') {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100">
        <StockProfilePage ticker={selectedTicker} onBack={handleBackFromProfile} />
        <BottomNavigation currentPage="ranking" onNavigate={handleNavigate} />
      </div>
    );
  }

  if (currentPage === 'compare') {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100">
        <ComparisonPage />
        <BottomNavigation currentPage={currentPage} onNavigate={handleNavigate} />
      </div>
    );
  }

  if (currentPage === 'list') {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100">
        <RankingListPage onViewProfile={handleViewProfile} sector={selectedSector} />
        <BottomNavigation currentPage={currentPage} onNavigate={handleNavigate} />
      </div>
    );
  }

  if (currentPage === 'ranking') {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100">
        <RankingPage onViewProfile={handleViewProfile} />
        <BottomNavigation currentPage={currentPage} onNavigate={handleNavigate} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 pb-24">
      <Header />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <HeroSection onNavigateToList={handleNavigateToList} />
        <DataGrid onViewProfile={handleViewProfile} onNavigateToList={handleNavigateToList} />
      </main>
      <BottomNavigation currentPage={currentPage} onNavigate={handleNavigate} />
    </div>
  );
}