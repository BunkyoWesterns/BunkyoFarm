import { components } from "@/utils/backend_types";
import { statusQuery, submittersQuery, testSubmitter } from "@/utils/queries";
import { Alert, Box, Button, Group, Loader, Modal, ScrollArea, Space, Table, Text, Textarea, Title } from "@mantine/core"
import { useForm } from "@mantine/form";
import { notifications } from "@mantine/notifications";
import { useEffect, useRef, useState } from "react";
import { BsCardText } from "react-icons/bs";
import { FlagStatusIcon } from "../elements/StatusIcon";


export const TestSubmissionModal = ({ opened, close, submitterId }:{
    opened:boolean,
    close:()=>void,
    submitterId: number
}) => {

    const status = statusQuery()
    const submitters = submittersQuery()
    const [currentState, setCurrentState] = useState<"input"|"loading"|"results">("input")
    const [apiResult, setApiResult] = useState<components["schemas"]["MessageResponse_Dict_str__Any__"]|undefined>()
    const currentSubmitter = submitters.data?.find(exp => exp.id == submitterId)
    const scrollExternalRef = useRef<any>()

    const inizialize = () => {
        setCurrentState("input")
        setApiResult(undefined)
        form.reset()
    }

    useEffect(inizialize, [opened, submitterId])

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

    const isResponseValid = Array.isArray(apiResult?.response?.results)
    const flagResponse = isResponseValid?apiResult?.response?.results:[]
    const flagRegex = status.data?.config?.FLAG_REGEX

    return <Modal opened={opened} onClose={()=>{
        if (currentState != "loading") close()
        else notifications.show({
            title: "Plase wait until loading is complete!",
            message: "The request has not been terminated yet",
            color: "orange"
        })
    }} title={`Try the '${currentSubmitter?.name??submitterId}' submitter 🚩`} size="xl" centered>
        
        <form onSubmit={form.onSubmit((data) => {
            setCurrentState("loading")
            testSubmitter(submitterId, data.output).then((res) => {
                setApiResult(res)
            }).catch((err) => {
                setApiResult(err)
            }).finally(()=>{
                setCurrentState("results")
            })
        })}>
            {
                currentState == "input"?<Box>
                    Notes:
                    <ol>
                        <li>The test will use the selected submitter to send the flags below</li>
                        <li>Flags inserted here are not filtered or included in the statistics</li>
                        <li>The test don't intercept the normal behaviour of the submitter cycle</li>
                    </ol>
                    <Textarea
                        label="Insert here some text with the flags to submit here"
                        description={flagRegex?`The flags will be filtered using the regex: ${flagRegex}`:"Regex not set! Please insert only 1 flag"}
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
                        <Button onClick={close} color="red">Close</Button>
                        <Button type="submit" color="blue" disabled={!form.isValid()}>Submit</Button>
                    </Group>
                </Box>:
                currentState == "loading"?<Box className="center-flex-col">
                    <Space h="lg" />
                    <Text size="sm">Your test is running (sometime test can fail due to http timeout, but the submitter can be still valid)</Text>
                    <Space h="lg" />
                    <Loader />
                    <Space h="lg" />
                </Box>:
                currentState == "results"?<Box>
                    {
                        apiResult?.status == "ok"?<Box>
                            {
                                apiResult.response?.ok?<Box>
                                    <Title order={3}>Submission done correctly</Title>
                                    <Space h="lg" ref={scrollExternalRef}/>
                                    {!isResponseValid?<u>The response recived is not a list</u>:null}
                                    {isResponseValid && flagResponse?.length == 0?<u>No flags in the list returned by the submitter</u>:null}
                                    {isResponseValid && (flagResponse?.length??0) > 0?
                                    <ScrollArea><Table>
                                        <Table.Thead>
                                        <Table.Tr>
                                            <Table.Th>Status</Table.Th>
                                            <Table.Th>Flag</Table.Th>
                                            <Table.Th>Message</Table.Th>
                                        </Table.Tr>
                                        </Table.Thead>
                                        <Table.Tbody>
                                            {flagResponse?.map((ele)=>
                                                <Table.Tr key={ele[0]}>
                                                    <Table.Td><FlagStatusIcon status={ele[1]} /></Table.Td>
                                                    <Table.Td>{ele[0]}</Table.Td>
                                                    <Table.Td>{ele[2]}</Table.Td>
                                                </Table.Tr>
                                            )}
                                        </Table.Tbody>
                                    </Table></ScrollArea>:null}
                                    <Space h="lg" />
                                    <Alert icon={<BsCardText />} title={<Title order={4}>Output from submitter {apiResult?.response?.warning?"(some warning has been generated!)":""}</Title>} color={apiResult?.response?.warning?"yellow":"gray"} style={{width: "100%", height:"100%", display:"flex"}}>
                                        <ScrollArea.Autosize mah={400}>
                                            <Box style={{whiteSpace:"pre"}} w={(scrollExternalRef.current?.getBoundingClientRect().width-60)+"px"}>
                                                {(apiResult.response?.output??"" == "")?apiResult.response?.output:<u>No output recieved from submitter</u>}
                                            </Box>
                                        </ScrollArea.Autosize> 
                                    </Alert>
                                    
                                </Box>:
                                <Box>
                                    <Title order={3}>The submitter gave an error in the submission</Title>
                                    <Space h="lg" ref={scrollExternalRef}/>
                                    <Alert icon={<BsCardText />} title={<Title order={4}>{apiResult.response?.error??"No error message recieved"}</Title>} color="red" style={{width: "100%", height:"100%", display:"flex"}}>
                                        <ScrollArea.Autosize mah={400}>
                                            <Box style={{whiteSpace:"pre"}} w={(scrollExternalRef.current?.getBoundingClientRect().width-60)+"px"}>
                                                {apiResult.response?.output??<u>No output recieved from submitter</u>}
                                            </Box>
                                        </ScrollArea.Autosize> 
                                    </Alert>
                                </Box>
                            }
                        </Box>:<Box>
                            <Title order={2}>
                                Something went wrong in the request :/
                            </Title>
                            <Text>

                            </Text>
                        </Box>

                    }
                    
                    <Group justify="flex-end" mt="lg">
                        <Button color="red" onClick={close}>
                            Close
                        </Button>
                        <Button color="blue" onClick={inizialize}>
                            Re-try
                        </Button>
                    </Group>
                </Box>:null
            }

        </form>
    </Modal>
}