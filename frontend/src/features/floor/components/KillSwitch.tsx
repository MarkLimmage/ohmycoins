import { Box, Flex, Text } from "@chakra-ui/react"
import { BsOctagonFill } from "react-icons/bs"
import { SafetyButton } from "@/components/Floor"

interface KillSwitchProps {
  onEmergencyStop: () => Promise<void>
  isActive: boolean
}

export const KillSwitch = ({ onEmergencyStop, isActive }: KillSwitchProps) => {
  return (
    <Box position="fixed" bottom={8} right={8} zIndex={100}>
      <SafetyButton
        action="kill"
        onConfirm={onEmergencyStop}
        requireConfirmation={true}
        confirmationText="STOP"
        isDisabled={!isActive}
        cooldownSeconds={5}
        label="EMERGENCY STOP"
        colorScheme="red"
        w="120px"
        h="120px"
        borderRadius="lg"
        boxShadow="dark-lg"
      >
        <Flex
          direction="column"
          alignItems="center"
          justifyContent="center"
          gap={2}
        >
          <BsOctagonFill size={32} />
          <Text
            fontWeight="bold"
            fontSize="lg"
            lineHeight="1.2"
            textAlign="center"
          >
            EMERGENCY STOP
          </Text>
        </Flex>
      </SafetyButton>
    </Box>
  )
}
