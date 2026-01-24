/**
 * Example usage of SafetyButton components
 * This file demonstrates how to integrate the Floor safety components
 */

import { Box, Container, Heading, HStack, VStack } from "@chakra-ui/react"
import { ConfirmTrade, EmergencyStop, KillSwitch } from "@/components/Floor"

function SafetyButtonExample() {
  // Simulated API calls
  const handleKillSwitch = async () => {
    console.log("🚨 Kill Switch activated")
    await new Promise((resolve) => setTimeout(resolve, 1000))
    // In production: await api.emergencyStop();
    console.log("✓ All algorithms stopped, positions closed")
  }

  const handleConfirmTrade = async () => {
    console.log("📈 Executing trade")
    await new Promise((resolve) => setTimeout(resolve, 1500))
    // In production: await api.executeTrade(tradeData);
    console.log("✓ Trade executed successfully")
  }

  const handleEmergencyStop = async () => {
    console.log("⛔ Emergency stop initiated")
    await new Promise((resolve) => setTimeout(resolve, 2000))
    // In production:
    // await api.cancelAllOrders();
    // await api.liquidatePositions();
    // await api.disableAlgorithms();
    console.log("✓ All trading stopped, positions liquidated")
  }

  return (
    <Container maxW="container.lg" py={8}>
      <VStack gap={8} align="stretch">
        <Box>
          <Heading size="xl" mb={4}>
            Safety Button Components Demo
          </Heading>
        </Box>

        {/* Kill Switch - Fixed Position */}
        <Box>
          <Heading size="md" mb={2}>
            1. Kill Switch (Fixed Bottom-Right)
          </Heading>
          <Box p={4} bg="gray.50" borderRadius="md">
            <p>
              • Large 120x120px emergency button
              <br />• Fixed bottom-right position
              <br />• Keyboard shortcut: <kbd>Ctrl+Shift+K</kbd>
              <br />• Requires confirmation before executing
            </p>
          </Box>
          <KillSwitch onKill={handleKillSwitch} />
        </Box>

        {/* Confirm Trade */}
        <Box>
          <Heading size="md" mb={2}>
            2. Confirm Trade Button
          </Heading>
          <Box p={4} bg="gray.50" borderRadius="md">
            <HStack gap={4}>
              <ConfirmTrade
                onConfirm={handleConfirmTrade}
                tradeDetails="BUY 100 BTC at $50,000"
              />
              <Box>
                <p>
                  • Two-step confirmation modal
                  <br />• Amber/orange color (warning)
                  <br />• 5-second cooldown after use
                </p>
              </Box>
            </HStack>
          </Box>
        </Box>

        {/* Emergency Stop */}
        <Box>
          <Heading size="md" mb={2}>
            3. Emergency Stop (Typed Confirmation)
          </Heading>
          <Box p={4} bg="gray.50" borderRadius="md">
            <HStack gap={4}>
              <EmergencyStop
                onStop={handleEmergencyStop}
                consequences={[
                  "Cancel all pending orders",
                  "Liquidate all open positions",
                  "Disable all trading algorithms",
                  "Block new trade execution",
                ]}
              />
              <Box>
                <p>
                  • Requires typing "STOP" to confirm
                  <br />• Shows consequences list
                  <br />• Large red button with icon
                  <br />• 5-second cooldown
                </p>
              </Box>
            </HStack>
          </Box>
        </Box>

        {/* Features */}
        <Box>
          <Heading size="md" mb={2}>
            Common Features
          </Heading>
          <Box p={4} bg="blue.50" borderRadius="md">
            <ul style={{ paddingLeft: "20px" }}>
              <li>✅ Full keyboard navigation (Tab, Enter, Esc)</li>
              <li>✅ WCAG 2.1 AA accessibility compliance</li>
              <li>✅ ARIA live regions for screen readers</li>
              <li>✅ Focus indicators (2px blue outline)</li>
              <li>✅ Loading states with spinners</li>
              <li>✅ Success/error feedback</li>
              <li>✅ Audit logging (console in MVP)</li>
              <li>✅ Cooldown prevention (&lt;50ms interaction)</li>
            </ul>
          </Box>
        </Box>
      </VStack>
    </Container>
  )
}

export default SafetyButtonExample
