import { editGroup } from "@/utils/queries"
import { AttackGroup } from "@/utils/types"
import { Button, Group, Modal, TextInput } from "@mantine/core"
import { useForm } from "@mantine/form"
import { notifications } from "@mantine/notifications"
import { useQueryClient } from "@tanstack/react-query"
import { useEffect } from "react"


export const EditGroupModal = ({ onClose, group }:{ onClose: ()=>void, group?:AttackGroup }) => {
    const form = useForm({
        initialValues: {
            name: group?.name??"",
        },
        validate: {
            name: (value) => value == ""?"Name is required":undefined
        }
    })

    const queryClient = useQueryClient()

    useEffect(() => {
        form.setInitialValues({
            name: group?.name??""
        })
        form.reset()
    }, [group])

    return <Modal
        opened={ group != null }
        onClose={onClose}
        title="Edit group"
        size="xl"
        centered
    >
        <form onSubmit={form.onSubmit((data) => {
            if (group == null){
                onClose()
                return
            }
            editGroup(group.id, data)
            .then(()=>{
                notifications.show({
                    title: `${group.name} Group edited!`,
                    message: "Group has been edited successfully!",
                    color: "green",
                })
                queryClient.invalidateQueries({ queryKey: ["groups"] })
            }).catch((err) => {
                notifications.show({
                    title: "Error during editing!",
                    message: err.message??err??"Unknown error",
                    color: "red",
                })
            }).finally(()=>{ onClose() })
        })}>
            <TextInput
                label="Name"
                placeholder="Group name"
                withAsterisk
                {...form.getInputProps("name")}
            />
            <Group mt="xl" justify="flex-end">
                <Button onClick={form.reset} color="gray" disabled={!form.isDirty()}>Reset</Button>
                <Button type="submit" color="blue" disabled={!form.isValid() || !form.isDirty()}>Edit</Button>
            </Group>
        </form>

    </Modal>
}