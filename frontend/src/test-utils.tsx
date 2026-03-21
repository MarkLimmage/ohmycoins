import { ChakraProvider } from "@chakra-ui/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { render } from "@testing-library/react"
import type { PropsWithChildren, ReactElement } from "react"
import { system } from "@/theme"

/**
 * Render helper that wraps components in Chakra + QueryClient providers.
 * No router context — mock @tanstack/react-router in individual tests.
 */
export function renderWithProviders(ui: ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })

  function Wrapper({ children }: PropsWithChildren) {
    return (
      <ChakraProvider value={system}>
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      </ChakraProvider>
    )
  }

  return { ...render(ui, { wrapper: Wrapper }), queryClient }
}
