import { flagsQuery, flagsStatsQuery } from "@/utils/queries";
import { Box, Loader, Space, Table, TableData } from "@mantine/core";
import { useEffect, useState } from "react";
import { useImmer } from "use-immer";


export const HomePage = () => {

    const [page, setPage] = useState<number>(1)
    const [pageSize, setPageSize] = useState<number>(500)
    const flags = flagsQuery(page, pageSize)
    const flagsStats = flagsStatsQuery()
    const [tableData, updateTableData] = useImmer<TableData>({ head: [
        "Id", "Flag", "Service", "Team" ,"Execution Time", "Status Text", "Status"
    ]})

    useEffect(() => {
        //Need to call other api to collect data about exploits and targets
        console.log("UPDATING")
        updateTableData((draft) => {
            draft.body = [["a", "b", "c", "d", "e", "f", "g"]]
            draft.body = (flags.data?.items??[]).map((item) => {
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
    }, [flags.isFetched])

    return <Box style={{
        width: "100%",
    }}>
        <h1>HomePage</h1>
        [Here will be places some graphs]<br />
        [This page has to be finished]<br />
        Flags Submitted: {flagsStats.data?.ok_flags}<br />
        Flags Rejected: {flagsStats.data?.invalid_flags}<br />
        Flags Timeout: {flagsStats.data?.timeout_flags}<br />
        Flags Pending: {flagsStats.data?.wait_flags}<br />
        <Space h="md" />
        <Box className="center-flex-col">
            {flags.isLoading?<Loader />:null}
            <Table data={tableData} />
            Page: {page} <button onClick={() => setPage(page-1)}>-</button> <button onClick={() => setPage(page+1)}>+</button><br />
            PageSize: {pageSize} <button onClick={() => setPageSize(pageSize-100)}>-</button> <button onClick={() => setPageSize(pageSize+100)}>+</button>
        </Box>
        
    </Box>
}