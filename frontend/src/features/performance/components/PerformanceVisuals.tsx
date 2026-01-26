import React from 'react';
import { EquityCurve } from './EquityCurve';

interface EquityDataPoint {
  date: string;
  equity: number;
}

interface PerformanceVisualsProps {
    equityData: EquityDataPoint[];
}

export const PerformanceVisuals: React.FC<PerformanceVisualsProps> = ({ equityData }) => {
    return (
        <div className="space-y-6">
            <EquityCurve data={equityData} />
        </div>
    )
}
