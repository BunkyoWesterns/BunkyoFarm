import { statusQuery } from "@/utils/queries";
import { Alert, Box, Progress, ScrollArea, Space, Tabs } from "@mantine/core";
import { Fragment, useEffect, useState } from "react";
import { MdErrorOutline } from "react-icons/md";
import { AiOutlineInfoCircle } from "react-icons/ai";
import { AiOutlineWarning } from "react-icons/ai";
import { IoFlagSharp } from "react-icons/io5";
import { FlagsScreen } from "./Pages/FlagsScreen";
import { PiSwordBold } from "react-icons/pi";
import { MdGroups } from "react-icons/md";
import { useNavigate, useParams } from "react-router";
import { useInterval } from "@mantine/hooks";
import { secondDurationToString } from "@/utils/time";

export const HomePage = () => {
    const { page } = useParams()
    const navigate = useNavigate()
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

    const [nextTickIn, setNextTickIn] = useState(Infinity)

    const nextTickTime = () => {
        const start = status.data?.start_time?new Date(status.data.start_time).getTime():null
        const end = status.data?.config?.END_TIME?new Date(status.data.config.END_TIME).getTime():null
        if (start == null) return Infinity
        const tick = status.data?.config?.TICK_DURATION
        if (tick == null) return Infinity
        const now = new Date().getTime()
        if (now < start) return -1
        const tickCalc = ((now-start)/1000)%tick
        if (end && now > end) return -2
        return tick-tickCalc
    }

    const tickTime = status.data?.config?.TICK_DURATION??1

    const interval = useInterval(() => {setNextTickIn(nextTickTime())}, 1000)

    useEffect(() => {
        interval.start()
        return () => interval.stop()
    }, [])

    useEffect(() => {
        if (page == undefined || !["flags", "attacks", "teams"].includes(page)){
            navigate("/flags")
        }
    }, [page])

    const onTabChange = (page:string|null) => {
        navigate("/"+page)
    }

    return <Box style={{
        width: "100%",
    }}>
        {messages?<>{messages}<Space h="lg" /></>:null}
        {nextTickIn==Infinity?"Waiting for the first attack":
        nextTickIn==-2?"Game ended! 👾":<>
            Next tick in: {nextTickIn == -1?"Not started yet :(":`${secondDurationToString(parseInt(nextTickIn.toFixed(0)))}`}
        </>}
        <Progress color={nextTickIn!=-2?"red":"lime"} radius="md" size="xl" value={nextTickIn==-2?100:(nextTickIn/tickTime)*100} striped={nextTickIn!=-2} animated={nextTickIn!=-2} />
        <Space h="lg" />
        <Tabs variant="pills" radius="xl" orientation="horizontal" defaultValue="gallery" value={page} onChange={onTabChange} >
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