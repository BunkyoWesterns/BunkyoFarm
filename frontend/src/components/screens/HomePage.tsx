import { statusQuery } from "@/utils/queries";
import { Alert, Box, Modal, Progress, ScrollArea, Space, Tabs, Text } from "@mantine/core";
import { Fragment, useEffect, useRef, useState } from "react";
import { MdErrorOutline } from "react-icons/md";
import { AiOutlineInfoCircle } from "react-icons/ai";
import { AiOutlineWarning } from "react-icons/ai";
import { IoFlagSharp } from "react-icons/io5";
import { FlagsScreen } from "@/components/screens/FlagsScreen";
import { PiSwordBold } from "react-icons/pi";
import { MdGroups } from "react-icons/md";
import { useNavigate, useParams } from "react-router";
import { secondDurationToString } from "@/utils/time";
import { AttackScreen } from "@/components/screens/AttackScreen";
import { TeamsScreen } from "@/components/screens/TeamsScreen";
import { MainLayout } from "@/components/MainLayout";
import { useGetTick } from "@/utils";
import { ImInfo } from "react-icons/im";

export const HomePage = () => {
    const { page } = useParams()
    const navigate = useNavigate()
    const status = statusQuery()
    const scrollExternalRef = useRef<any>()
    const [messagesModal, setMessagesModal] = useState(false)
    const { nextTickIn, tickDuration, gameEnded, isSuccess:tickInfoValid, gameStarted } = useGetTick()

    const messages = (status.data?.messages??[]).map((msg, i) => {
        const lvl = msg.level??"warning"
        const title = msg.title??"Unknown message"
        const message = msg.message??"No message"
        const color = (lvl=="error")?"red":(lvl=="warning")?"yellow":"green"
        const icon = (lvl=="error")?<MdErrorOutline />:(lvl=="warning")?<AiOutlineWarning />:<AiOutlineInfoCircle />
        return <Fragment key={i}>
            <Space h="lg" />
            <Alert ref={scrollExternalRef} icon={icon} title={title} color={color} style={{width: "100%", height:"100%", display:"flex"}}>
                <ScrollArea.Autosize mah={200}>
                    <Box style={{whiteSpace:"pre"}} w={(scrollExternalRef.current?.getBoundingClientRect().width-70)+"px"}>
                        {message}
                    </Box>
                </ScrollArea.Autosize> 
            </Alert>
        </Fragment>
    })

    useEffect(() => {
        if (page == undefined || !["flags", "attacks", "teams"].includes(page)){
            navigate("/flags")
        }
    }, [page])

    const onTabChange = (page:string|null) => {
        navigate("/"+page)
    }

    return <MainLayout>
        <Box style={{width: "100%",}}>
            {(messages.length > 0) && (!gameEnded || !tickInfoValid)?messages:null}
            <Space h="lg" />
            {nextTickIn==Infinity?"Waiting for the first attack":
            gameEnded?"Game ended! 👾":<>
                Next tick in: {!gameStarted?"Not started yet :(":`${secondDurationToString(parseInt(nextTickIn.toFixed(0)))}`}
            </>}
            <Progress color={!gameEnded?"red":"lime"} radius="md" size="xl" value={gameEnded?100:(nextTickIn/tickDuration)*100} striped={!gameEnded} animated={!gameEnded} />
            {(messages.length > 0) && gameEnded && tickInfoValid?<Box display="flex" style={{alignItems:"center", cursor: "pointer"}} onClick={()=>setMessagesModal(true)}>
                <Space h="lg" /><ImInfo size={10} /><Text size="sm" ml={4}>Click here to see hidden messages</Text>
            </Box>:null}
            <Space h="lg" />
            <Tabs variant="pills" radius="xl" orientation="horizontal" defaultValue="gallery" value={page} onChange={onTabChange} >
                <Tabs.List>
                    <Tabs.Tab value="flags" leftSection={<IoFlagSharp />} color="red"> Flags </Tabs.Tab>
                    <Tabs.Tab value="attacks" leftSection={<PiSwordBold />} color="green"> Attacks </Tabs.Tab>
                    <Tabs.Tab value="teams" leftSection={<MdGroups />}> Teams </Tabs.Tab>

                </Tabs.List>
                <Space h="md" />
            </Tabs>
            {
                page == "flags"?<FlagsScreen />:
                page == "attacks"?<AttackScreen />:
                page == "teams"?<TeamsScreen />:"Unknown page"
            }
            <Space h="xl" />
            <Space h="xl" />
        </Box>
        <Modal opened={messagesModal} onClose={()=>setMessagesModal(false)} title="Hidden messages" size="xl" centered>
            <Box>
                {messages}
            </Box>
        </Modal>
    </MainLayout>
}