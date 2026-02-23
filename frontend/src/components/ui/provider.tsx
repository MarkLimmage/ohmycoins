"use client"

import { ChakraProvider } from "@chakra-ui/react"
import { type PropsWithChildren } from "react"
import { system } from "../../theme"
import { ColorModeProvider } from "./color-mode"
import { Toaster } from "./toaster"
import { ErrorProvider } from "../../context/ErrorContext"
import { AutoRefreshProvider } from "../../context/AutoRefreshContext"

export function CustomProvider(props: PropsWithChildren) {
  return (
    <ChakraProvider value={system}>
      <ColorModeProvider defaultTheme="light">
          <ErrorProvider>
            <AutoRefreshProvider>
              {props.children}
            </AutoRefreshProvider>
          </ErrorProvider>
      </ColorModeProvider>
      <Toaster />
    </ChakraProvider>
  )
}
