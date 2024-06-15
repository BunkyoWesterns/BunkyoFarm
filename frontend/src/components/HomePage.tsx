import { flagsQuery, flagsStatsQuery } from "@/utils/queries";
import { useSettingsStore } from "@/utils/stores";
import { Box, Button, Loader, Pagination, Space, Table, TableData } from "@mantine/core";
import { useEffect, useState } from "react";
import { DonutChart } from '@mantine/charts';
import { useImmer } from "use-immer";
import { FaKeyboard } from "react-icons/fa";
import { TbReload } from "react-icons/tb";
import { useQueryClient } from "@tanstack/react-query";
import { notifications } from "@mantine/notifications";

export const HomePage = () => {

    const [page, setPage] = useState<number>(1)
    const [bulkPageSize, tablePageSize] = useSettingsStore((state) => [state.pageSizeRequest, state.tablePageSize])
    const pagesForBulk = (bulkPageSize/tablePageSize)
    const bulkedPage = Math.ceil(page/pagesForBulk)
    const queryClient = useQueryClient()

    const flagsStats = flagsStatsQuery()
    const flags = flagsQuery(bulkedPage)

    const [tableData, updateTableData] = useImmer<TableData>({ head: [
        "Id", "Flag", "Service", "Team" ,"Execution Time", "Status Text", "Status"
    ]})
    const totFlags = (flagsStats.data?.invalid_flags??0) + (flagsStats.data?.ok_flags??0) + (flagsStats.data?.timeout_flags??0) + (flagsStats.data?.wait_flags??0)
    const totalPages = Math.ceil(totFlags/tablePageSize)

    useEffect(() => {
        //Need to call other api to collect data about exploits and targets
        updateTableData((draft) => {
            const offsetArray = ((page-1)%pagesForBulk)*tablePageSize
            draft.body = (flags.data?.items??[]).slice(offsetArray,offsetArray+tablePageSize).map((item) => {
                return [
                    item.id,
                    item.flag,
                    item.attack.exploit??"Unknown", //Service include exploit name and detail (on click)
                    item.attack.target??"Unknown", //Team include target name and detail (on click)
                    (item.attack.start_time && item.attack.end_time)?
                    (new Date(item.attack.end_time).getTime()-new Date(item.attack.start_time).getTime()).toFixed(2):
                    "Attack Info", //Execution Time include attack info (on click) (with a modal)
                    item.status_text??"",
                    item.status //item.submit_attempts + item.last_submission_at -> Status include number of tries if != 1 and last submission if failed
                ]
            })
        })
    }, [flags.isFetched, page])

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
                        style={{ marginBottom: -85 }}
                        chartLabel={`Flags: ${totFlags}`}
                    />
                </Box>
            </Box>
            {flags.isLoading?<Loader />:null}
            <Space h="md" />
            <Table data={tableData} />
            <Space h="md" />
            {flags.isLoading?<Loader />:null}
            {totalPages==0?"No flags found!":null}
            <Pagination total={totalPages} color="red" radius="md" value={page} onChange={setPage} />
        </Box>
        <Space h="xl" />
    </Box>
}