"use client"

import { useCallback } from "react"
import { toaster } from "@/components/ui/toaster"

const useCustomToast = () => {
  const showSuccessToast = useCallback((description: string) => {
    toaster.create({
      title: "Success",
      description,
      type: "success",
    })
  }, [])

  const showErrorToast = useCallback((description: string) => {
    toaster.create({
      title: "Something went wrong",
      description,
      type: "error",
    })
  }, [])

  return { showSuccessToast, showErrorToast }
}

export default useCustomToast
