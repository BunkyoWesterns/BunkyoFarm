import { attacksQuery, exploitsSourcesQuery, useClientSolver, useExtendedExploitSolver, useGroupSolver, useTeamSolver } from "@/utils/queries";
import { useGlobalStore } from "@/utils/stores";
import { Alert, Box, Modal, ScrollArea, Space, Title } from "@mantine/core"
import { showNotification } from "@mantine/notifications";
import { Fragment, useEffect, useRef } from "react";
import { FaUser } from "react-icons/fa";
import { ImTarget } from "react-icons/im";
import { FaBomb } from "react-icons/fa";
import { attackStatusTable } from "@/components/elements/StatusIcon";
import { FaFlag } from "react-icons/fa";
import { MdTimer } from "react-icons/md";
import { getDateFormatted, secondDurationToString } from "@/utils/time";
import { MdTimerOff } from "react-icons/md";
import { FaPersonRunning } from "react-icons/fa6";
import { calcAttackDuration } from "@/utils";
import { BsCardText } from "react-icons/bs";
import { ExploitSourceCard } from "../elements/ExploitSourceCard";

export const AttackExecutionDetailsModal = (props:{ opened:boolean, close:()=>void, attackId:number }) => {

    if (!props.opened) return null

    const attackQuery = attacksQuery(1, { id: props.attackId })
    const attack = attackQuery.data?.items[0]??null
    const sourceQuery = exploitsSourcesQuery(attack?.exploit??undefined)
    const usedSource = sourceQuery.data?.find((src) => src.id == attack?.exploit_source)??null
    const isUsedSourceLatest = sourceQuery.data?.length??0 > 0 ? sourceQuery.data?.[0]?.id == usedSource?.id : false
    const setLoading = useGlobalStore((store) => store.setLoader)
    const clientSolver = useClientSolver()
    const groupSolver = useGroupSolver()
    const teamSolver = useTeamSolver()
    const extendedExploitSolver = useExtendedExploitSolver()
    const scollRef = useRef<any>()

    useEffect(() => {
        if (attackQuery.isError){
            showNotification({ title: "Error", message: "Failed to fetch attack details", color: "red" })
            setLoading(false)
        }else if (attackQuery.isSuccess && attack != null){
            setLoading(false)
        }else{
            setLoading(true)
        }
    }, [attackQuery.isLoading, attack])
    const StatusIcon = attack?attackStatusTable[attack.status].icon:Fragment
    const executionTime = attack?calcAttackDuration(attack):null
    const boxWidth = 180

    return <Modal opened={props.opened} onClose={props.close} title={<Title order={3}>Attack no. {props.attackId} 🚩</Title>} size="xl" centered>
        {attack?<Box>
            <Box display="flex">
                <Box display="flex" style={{alignItems: "center", width: boxWidth}}><FaUser /><Space w="xs" />Executed by<Space w="xs" /></Box>
                <b>{clientSolver(attack.executed_by)}</b>
            </Box>
            {attack.executed_by_group?<Box display="flex">
                <Box display="flex" style={{alignItems: "center", width: boxWidth}}><FaUser /><Space w="xs" />Executed by group<Space w="xs" /></Box>
                <b>{groupSolver(attack.executed_by_group)}</b>
            </Box>:null

            }
            <Box display="flex">
                <Box display="flex" style={{alignItems: "center", width: boxWidth}}><ImTarget /><Space w="xs" />Target Team<Space w="xs" /></Box>
                <b>{teamSolver(attack.target)}</b>
            </Box>
            <Box display="flex">
                <Box display="flex" style={{alignItems: "center", width: boxWidth}}><FaBomb /><Space w="xs" />Exploit<Space w="xs" /></Box>
                <b>{extendedExploitSolver(attack.exploit)}</b>
            </Box>
            <Box display="flex">
                <Box display="flex" style={{alignItems: "center", width: boxWidth}}><StatusIcon /><Space w="xs" />Status<Space w="xs" /></Box>
                <b>{attackStatusTable[attack.status].name} ({attackStatusTable[attack.status].label})</b>
            </Box>
            <Box display="flex">
                <Box display="flex" style={{alignItems: "center", width: boxWidth}}><FaFlag /><Space w="xs" />Got flags<Space w="xs" /></Box>
                <b>{attack.flags.length}</b>
            </Box>
            <Box display="flex">
                <Box display="flex" style={{alignItems: "center", width: boxWidth}}><MdTimer /><Space w="xs" />Attack started at<Space w="xs" /></Box>
                <b>{attack.start_time?getDateFormatted(attack.start_time):"unknown"}</b>
            </Box>
            <Box display="flex">
                <Box display="flex" style={{alignItems: "center", width: boxWidth}}><MdTimerOff /><Space w="xs" />Attack ended at<Space w="xs" /></Box>
                <b>{attack.end_time?getDateFormatted(attack.end_time):"unknown"}</b>
            </Box>
            <Box display="flex">
                <Box display="flex" style={{alignItems: "center", width: boxWidth}}><FaPersonRunning /><Space w="xs" />Runned for<Space w="xs" /></Box>
                <b>{executionTime?secondDurationToString(executionTime):"unknown"}</b>
            </Box>
            <Space h="lg" ref={scollRef} />
            
            <Alert icon={<BsCardText />} title={<Title order={4}>Attack logs</Title>} color="gray" style={{width: "100%", height:"100%", display:"flex"}}>
                <ScrollArea.Autosize mah={400} >
                    <Box style={{whiteSpace:"pre"}} w={(scollRef.current?.getBoundingClientRect().width-60)+"px"}>
                        {attack.output?attack.output:<u>No logs found</u>}
                    </Box>
                </ScrollArea.Autosize> 
            </Alert>

            {usedSource?<ExploitSourceCard src={usedSource} latest={isUsedSourceLatest} viewOnly />:null}

        </Box>:null}
        
    </Modal>
}