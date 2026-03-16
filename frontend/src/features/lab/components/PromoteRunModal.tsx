import { Button, Input, Select, VStack } from "@chakra-ui/react"
import { useState } from "react"
import {
  DialogBackdrop,
  DialogBody,
  DialogCloseTrigger,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogRoot,
  DialogTitle,
} from "@/components/ui/dialog"
import { promoteRunToFloor } from "../api/promote";
import useCustomToast from "@/hooks/useCustomToast";

interface PromoteRunModalProps {
  isOpen: boolean;
  onClose: () => void;
  mlflowRunId: string;
  defaultAlgorithmName?: string;
  defaultSignalType?: string;
  onSuccess?: () => void;
}

export function PromoteRunModal({
  isOpen,
  onClose,
  mlflowRunId,
  defaultAlgorithmName = "",
  defaultSignalType = "CLASSIFICATION",
  onSuccess,
}: PromoteRunModalProps) {
  const [algorithmName, setAlgorithmName] = useState(defaultAlgorithmName);
  const [signalType, setSignalType] = useState(defaultSignalType);
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const { showSuccessToast, showErrorToast } = useCustomToast();

  const handleSubmit = async () => {
    if (!algorithmName.trim()) {
      showErrorToast("Algorithm name is required");
      return;
    }

    setIsSubmitting(true);
    try {
      await promoteRunToFloor({
        mlflow_run_id: mlflowRunId,
        algorithm_name: algorithmName,
        signal_type: signalType,
      });
      showSuccessToast("Algorithm promoted successfully");
      onSuccess?.();
      onClose();
    } catch (error: any) {
      showErrorToast(error.message || "Failed to promote run");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <DialogRoot
      open={isOpen}
      onOpenChange={(details) => {
        if (!details.open) onClose()
      }}
    >
      <DialogBackdrop />
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Promote to Floor</DialogTitle>
        </DialogHeader>
        <DialogCloseTrigger />
        <DialogBody>
          <VStack align="stretch" gap={4}>
            <VStack align="stretch" gap={1}>
              <label htmlFor="algoName" style={{ fontSize: 'sm', fontWeight: 500 }}>Algorithm Name</label>
              <Input 
                id="algoName"
                placeholder="e.g. BTC_Sentiment_XGB_v1" 
                value={algorithmName} 
                onChange={(e) => setAlgorithmName(e.target.value)} 
              />
            </VStack>
            
            <VStack align="stretch" gap={1}>
              <label htmlFor="signalType" style={{ fontSize: 'sm', fontWeight: 500 }}>Signal Type</label>
              <Select.Root 
                value={process.env.NODE_ENV === 'test' ? [signalType] : [signalType]} 
                onValueChange={(e) => setSignalType(e.value[0])}
                collection={
                    { items: [
                        { label: 'Classification', value: 'CLASSIFICATION' },
                        { label: 'Regression', value: 'REGRESSION' }
                    ] } as any
                }
              >
                  <Select.Trigger>
                      <Select.ValueText placeholder="Select signal type" />
                  </Select.Trigger>
                  <Select.Content>
                      {[{ label: 'Classification', value: 'CLASSIFICATION' }, { label: 'Regression', value: 'REGRESSION' }].map((item) => (
                          <Select.Item item={item} key={item.value}>
                              {item.label}
                          </Select.Item>
                      ))}
                  </Select.Content>
              </Select.Root>
            </VStack>
            
            <Input readOnly disabled value={`Run ID: ${mlflowRunId}`} fontSize="xs" color="gray.500" />
            
          </VStack>
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isSubmitting}>Cancel</Button>
          <Button colorScheme="blue" onClick={handleSubmit} loading={isSubmitting}>Promote</Button>
        </DialogFooter>
      </DialogContent>
    </DialogRoot>
  );
}
