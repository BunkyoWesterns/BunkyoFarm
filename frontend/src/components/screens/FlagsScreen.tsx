import { flagsQuery, statsQuery, useClientSolver, useExploitSolver, useServiceSolverByExploitId, useTeamMapping, useTeamSolver } from "@/utils/queries";
import { Alert, Box, Button, Divider, Loader, MantineStyleProp, Modal, Pagination, ScrollArea, Space, Table, Title } from "@mantine/core";
import { useMemo, useRef, useState } from "react";
import { DonutChart } from '@mantine/charts';
import { FaKeyboard } from "react-icons/fa";
import { TbReload } from "react-icons/tb";
import { useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import { FlagStatusIcon } from "@/components/elements/StatusIcon";
import { getDateFormatted, secondDurationToString } from "@/utils/time";
import { ManualSubmissionModal } from "@/components/modals/ManualSubmissionModal";
import { FlagStatusType, LineChartFlagView } from "@/components/charts/LineChartFlagView";
import { useSessionStorage } from "@mantine/hooks";
import { TeamSelector } from "@/components/inputs/TeamSelector";
import { FlagTypeControl } from "@/components/inputs/Controllers";
import { ExploitBar } from "@/components/elements/ExploitsBar";
import { AttackExecutionDetailsModal } from "@/components/modals/AttackExecutionDetailModal";
import { HiCursorClick } from "react-icons/hi";
import { FaInfoCircle } from "react-icons/fa";
import { calcAttackDuration } from "@/utils";
import { BsCardText } from "react-icons/bs";

export const FlagsScreen = () => {

    const [page, setPage] = useState<number>(1)
    const queryClient = useQueryClient()
    const getTeamName = useTeamSolver()
    const teamMapping = useTeamMapping()
    const getServiceName = useServiceSolverByExploitId()
    const getExploitName = useExploitSolver()
    const getClientName = useClientSolver()
    const [manualSubmissionModal, setManualSubmissionModal] = useState<boolean>(false)
    const [viewStatusText, setViewStatusText] = useState<string|undefined>()
    const scrollRef = useRef<any>()

    const [attackDetailId, setAttackDetailId] = useState<number|null>(null)

    const [flagStatusFilter, setFlagStatusFilterChart] = useSessionStorage<FlagStatusType>({ key: "flagStatusFilter", defaultValue: "tot" })
    const [flagTargetFilter, setFlagTargetFilter] = useSessionStorage<number>({ key: "flagTargetFilter", defaultValue: -1 })

    const flagsStats = statsQuery()
    const flags = flagsQuery(page, {
        flag_status: flagStatusFilter=="tot"?undefined:flagStatusFilter,
        target: flagTargetFilter==-1?undefined:flagTargetFilter,
    })
    const totFlags = flagsStats.data?.globals.flags.tot??0
    const totalPages = flags.data?.pages??0
    const isEmpty = flags.data?.items.length==0
    const thStyle: MantineStyleProp = { fontWeight: "bolder", fontSize: "130%", textTransform: "uppercase" }
    const submitterTextLimit = 130
    
    const tableData = useMemo(() => {
        return (flags.data?.items??[]).map((item) => {
            const executionTime = calcAttackDuration(item.attack)
            return <Table.Tr key={item.id}>
                <Table.Td><Box>{item.id}</Box></Table.Td>
                <Table.Td><Box style={{fontWeight: "bolder"}}>{item.flag}</Box></Table.Td>
                <Table.Td><Box><Box style={{fontWeight: "bolder"}}>{getServiceName(item.attack.exploit)}</Box>using {getExploitName(item.attack.exploit)} exploit</Box></Table.Td>
                <Table.Td><Box><span style={{fontWeight: "bolder"}}>{getTeamName(item.attack.target)}</span><br />{item.attack.target?teamMapping[item.attack.target]?.host:null}</Box></Table.Td>
                <Table.Td>
                    <Box display="flex">
                        <Box>time: {executionTime?secondDurationToString(executionTime):"unknown execution time"}<br />by {getClientName(item.attack.executed_by)}</Box>
                        <Space w="xs" />
                        <FaInfoCircle onClick={()=>setAttackDetailId(item.attack.id)} style={{marginTop: 4, cursor:"pointer"}}/>
                    </Box>
                </Table.Td>
                <Table.Td>
                    <Box display="flex">
                        <Box>
                            {item.status_text?.slice(0,submitterTextLimit)??"No response from submitter"}{(item.status_text?.length??0)>submitterTextLimit?<> <u>[...]</u></>:null} 
                            <br />Submitted At: {item.last_submission_at?getDateFormatted(item.last_submission_at):"never"}
                        </Box>
                        <Space w="xs" />
                        <FaInfoCircle onClick={()=>setViewStatusText(item.status_text??"No response from submitter")} style={{marginTop: 4, cursor:"pointer"}}/>
                        {/* item.submit_attempts + item.last_submission_at -> Status include number of tries if != 1 and last submission if failed */}
                    </Box>
                </Table.Td>
                <Table.Td><FlagStatusIcon status={item.status} /></Table.Td>
            </Table.Tr>
        })
    }, [flags.isFetching, page, flagStatusFilter, flagTargetFilter])

    const flags_tot_stats = {
        ok: flagsStats.data?.globals.flags.ok??0,
        timeout: flagsStats.data?.globals.flags.timeout??0,
        invalid: flagsStats.data?.globals.flags.invalid??0,
        wait: flagsStats.data?.globals.flags.wait??0
    }

    return <Box style={{
        width: "100%",
    }}>
        <ExploitBar />
        <LineChartFlagView withControls/>
        <Space h="xl" hiddenFrom="md" />
        <Box className="center-flex-col">
            <Box className="center-flex" style={{width:"100%", flexWrap: "wrap" }}>
                <Pagination total={totalPages} color="red" radius="md" value={page} onChange={setPage} />
                <Box hiddenFrom="md" style={{flexBasis: "100%", height:30}} />
                <Space w="lg" visibleFrom="md"/>
                <Box className="center-flex">
                    <Button
                        leftSection={<FaKeyboard size={20} />}
                        variant="gradient"
                        gradient={{ from: 'red', to: 'grape', deg: 90 }}
                        onClick={() => setManualSubmissionModal(true)}
                    >
                        Manual Submission
                    </Button>
                    <Space w="md" />
                    <Button
                        leftSection={<TbReload size={20} />}
                        variant="gradient"
                        gradient={{ from: 'blue', to: 'teal', deg: 90 }}
                        onClick={() => {
                            queryClient.invalidateQueries({ queryKey:["flags"] })
                            notifications.show({
                                title: "Fresh data arrived 🌱",
                                message: "Flag data has been refreshed!",
                                color: "green",
                                autoClose: 3000
                            })
                        }}
                        loading={flags.isFetching}
                    >
                        Refresh
                    </Button>
                </Box>
                
                <Box hiddenFrom="md" style={{flexBasis: "100%", height:20}} />
                <Box style={{flex:1, flexGrow:1}} visibleFrom="md"/>

                <Box className="center-flex-col">
                    <Space visibleFrom="md" h="lg" />
                    <DonutChart
                        data={totFlags>0?[
                            { value: flags_tot_stats.ok, color: 'lime', name: "Accepted" },
                            { value: flags_tot_stats.timeout, color: 'yellow', name: "Expired" },
                            { value: flags_tot_stats.invalid, color: 'red', name: "Rejected"},
                            { value: flags_tot_stats.wait, color: 'indigo', name: "Queued"},
                        ]:[
                            { value: 1, color: 'gray', name: "No flags" },
                        ]}
                        
                        startAngle={0}
                        endAngle={180}
                        paddingAngle={1}
                        size={160}
                        thickness={35}
                        withTooltip={totFlags>0}
                        tooltipDataSource="all"
                        mx="auto"
                        withLabelsLine
                        withLabels={totFlags>0}
                        style={{ marginBottom: -75 }}
                        chartLabel={totFlags>0?`${totFlags} Flags`:"No flags"}
                    />
                </Box>
            </Box>
            <Box style={{width:"100%"}} >
                <b>Table Filters</b>
                <Space h="md" />
                <Divider />
                <Space h="md" />
                <Box className="center-flex" style={{width: "100%", flexWrap:"wrap"}}>
                    <Box style={{marginBottom:-15}}>
                        <Space h="lg" hiddenFrom="md" />
                        <FlagTypeControl value={flagStatusFilter} onChange={setFlagStatusFilterChart} />
                        <Space h="lg" hiddenFrom="md" /><br />
                        <small>Total results: {flags.data?.total}</small>
                    </Box>
                    <Box visibleFrom="md" style={{flexGrow: 1}} />
                    <Box hiddenFrom="md" style={{flexBasis: "100%", height: 20}} />
                    <TeamSelector onChange={(target)=>setFlagTargetFilter((target==undefined)?-1:target)} label="TEAM"/>    
                </Box>
                <Space h="lg" hiddenFrom="md" />
                <Space h="md" />
            </Box>
            <Space h="md" />
            <ScrollArea style={{zIndex:1}} h="100%" w="100%">
                <Table>
                    <Table.Thead>
                        <Table.Tr>
                            <Table.Th style={thStyle}>ID</Table.Th>
                            <Table.Th style={thStyle}>Flag</Table.Th>
                            <Table.Th style={thStyle}>Service</Table.Th>
                            <Table.Th style={thStyle}>Team</Table.Th>
                            <Table.Th style={thStyle}><Box display="flex" style={{alignItems: "center"}}>Execution<Space w="sm" /><HiCursorClick /></Box></Table.Th>
                            <Table.Th style={thStyle}><Box display="flex" style={{alignItems: "center"}}>response<Space w="sm" /><HiCursorClick /></Box></Table.Th>
                            <Table.Th style={thStyle} className="center-flex">Status</Table.Th>
                        </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>{tableData}</Table.Tbody>
                </Table>
                <Space h="md" />
                <Box className="center-flex">{flags.isLoading?<Loader />:null}</Box>
                {isEmpty?<Box className="center-flex">No flags found :{"("}</Box>:null}
            </ScrollArea>
            <Space h="xl" />
            <Pagination total={totalPages} color="red" radius="md" value={page} onChange={setPage} />
        </Box>
        <Space h="xl" /><Space h="xl" />
        <ManualSubmissionModal opened={manualSubmissionModal} close={() => setManualSubmissionModal(false)} />
        {attackDetailId==null?null:<AttackExecutionDetailsModal opened={true} close={()=>setAttackDetailId(null)} attackId={attackDetailId} />}
        <Modal size="xl" opened={viewStatusText!=undefined} onClose={()=>setViewStatusText(undefined)} title="Submission status text" centered>
            <Space w="md" />
            <Alert ref={scrollRef} icon={<BsCardText />} title={<Title order={4}>Submitter logs</Title>} color="gray" style={{width: "100%", height:"100%", display:"flex"}}>
                <ScrollArea.Autosize mah={400} >
                    <Box style={{whiteSpace:"pre"}} w={(scrollRef.current?.getBoundingClientRect().width-70)+"px"}>
                        {viewStatusText}
                    </Box>
                </ScrollArea.Autosize> 
            </Alert>
        </Modal>
    </Box>
}