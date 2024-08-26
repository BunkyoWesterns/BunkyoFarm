import { commitManualSubmission, statusQuery } from "@/utils/queries";
import { Button, Group, Modal, Space, Textarea } from "@mantine/core"
import { useForm } from "@mantine/form";
import { notifications } from "@mantine/notifications";
import { useEffect } from "react";


export const ManualSubmissionModal = (props:{
    opened:boolean,
    close:()=>void
}) => {

    const status = statusQuery()

    const form = useForm({
        mode: 'uncontrolled',
        initialValues: {
            output: '',
        },

        validate: {
            output: (val) => {
                if (val == "") return 'Output is required';
            }
        },
    });

    const flagRegex = status.data?.config?.FLAG_REGEX??'Unknown'

    useEffect(() => {
        form.reset()
    },[props.opened])

    return <Modal opened={props.opened} onClose={props.close} title="Manual flag submission 🚩" size="xl" centered>
        
        <form onSubmit={form.onSubmit((data) => {
            commitManualSubmission(data.output).then((res) => {
                if (res.status == "ok"){
                    props.close()
                    notifications.show({
                        title: `Found ${res?.response?.flags??0} flags!`,
                        message: `${res?.response?.flags??0} flags has been queued for submission!`,
                        color: "green",
                        autoClose: 5000
                    })
                }
            }).catch((err) => {
                notifications.show({
                    title: "Error during submission!",
                    message: err.message??err??"Unknown error",
                    color: "red",
                    autoClose: 5000
                })
            })
        })}>
            <Textarea
                label="Insert here some text with the flags to submit here"
                description={`The flags will be filtered using the regex ${flagRegex}`}
                placeholder="<html> ... FLAGABC123= ... </html>"
                {...form.getInputProps("output")}
                withAsterisk
                styles={{
                    input: {
                        minHeight: 200
                    }
                }}
            />
            <Space h="lg" />
            <Group justify="flex-end">
                <Button onClick={props.close} color="red">Close</Button>
                <Button type="submit" color="blue" disabled={!form.isValid()}>Submit</Button>
            </Group>
        </form>
    </Modal>
}