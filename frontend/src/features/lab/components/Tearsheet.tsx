import { Box, Button, Grid, GridItem, Heading, HStack, Text, VStack, Badge } from "@chakra-ui/react";
import { useState } from "react";
import { PromoteRunModal } from "./PromoteRunModal";
import { useLabContext } from "../context/LabContext";
import { FiTrendingUp, FiActivity } from "react-icons/fi";

interface TearsheetProps {
    data: {
        metrics: Record<string, number>;
        assumed_pnl_percent?: number;
        mlflow_run_id: string;
    };
}

export const Tearsheet = ({ data }: TearsheetProps) => {
    const { metrics, assumed_pnl_percent, mlflow_run_id } = data;
    const [isPromoteOpen, setIsPromoteOpen] = useState(false);
    const { state } = useLabContext();
    const blueprint = state.blueprint;

    const formatMetric = (key: string, value: number) => {
        if (key.includes('percent') || key.includes('rate') || value < 1) {
            return `${(value * 100).toFixed(2)}%`;
        }
        return value.toFixed(4);
    };

    return (
        <Box borderWidth="1px" borderRadius="lg" overflow="hidden" p={4} bg="gray.50" _dark={{ bg: "gray.800" }}>
            <VStack align="stretch" spacing={4}>
                <HStack justify="space-between">
                    <Heading size="md" display="flex" alignItems="center" gap={2}>
                        <FiActivity /> Performance Tearsheet
                    </Heading>
                    <Badge colorScheme="purple">{mlflow_run_id}</Badge>
                </HStack>

                <Grid templateColumns="repeat(auto-fit, minmax(150px, 1fr))" gap={4}>
                    <GridItem colSpan={2} bg="white" _dark={{ bg: "gray.700" }} p={4} borderRadius="md" shadow="sm" borderLeft="4px solid" borderLeftColor="green.400">
                        <Text fontSize="sm" color="gray.500">Assumed PnL</Text>
                        <Heading size="lg" color="green.500">
                            {(assumed_pnl_percent ?? 0).toFixed(2)}%
                        </Heading>
                    </GridItem>
                    
                    {Object.entries(metrics).map(([key, value]) => (
                        <GridItem key={key} bg="white" _dark={{ bg: "gray.700" }} p={3} borderRadius="md" shadow="sm">
                            <Text fontSize="xs" color="gray.500" textTransform="uppercase">{key.replace(/_/g, ' ')}</Text>
                            <Text fontSize="md" fontWeight="bold">{formatMetric(key, value)}</Text>
                        </GridItem>
                    ))}
                </Grid>

                <HStack justify="flex-end" pt={2}>
                    <Button 
                        colorScheme="blue" 
                        leftIcon={<FiTrendingUp />}
                        onClick={() => setIsPromoteOpen(true)}
                        isDisabled={!mlflow_run_id}
                    >
                        Promote to Floor
                    </Button>
                </HStack>

                <PromoteRunModal 
                    isOpen={isPromoteOpen}
                    onClose={() => setIsPromoteOpen(false)}
                    mlflowRunId={mlflow_run_id}
                    defaultAlgorithmName={blueprint?.algorithm_recommendation ? `${blueprint.algorithm_recommendation}_v1` : `Algo_${mlflow_run_id.substring(0,8)}`}
                    defaultSignalType={blueprint?.ml_task_type || "CLASSIFICATION"}
                />
            </VStack>
        </Box>
    );
};
