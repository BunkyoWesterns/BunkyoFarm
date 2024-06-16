import { flagsQuery, flagsStatsQuery, statusQuery, useClientSolver, useExploitSolver, useServiceSolverByExploitId, useTeamSolver } from "@/utils/queries";
import { useSettingsStore } from "@/utils/stores";
import { Alert, Box, Button, Loader, MantineStyleProp, Pagination, ScrollArea, Space, Table } from "@mantine/core";
import { Fragment, useMemo, useState } from "react";
import { DonutChart } from '@mantine/charts';
import { FaKeyboard } from "react-icons/fa";
import { TbReload } from "react-icons/tb";
import { useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import { StatusIcon } from "./StatusIcon";
import { getDateFormatted, secondDurationToString } from "@/utils/time";
import { MdErrorOutline } from "react-icons/md";
import { AiOutlineInfoCircle } from "react-icons/ai";
import { AiOutlineWarning } from "react-icons/ai";
import { ManualSubmissionModal } from "./ManualSubmissionModal";
import { ChartView } from "./ChartView";

export const HomePage = () => {

    const [page, setPage] = useState<number>(1)
    const [bulkPageSize, tablePageSize] = useSettingsStore((state) => [state.pageSizeRequest, state.tablePageSize])
    const pagesForBulk = (bulkPageSize/tablePageSize)
    const bulkedPage = Math.ceil(page/pagesForBulk)
    const queryClient = useQueryClient()
    const getTeamName = useTeamSolver()
    const getServiceName = useServiceSolverByExploitId()
    const getExploitName = useExploitSolver()
    const getClientName = useClientSolver()
    const [manualSubmissionModal, setManualSubmissionModal] = useState<boolean>(false)

    const flagsStats = flagsStatsQuery()
    const status = statusQuery()
    const flags = flagsQuery(bulkedPage)
    const totFlags = flagsStats.data?.globals.flags.tot??0
    const totalPages = Math.ceil(totFlags/tablePageSize)
    const thStyle: MantineStyleProp = { fontWeight: "bolder", fontSize: "130%", textTransform: "uppercase" }

    const tableData = useMemo(() => {
        const offsetArray = ((page-1)%pagesForBulk)*tablePageSize
        
        return (flags.data?.items??[]).slice(offsetArray,offsetArray+tablePageSize).map((item) => {
            const executionTime = (item.attack.start_time && item.attack.end_time)?secondDurationToString((new Date(item.attack.end_time).getTime()-new Date(item.attack.start_time).getTime())/1000):"unknown execution time"
            return <Table.Tr key={item.id}>
                <Table.Td>{item.id}</Table.Td>
                <Table.Td><span style={{fontWeight: "bolder"}}>{item.flag}</span></Table.Td> {/* Insert click to attack execution details */}
                <Table.Td><Box style={{fontWeight: "bolder"}}>{getServiceName(item.attack.exploit)}</Box>using {getExploitName(item.attack.exploit)} exploit</Table.Td>
                <Table.Td><span style={{fontWeight: "bolder"}}>{getTeamName(item.attack.target)}</span></Table.Td>
                <Table.Td>time: {executionTime}<br />by {getClientName(item.attack.executed_by)}</Table.Td>
                <Table.Td>{item.status_text??"No response from submitter"}<br />Submitted At: {item.last_submission_at?getDateFormatted(item.last_submission_at):"never"}</Table.Td> {/* item.submit_attempts + item.last_submission_at -> Status include number of tries if != 1 and last submission if failed */}
                <Table.Td><StatusIcon status={item.status} /></Table.Td>
            </Table.Tr>
        })
    }, [flags.isFetching, page])

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
        {messages}
        <ChartView />
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
                            queryClient.refetchQueries({ queryKey:["flags"] })
                            notifications.show({
                                title: "Fresh data arrived 🌱",
                                message: "Flag data has been refreshed!",
                                color: "green",
                                autoClose: 3000
                            })
                        }}
                        loading={flags.isLoading}
                    >
                        Refresh
                    </Button>
                </Box>
                <Box hiddenFrom="md" style={{flexBasis: "100%", height:20}} />
                
                <Box style={{flex:1, flexGrow:1}} visibleFrom="md"/>
                
                <Box className="center-flex-col">
                    <Space visibleFrom="md" h="lg" />
                    <DonutChart
                        data={[
                            { value: flagsStats.data?.globals.flags.ok??0, color: 'lime', name: "Accepted" },
                            { value: flagsStats.data?.globals.flags.timeout??0, color: 'yellow', name: "Expired" },
                            { value: flagsStats.data?.globals.flags.invalid??0, color: 'red', name: "Rejected"},
                            { value: flagsStats.data?.globals.flags.wait??0, color: 'indigo', name: "Queued"},
                        ]}
                        startAngle={0}
                        endAngle={180}
                        paddingAngle={1}
                        size={160}
                        thickness={35}
                        withTooltip
                        tooltipDataSource="all"
                        mx="auto"
                        withLabelsLine
                        withLabels
                        style={{ marginBottom: -75 }}
                        chartLabel={`${totFlags} Flags`}
                    />
                </Box>
            </Box>
            {flags.isLoading?<Loader />:null}
            <Space h="md" />
            <Table style={{zIndex:1}}>
                <Table.Thead>
                    <Table.Tr>
                        <Table.Th style={thStyle}>ID</Table.Th>
                        <Table.Th style={thStyle}>Flag</Table.Th>
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
            {flags.isLoading?<Loader />:null}
            {totalPages==0?"No flags found!":null}
            <Space h="xl" />
            <Pagination total={totalPages} color="red" radius="md" value={page} onChange={setPage} />
        </Box>
        <ManualSubmissionModal opened={manualSubmissionModal} close={() => setManualSubmissionModal(false)} />
        <Space h="xl" /><Space h="xl" />
    </Box>
}