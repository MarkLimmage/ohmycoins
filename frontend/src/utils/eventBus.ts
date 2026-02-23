type Listener = (message: string) => void
const listeners: Listener[] = []

export const onError = (listener: Listener) => {
  listeners.push(listener)
  return () => {
    const index = listeners.indexOf(listener)
    if (index > -1) listeners.splice(index, 1)
  }
}

export const emitError = (message: string) => {
  listeners.forEach((l) => l(message))
}
