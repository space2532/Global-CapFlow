import { HeatmapWidget } from './HeatmapWidget';
import { RankingWidget } from './RankingWidget';

interface DataGridProps {
  onViewProfile?: (ticker: string) => void;
  onNavigateToList?: (sector?: string) => void;
}

export function DataGrid({ onViewProfile, onNavigateToList }: DataGridProps) {
  return (
    <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2">
        <HeatmapWidget onNavigateToList={onNavigateToList} />
      </div>
      <div className="lg:col-span-1">
        <RankingWidget onViewProfile={onViewProfile} />
      </div>
    </section>
  );
}