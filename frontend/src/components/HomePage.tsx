import { statusQuery } from "@/utils/queries";
import { Alert, Box, ScrollArea, Space, Tabs } from "@mantine/core";
import { Fragment } from "react";
import { MdErrorOutline } from "react-icons/md";
import { AiOutlineInfoCircle } from "react-icons/ai";
import { AiOutlineWarning } from "react-icons/ai";
import { IoFlagSharp } from "react-icons/io5";
import { FlagsScreen } from "./Pages/FlagsScreen";
import { PiSwordBold } from "react-icons/pi";
import { MdGroups } from "react-icons/md";

export const HomePage = () => {

    const status = statusQuery()
    const messages = (status.data?.messages??[]).map((msg, i) => {
        const lvl = msg.level??"warning"
        const title = msg.title??"Unknown message"
        const message = msg.message??"No message"
        const color = (lvl=="error")?"red":(lvl=="warning")?"yellow":"green"
        const icon = (lvl=="error")?<MdErrorOutline />:(lvl=="warning")?<AiOutlineWarning />:<AiOutlineInfoCircle />
        return <Fragment key={i}>
            <Space h="lg" />
            <Alert icon={icon} title={title} color={color} style={{width: "100%", height:"100%"}}>
                <ScrollArea.Autosize mah={200}>
                    <pre>{message}</pre>
                </ScrollArea.Autosize> 
            </Alert>
        </Fragment>
    })

    return <Box style={{
        width: "100%",
    }}>
        {messages?<>{messages}<Space h="lg" /></>:null}
        <Tabs variant="pills" radius="xl" orientation="horizontal" defaultValue="gallery">
            <Tabs.List>
                <Tabs.Tab value="flags" leftSection={<IoFlagSharp />} color="red"> Flags </Tabs.Tab>
                <Tabs.Tab value="attacks" leftSection={<PiSwordBold />} color="green"> Attacks </Tabs.Tab>
                <Tabs.Tab value="teams" leftSection={<MdGroups />}> Teams </Tabs.Tab>

            </Tabs.List>
            <Space h="md" />
            <Tabs.Panel value="flags">
                <FlagsScreen />
            </Tabs.Panel>
            <Tabs.Panel value="attacks">
                TODO
            </Tabs.Panel>
            <Tabs.Panel value="teams">
                TODO
            </Tabs.Panel>
        </Tabs>
        <Space h="xl" />
        <Space h="xl" />
    </Box>
}