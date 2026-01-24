import { SafetyButton } from "./SafetyButton"

interface ConfirmTradeProps {
  onConfirm: () => Promise<void>
  isDisabled?: boolean
  tradeDetails?: string
}

export const ConfirmTrade = ({
  onConfirm,
  isDisabled = false,
  tradeDetails,
}: ConfirmTradeProps) => {
  return (
    <SafetyButton
      action="confirm"
      onConfirm={onConfirm}
      requireConfirmation={true}
      isDisabled={isDisabled}
      cooldownSeconds={5}
      buttonSize="md"
      colorScheme="orange"
      label="Confirm Trade"
      description={`Confirm trade action${tradeDetails ? `: ${tradeDetails}` : ""}. This action requires confirmation.`}
    >
      Confirm Trade
    </SafetyButton>
  )
}
