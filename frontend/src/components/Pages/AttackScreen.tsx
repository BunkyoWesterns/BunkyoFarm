import { attacksQuery, statsQuery as statsQuery, useClientSolver, useExploitSolver, useServiceSolverByExploitId, useTeamMapping, useTeamSolver } from "@/utils/queries";
import { Box, Button, Divider, Loader, MantineStyleProp, Pagination, ScrollArea, Space, Table } from "@mantine/core";
import { useMemo, useState } from "react";
import { DonutChart } from '@mantine/charts';
import { TbReload } from "react-icons/tb";
import { useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import { AttackStatusIcon } from "@/components/StatusIcon";
import { secondDurationToString } from "@/utils/time";
import { useSessionStorage } from "@mantine/hooks";
import { TeamSelector } from "../TeamSelector";
import { AttackTypeControl } from "../Controllers";
import { AttackStatusType, LineChartAttackView } from "../LineChartAttackView";
import { ExploitBar } from "../ExploitsBar";
import { calcAttackDuration } from "@/utils";
import { FaInfoCircle } from "react-icons/fa";
import { AttackExecutionDetailsModal } from "../AttackExecutionDetailModal";
import { HiCursorClick } from "react-icons/hi";

export const AttackScreen = () => {

    const [page, setPage] = useState<number>(1)
    const queryClient = useQueryClient()
    const getTeamName = useTeamSolver()
    const getServiceName = useServiceSolverByExploitId()
    const getExploitName = useExploitSolver()
    const teamMapping = useTeamMapping()
    const getClientName = useClientSolver()
    const errorTextLimit = 60

    const [attackDetailId, setAttackDetailId] = useState<number|null>(null)

    const [attackStatusFilter, setAttackStatusFilterChart] = useSessionStorage<AttackStatusType>({ key: "attackStatusFilter", defaultValue: "tot" })
    const [attackTargetFilter, setAttackTargetFilter] = useSessionStorage<number>({ key: "attackTargetFilter", defaultValue: -1 })

    const attacksStats = statsQuery()
    const attacks = attacksQuery(page, {
        status: attackStatusFilter=="tot"?undefined:attackStatusFilter,
        target: attackTargetFilter==-1?undefined:attackTargetFilter,
    })
    const totAttacks = attacksStats.data?.globals.attacks.tot??0
    const totalPages = attacks.data?.pages??0
    const isEmpty = attacks.data?.items.length==0
    const thStyle: MantineStyleProp = { fontWeight: "bolder", fontSize: "130%", textTransform: "uppercase" }

    const tableData = useMemo(() => {
        return (attacks.data?.items??[]).map((item) => {
            const executionTime = calcAttackDuration(item)
            return <Table.Tr key={item.id}>
                <Table.Td>
                    <Box display="flex" onClick={()=>setAttackDetailId(item.id)} style={{cursor:"pointer"}}>
                        <FaInfoCircle style={{marginTop: 4}}/>
                        <Space w="xs" />
                        <Box>{item.id}</Box>
                    </Box>
                </Table.Td>
                <Table.Td><Box style={{fontWeight: "bolder"}}>{getServiceName(item.exploit)}</Box>using {getExploitName(item.exploit)} exploit</Table.Td>
                <Table.Td><span style={{fontWeight: "bolder"}}>{getTeamName(item.target)}</span><br />{item.target?teamMapping[item.target].host:null}</Table.Td>
                <Table.Td>
                    time: {executionTime?secondDurationToString(executionTime):"unknown execution time"}<br />by {getClientName(item.executed_by)}
                </Table.Td>
                <Table.Td>{item.error?.slice(0,errorTextLimit)??"No errors"}{item.error?.length??0>errorTextLimit?<> <u>[...]</u></>:null}<br />{item.flags.length} flags got</Table.Td>
                <Table.Td><AttackStatusIcon status={item.status} /></Table.Td>
            </Table.Tr>
        })
    }, [attacks.isFetching, page, attackStatusFilter, attackTargetFilter])

    const attack_tot_stats = {
        done: attacksStats.data?.globals.attacks.done??0,
        crashed: attacksStats.data?.globals.attacks.crashed??0,
        noflags: attacksStats.data?.globals.attacks.noflags??0,
    }

    return <Box style={{
        width: "100%",
    }}>

        <ExploitBar />
        <LineChartAttackView withControls/>
        <Space h="xl" hiddenFrom="md" />

        <Box className="center-flex-col">
            <Box className="center-flex" style={{width:"100%", flexWrap: "wrap" }}>
                <Pagination total={totalPages} color="red" radius="md" value={page} onChange={setPage} />
                <Box hiddenFrom="md" style={{flexBasis: "100%", height:30}} />
                <Space w="lg" visibleFrom="md"/>
                <Box className="center-flex">
                    <Button
                        leftSection={<TbReload size={20} />}
                        variant="gradient"
                        gradient={{ from: 'blue', to: 'teal', deg: 90 }}
                        onClick={() => {
                            queryClient.refetchQueries({ queryKey:["attacks"] })
                            notifications.show({
                                title: "Fresh data arrived 🌱",
                                message: "Attacks data has been refreshed!",
                                color: "green",
                                autoClose: 3000
                            })
                        }}
                        loading={attacks.isLoading}
                    >
                        Refresh
                    </Button>
                </Box>
                
                <Box hiddenFrom="md" style={{flexBasis: "100%", height:20}} />
                <Box style={{flex:1, flexGrow:1}} visibleFrom="md"/>

                <Box className="center-flex-col">
                    <Space visibleFrom="md" h="lg" />
                    <DonutChart
                        data={totAttacks>0?[
                            { value: attack_tot_stats.done, color: 'lime', name: "Completed" },
                            { value: attack_tot_stats.noflags, color: 'yellow', name: "No flags obtained" },
                            { value: attack_tot_stats.crashed, color: 'red', name: "Crashed"},
                        ]:[
                            { value: 1, color: 'gray', name: "No attacks" },
                        ]}
                        
                        startAngle={0}
                        endAngle={180}
                        paddingAngle={1}
                        size={160}
                        thickness={35}
                        withTooltip={totAttacks>0}
                        tooltipDataSource="all"
                        mx="auto"
                        withLabelsLine
                        withLabels={totAttacks>0}
                        style={{ marginBottom: -75 }}
                        chartLabel={totAttacks>0?`${totAttacks} Attacks`:"No attacks"}
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
                        <AttackTypeControl value={attackStatusFilter} onChange={setAttackStatusFilterChart} />
                        <Space h="lg" hiddenFrom="md" /><br />
                        <small>Total results: {attacks.data?.total}</small>
                    </Box>
                    <Box visibleFrom="md" style={{flexGrow: 1}} />
                    <Box hiddenFrom="md" style={{flexBasis: "100%", height: 20}} />
                    <TeamSelector onChange={(target)=>setAttackTargetFilter((target==undefined)?-1:target)} label="TEAM"/>    
                </Box>
                <Space h="lg" hiddenFrom="md" />
                <Space h="md" />
            </Box>
            <Space h="md" />
            <ScrollArea style={{zIndex:1}} h="100%" w="100%">
                <Table>
                    <Table.Thead>
                        <Table.Tr>
                            <Table.Th style={thStyle}><Box display="flex" style={{alignItems: "center"}}>ID<Space w="sm" /><HiCursorClick /></Box></Table.Th>
                            <Table.Th style={thStyle}>Service</Table.Th>
                            <Table.Th style={thStyle}>Team</Table.Th>
                            <Table.Th style={thStyle}>Execution</Table.Th>
                            <Table.Th style={thStyle}>Response</Table.Th>
                            <Table.Th style={thStyle} className="center-flex">Status</Table.Th>
                        </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>{tableData}</Table.Tbody>
                </Table>
                <Space h="md" />
                <Box className="center-flex">{attacks.isLoading?<Loader />:null}</Box>
                {isEmpty?<Box className="center-flex">No attacks found :{"("}</Box>:null}
            </ScrollArea>
            <Space h="xl" />
            <Pagination total={totalPages} color="red" radius="md" value={page} onChange={setPage} />
        </Box>
        <Space h="xl" /><Space h="xl" />
        {attackDetailId==null?null:<AttackExecutionDetailsModal opened={true} close={()=>setAttackDetailId(null)} attackId={attackDetailId} />}
    </Box>
}