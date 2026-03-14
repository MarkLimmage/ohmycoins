import React from 'react';
import { VStack, Box } from '@chakra-ui/react';
import { useLabContext } from './context/LabContext';
import { LabGrid } from './components/LabGrid';
import { BlueprintCard } from './components/BlueprintCard';
import { TrainingProgressChart } from './components/TrainingProgressChart';
import { ArtifactViewer } from './components/ArtifactViewer';
import { ModelPlaygroundPanel } from './components/ModelPlaygroundPanel';
import { Artifact } from './components/ArtifactViewer';
import { LabHeader } from './components/LabHeader';

interface LabSessionViewProps {
  onPromote: (artifact: Artifact) => void;
  onTest: (artifact: Artifact) => void;
  playgroundArtifact: Artifact | null;
  setPlaygroundArtifact: (artifact: Artifact | null) => void;
  approvedBlueprints: Set<string>;
  setApprovedBlueprints: React.Dispatch<React.SetStateAction<Set<string>>>;
  artifacts: Artifact[];
}

export const LabSessionView: React.FC<LabSessionViewProps> = ({
  onPromote,
  onTest,
  playgroundArtifact,
  setPlaygroundArtifact,
  approvedBlueprints,
  setApprovedBlueprints,
  artifacts
}) => {
  const { state } = useLabContext();
  const { blueprint, metrics } = state;

  return (
    <VStack align="stretch" gap={4} h="full">
      <LabHeader />
      
      <Box flex={1} overflowY="auto" px={4} pb={4}>
        <LabGrid />

        {/* Blueprint Card */}
        {blueprint && (
          <BlueprintCard
            data={blueprint}
            onApprove={() => {
              setApprovedBlueprints((prev) => {
                const next = new Set(prev);
                next.add(blueprint.target);
                return next;
              });
            }}
            isApproved={approvedBlueprints.has(blueprint.target)}
          />
        )}

        {/* Training Progress */}
        {metrics && metrics.length > 0 && (
          <TrainingProgressChart metrics={metrics} />
        )}

        {/* Artifacts */}
        {artifacts && artifacts.length > 0 && (
          <ArtifactViewer
            artifacts={artifacts}
            onPromote={onPromote}
            onTest={onTest}
          />
        )}

        {/* Model Playground */}
        {playgroundArtifact?.id && (
          <ModelPlaygroundPanel
            artifactId={playgroundArtifact.id}
            onClose={() => setPlaygroundArtifact(null)}
          />
        )}
      </Box>
    </VStack>
  );
};
