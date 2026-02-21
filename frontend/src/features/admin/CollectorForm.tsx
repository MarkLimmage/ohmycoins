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
import { CollectorPlugin, CollectorCreate } from "./types"
import { useCollectors } from "./hooks"
import { SelectContent, SelectItem, SelectRoot, SelectTrigger, SelectValueText } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { Field } from "@/components/ui/field"

interface CollectorPluginFormProps {
  plugins: CollectorPlugin[]
  onCancel: () => void
  onSuccess: () => void
}

export const CollectorPluginForm = ({ plugins, onCancel, onSuccess }: CollectorPluginFormProps) => {
  const { createInstance } = useCollectors()
  const { register, handleSubmit, control, watch, reset } = useForm<CollectorCreate>()
  const selectedPluginId = watch("plugin_id")
  
  // Find selected plugin to render its schema
  const selectedPlugin = plugins.find(p => p.id === selectedPluginId)

  const onSubmit = (data: CollectorCreate) => {
    createInstance.mutate(data, {
      onSuccess: () => {
        reset()
        onSuccess()
      }
    })
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

                  {/* Handle Boolean */}
                  {prop.type === "boolean" && (
                    <Controller
                        control={control}
                        name={`config.${key}`}
                        defaultValue={prop.default}
                        render={({ field: { value, onChange, ...field } }) => (
                            <Checkbox 
                                checked={!!value} 
                                onCheckedChange={(e) => onChange(!!e.checked)}
                                {...field}
                            >
                                {prop.title || key}
                            </Checkbox>
                        )}
                    />
                  )}

                  {/* Handle Enum Selection */}
                  {prop.enum && (

                  {/* Handle Enum Selection */}
                  {prop.enum && (
                    <Controller
                        control={control}
                        name={`config.${key}`}
                        render={({ field }) => {
                          const collection = createListCollection({
                            items: prop.enum.map((e: string) => ({ label: e, value: e }))
                          })
                          return (
                            <SelectRoot
                                collection={collection}
                                value={field.value ? [field.value] : []}
                                onValueChange={(e) => field.onChange(e.value[0])}
                            >
                                <SelectTrigger>
                                  <SelectValueText placeholder={`Select ${prop.title || key}...`} />
                                </SelectTrigger>
                                <SelectContent>
                                    {collection.items.map((opt: any) => (
                                        <SelectItem item={opt} key={opt.value}>
                                          {opt.label}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </SelectRoot>
                          )
                        }}
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
          <Button type="submit" loading={createInstance.isPending}>Create Collector</Button>
        </Flex>
      </Stack>
    </form>
  )
}
