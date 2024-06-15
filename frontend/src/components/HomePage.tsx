import { flagsQuery, flagsStatsQuery, useExtendedExploitSolver, useTeamSolver } from "@/utils/queries";
import { useSettingsStore } from "@/utils/stores";
import { Box, Button, Loader, Pagination, Space, Table } from "@mantine/core";
import { useMemo, useState } from "react";
import { DonutChart } from '@mantine/charts';
import { FaKeyboard } from "react-icons/fa";
import { TbReload } from "react-icons/tb";
import { useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";
import { StatusIcon } from "./StatusIcon";

export const HomePage = () => {

    const [page, setPage] = useState<number>(1)
    const [bulkPageSize, tablePageSize] = useSettingsStore((state) => [state.pageSizeRequest, state.tablePageSize])
    const pagesForBulk = (bulkPageSize/tablePageSize)
    const bulkedPage = Math.ceil(page/pagesForBulk)
    const queryClient = useQueryClient()
    const getTeamName = useTeamSolver()
    const getExploitDetails = useExtendedExploitSolver()

    const flagsStats = flagsStatsQuery()
    const flags = flagsQuery(bulkedPage)
    const totFlags = (flagsStats.data?.invalid_flags??0) + (flagsStats.data?.ok_flags??0) + (flagsStats.data?.timeout_flags??0) + (flagsStats.data?.wait_flags??0)
    const totalPages = Math.ceil(totFlags/tablePageSize)


    const tableData = useMemo(() => {
        const offsetArray = ((page-1)%pagesForBulk)*tablePageSize
        return (flags.data?.items??[]).slice(offsetArray,offsetArray+tablePageSize).map((item) => {
            return <Table.Tr key={item.id}>
                <Table.Td>{item.id}</Table.Td>
                <Table.Td>{item.flag}</Table.Td>
                <Table.Td>{getExploitDetails(item.attack.exploit)}</Table.Td>
                <Table.Td>{getTeamName(item.attack.target)}</Table.Td>
                <Table.Td>{(item.attack.start_time && item.attack.end_time)?
                    (new Date(item.attack.end_time).getTime()-new Date(item.attack.start_time).getTime()).toFixed(2):
                    "Attack Info"}</Table.Td> {/* Execution Time include attack info (on click) (with a modal) */}
                <Table.Td>{item.status_text??"-"}</Table.Td> {/* item.submit_attempts + item.last_submission_at -> Status include number of tries if != 1 and last submission if failed */}
                <Table.Td><StatusIcon status={item.status} /></Table.Td>
            </Table.Tr>
        })
    }, [flags.isFetching, page])

    return <Box style={{
        width: "100%",
    }}>
        <h1>HomePage</h1>
        [Here will be places some graphs]<br />
        [This page has to be finished]<br />
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
                        onClick={() => {
                            notifications.show({
                                title: "Implement me please :(",
                                message: "This feature is not implemented yet!",
                                color: "red",
                                autoClose: 5000
                            })
                        }}
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
                            { value: flagsStats.data?.ok_flags??0, color: 'lime', name: "Accepted" },
                            { value: flagsStats.data?.timeout_flags??0, color: 'yellow', name: "Expired" },
                            { value: flagsStats.data?.invalid_flags??0, color: 'red', name: "Rejected"},
                            { value: flagsStats.data?.wait_flags ??0, color: 'indigo', name: "Queued"},
                        ]}
                        startAngle={0}
                        endAngle={180}
                        size={160}
                        paddingAngle={2}
                        thickness={30}
                        withTooltip
                        tooltipDataSource="all"
                        mx="auto"
                        withLabelsLine
                        withLabels
                        style={{ marginBottom: -85}}
                        chartLabel={`Flags: ${totFlags}`}
                    />
                </Box>
            </Box>
            {flags.isLoading?<Loader />:null}
            <Space h="md" />
            <Table style={{zIndex: 1}}>
                <Table.Thead>
                    <Table.Tr>
                        <Table.Th>ID</Table.Th>
                        <Table.Th>Flag</Table.Th>
                        <Table.Th>Service</Table.Th>
                        <Table.Th>Team</Table.Th>
                        <Table.Th>Execution Time</Table.Th>
                        <Table.Th>Response</Table.Th>
                        <Table.Th className="center-flex">Status</Table.Th>
                    </Table.Tr>
                </Table.Thead>
                <Table.Tbody>{tableData}</Table.Tbody>
            </Table>
            <Space h="md" />
            {flags.isLoading?<Loader />:null}
            {totalPages==0?"No flags found!":null}
            <Pagination total={totalPages} color="red" radius="md" value={page} onChange={setPage} />
        </Box>
        <Space h="xl" />
    </Box>
}