import { 
  Box, 
  Button, 
  Flex, 
  Input, 
  Stack, 
  Text,
  createListCollection
} from "@chakra-ui/react"
import { useForm, Controller } from "react-hook-form"
import { CollectorPlugin, CollectorCreate, CollectorInstance } from "./types"
import { useCollectors } from "./hooks"
import { SelectContent, SelectItem, SelectRoot, SelectTrigger, SelectValueText } from "@/components/ui/select"
import { Field } from "@/components/ui/field"

interface CollectorPluginFormProps {
  plugins: CollectorPlugin[]
  initialValues?: CollectorInstance
  onCancel: () => void
  onSuccess: () => void
}

export const CollectorPluginForm = ({ plugins, initialValues, onCancel, onSuccess }: CollectorPluginFormProps) => {
  const { createInstance, updateInstance } = useCollectors()
  const { register, handleSubmit, control, watch, reset } = useForm<CollectorCreate>({
    defaultValues: initialValues ? {
      name: initialValues.name,
      plugin_id: initialValues.plugin_id,
      config: initialValues.config
    } : undefined
  })
  const selectedPluginId = watch("plugin_id")
  
  // Find selected plugin to render its schema
  const selectedPlugin = plugins.find(p => p.id === selectedPluginId)

  const onSubmit = (data: CollectorCreate) => {
    if (initialValues) {
      updateInstance.mutate({ id: initialValues.id, data }, {
        onSuccess: () => {
          reset()
          onSuccess()
        }
      })
    } else {
      createInstance.mutate(data, {
        onSuccess: () => {
          reset()
          onSuccess()
        }
      })
    }
  }

  const pluginCollection = createListCollection({
    items: plugins.map(p => ({ label: p.name, value: p.id }))
  })

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <Stack gap={4} py={4}>
        <Field label="Name">
          <Input {...register("name", { required: true })} placeholder="My Collector Instance" />
        </Field>

        <Field label="Plugin Strategy">
          <Controller
            control={control}
            name="plugin_id"
            rules={{ required: true }}
            render={({ field }) => (
              <SelectRoot 
                collection={pluginCollection}
                value={field.value ? [field.value] : []}
                onValueChange={(e) => field.onChange(e.value[0])}
                disabled={!!initialValues}
              >
                <SelectTrigger>
                  <SelectValueText placeholder="Select a plugin..." />
                </SelectTrigger>
                <SelectContent>
                  {pluginCollection.items.map((plugin) => (
                    <SelectItem item={plugin} key={plugin.value}>
                      {plugin.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </SelectRoot>
            )}
          />
        </Field>

        {selectedPlugin && (
          <Box border="1px solid" borderColor="gray.200" p={4} borderRadius="md" bg="gray.50">
            <Text fontWeight="bold" mb={3}>Configuration ({selectedPlugin.name})</Text>
            <Stack gap={3}>
              {/* Dynamic Form Generation based on Schema */}
              {Object.entries(selectedPlugin.schema.properties || {}).map(([key, prop]: [string, any]) => (
                <Field key={key} label={prop.title || key} helperText={prop.description}>
                  
                  {prop.type === "string" && !prop.enum && (
                    <Input 
                        {...register(`config.${key}`, { required: selectedPlugin.schema.required?.includes(key) })}
                        placeholder={prop.default?.toString()}
                    />
                  )}
                  
                  {prop.type === "integer" && (
                    <Input 
                        type="number"
                        {...register(`config.${key}`, { 
                            required: selectedPlugin.schema.required?.includes(key),
                            valueAsNumber: true 
                        })}
                        placeholder={prop.default?.toString()}
                    />
                  )}

                  {prop.enum && (
                    <Controller
                        control={control}
                        name={`config.${key}`}
                        render={({ field }) => (
                            <SelectRoot
                                onValueChange={(e) => field.onChange(e.value[0])}
                                value={field.value ? [field.value] : []}
                                collection={createListCollection({items: prop.enum.map((e: string) => ({label: e, value: e}))})}
                            >
                                <SelectTrigger>
                                  <SelectValueText placeholder={`Select ${key}`} />
                                </SelectTrigger>
                                <SelectContent>
                                    {prop.enum.map((opt: string) => (
                                        <SelectItem item={opt} key={opt}>{opt}</SelectItem>
                                    ))}
                                </SelectContent>
                            </SelectRoot>
                        )}
                    />
                  )}
                  
                  {prop.type === "array" && (
                    <Input
                        {...register(`config.${key}`)} 
                         placeholder="Comma separated values"
                         // Simple handling for array input - ideally split by comma
                    />
                  )}
                  
                </Field>
              ))}
            </Stack>
          </Box>
        )}

        <Flex justify="flex-end" gap={3} mt={4}>
          <Button variant="outline" onClick={onCancel}>Cancel</Button>
          <Button type="submit" loading={createInstance.isPending || updateInstance.isPending}>
            {initialValues ? "Update Collector" : "Create Collector"}
          </Button>
        </Flex>
      </Stack>
    </form>
  )
}
